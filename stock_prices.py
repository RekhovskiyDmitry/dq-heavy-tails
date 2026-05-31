# pip install requests sqlalchemy "psycopg[binary]"

import os
import json
import time
from decimal import Decimal
from tqdm import tqdm
import requests
from sqlalchemy import create_engine, text


ISS_BASE = "https://iss.moex.com/iss"

SOURCE_TABLE = "moex_stocks"
HISTORY_TABLE = "moex_daily_history"

REQUEST_SLEEP = 0.05


def fetch_json(url, params=None):
    params = params or {}
    params.setdefault("iss.meta", "off")
    params.setdefault("lang", "ru")

    r = requests.get(url, params=params, timeout=60)
    print(url)
    r.raise_for_status()
    return r.json()


def block_rows(payload, block_name):
    block = payload.get(block_name)
    if not block:
        return []

    columns = block["columns"]
    rows = block["data"]

    result = []
    for row in rows:
        result.append({
            columns[i].upper(): row[i]
            for i in range(len(columns))
        })

    return result


def cursor_total(payload, cursor_block_name):
    rows = block_rows(payload, cursor_block_name)
    if not rows:
        return None

    total = rows[0].get("TOTAL")
    return int(total) if total is not None else None


def recreate_history_table(engine):
    query = f"""
    CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
        id bigserial PRIMARY KEY,

        secid text NOT NULL,
        boardid text NOT NULL,
        engine text,
        market text,

        tradedate date,

        price numeric,
        open numeric,
        low numeric,
        high numeric,
        close numeric,
        legalcloseprice numeric,
        marketprice2 numeric,
        marketprice3 numeric,
        waprice numeric,

        volume numeric,
        value numeric,
        numtrades numeric,

        raw jsonb NOT NULL,

        loaded_at timestamptz DEFAULT now()
    );

    CREATE UNIQUE INDEX IF NOT EXISTS ux_{HISTORY_TABLE}_key
    ON {HISTORY_TABLE} (secid, boardid, tradedate);

    CREATE INDEX IF NOT EXISTS idx_{HISTORY_TABLE}_secid ON {HISTORY_TABLE} (secid);
    CREATE INDEX IF NOT EXISTS idx_{HISTORY_TABLE}_boardid ON {HISTORY_TABLE} (boardid);
    CREATE INDEX IF NOT EXISTS idx_{HISTORY_TABLE}_tradedate ON {HISTORY_TABLE} (tradedate);
    """

    with engine.begin() as conn:
        conn.execute(text(query))


def to_decimal(value):
    if value is None or value == "":
        return None
    return Decimal(str(value))


def first_not_none(row, keys):
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


def get_source_securities(engine):
    query = f"""
    SELECT DISTINCT
        secid,
        primary_boardid AS boardid
    FROM {SOURCE_TABLE}
    WHERE secid IS NOT NULL
      AND primary_boardid IS NOT NULL
      AND primary_boardid='TQBR'
    ORDER BY secid, primary_boardid
    """

    with engine.begin() as conn:
        rows = conn.execute(text(query)).mappings().all()

    return [
        {
            "secid": row["secid"],
            "boardid": row["boardid"],
        }
        for row in rows
    ]


def build_board_to_market_map():
    """
    Автоматически находит, к какому market относится каждый boardid внутри engine=stock.

    Пример:
    TQBR -> shares
    TQCB -> bonds
    INAV -> index / другой market, если MOEX так его отдает
    и т.д.
    """
    url = f"{ISS_BASE}/engines/stock/markets.json"
    payload = fetch_json(url)

    markets = []
    for row in block_rows(payload, "markets"):
        market_name = (
            row.get("MARKET_NAME")
            or row.get("NAME")
            or row.get("MARKET")
        )

        if market_name:
            markets.append(market_name)

    board_map = {}

    for market in markets:
        boards_url = f"{ISS_BASE}/engines/stock/markets/{market}/boards.json"

        try:
            boards_payload = fetch_json(boards_url)
        except Exception as e:
            print(f"skip market={market}: cannot load boards: {e}")
            continue

        for row in block_rows(boards_payload, "boards"):
            boardid = (
                row.get("BOARDID")
                or row.get("BOARD_ID")
                or row.get("ID")
            )

            if boardid:
                board_map[boardid] = {
                    "engine": "stock",
                    "market": market,
                }

    return board_map


def insert_history_rows(engine, secid, boardid, engine_name, market, history_rows):
    if not history_rows:
        return 0

    records = []

    for row in history_rows:
        price = first_not_none(row, [
            "CLOSE",
            "LEGALCLOSEPRICE",
            "MARKETPRICE3",
            "MARKETPRICE2",
            "WAPRICE",
        ])

        records.append({
            "secid": secid,
            "boardid": boardid,
            "engine": engine_name,
            "market": market,

            "tradedate": row.get("TRADEDATE"),

            "price": to_decimal(price),
            "open": to_decimal(row.get("OPEN")),
            "low": to_decimal(row.get("LOW")),
            "high": to_decimal(row.get("HIGH")),
            "close": to_decimal(row.get("CLOSE")),
            "legalcloseprice": to_decimal(row.get("LEGALCLOSEPRICE")),
            "marketprice2": to_decimal(row.get("MARKETPRICE2")),
            "marketprice3": to_decimal(row.get("MARKETPRICE3")),
            "waprice": to_decimal(row.get("WAPRICE")),

            "volume": to_decimal(row.get("VOLUME")),
            "value": to_decimal(row.get("VALUE")),
            "numtrades": to_decimal(row.get("NUMTRADES")),

            "raw": json.dumps(row, ensure_ascii=False),
        })

    query = text(f"""
        INSERT INTO {HISTORY_TABLE} (
            secid,
            boardid,
            engine,
            market,
            tradedate,
            price,
            open,
            low,
            high,
            close,
            legalcloseprice,
            marketprice2,
            marketprice3,
            waprice,
            volume,
            value,
            numtrades,
            raw
        )
        VALUES (
            :secid,
            :boardid,
            :engine,
            :market,
            :tradedate,
            :price,
            :open,
            :low,
            :high,
            :close,
            :legalcloseprice,
            :marketprice2,
            :marketprice3,
            :waprice,
            :volume,
            :value,
            :numtrades,
            CAST(:raw AS jsonb)
        )
        ON CONFLICT (secid, boardid, tradedate) DO NOTHING
    """)

    with engine.begin() as conn:
        conn.execute(query, records)

    return len(records)


def load_security_history(engine, secid, boardid, engine_name, market):
    start = 0
    total_inserted = 0

    while True:
        url = (
            f"{ISS_BASE}/history/engines/{engine_name}"
            f"/markets/{market}"
            f"/boards/{boardid}"
            f"/securities/{secid}.json"
        )

        payload = fetch_json(url, params={
            "start": start,
            "limit": 100,
        })

        rows = block_rows(payload, "history")

        if not rows:
            break

        inserted = insert_history_rows(
            engine=engine,
            secid=secid,
            boardid=boardid,
            engine_name=engine_name,
            market=market,
            history_rows=rows,
        )

        total_inserted += inserted

        total = cursor_total(payload, "history.cursor")

        start += len(rows)

        if total is not None and start >= total:
            break

        if len(rows) < 100:
            break

        time.sleep(REQUEST_SLEEP)

    return total_inserted

def history_exists_for_security(engine, secid, boardid):
    query = text(f"""
        SELECT 1
        FROM {HISTORY_TABLE}
        WHERE secid = :secid
          AND boardid = :boardid
        LIMIT 1
    """)

    with engine.begin() as conn:
        row = conn.execute(query, {
            "secid": secid,
            "boardid": boardid,
        }).first()

    return row is not None


def main():
    PG_DSN="postgresql+psycopg://postgres:password2544@localhost:5432/heavy_tails_data"
    engine = create_engine(PG_DSN)

    recreate_history_table(engine)

    securities = get_source_securities(engine)
    print(f"securities from {SOURCE_TABLE}: {len(securities)}")

    board_map = build_board_to_market_map()
    print(f"boards discovered from MOEX: {len(board_map)}")

    total_history_rows = 0
    skipped = 0

    for i, item in enumerate(tqdm(securities), start=1):
        secid = item["secid"]
        boardid = item["boardid"]

        board_info = board_map.get(boardid)

        if history_exists_for_security(engine, secid, boardid):
            continue

        if not board_info:
            print(f"[{i}/{len(securities)}] SKIP {secid} {boardid}: board not found in MOEX markets")
            skipped += 1
            continue

        engine_name = board_info["engine"]
        market = board_info["market"]

        try:
            inserted = load_security_history(
                engine=engine,
                secid=secid,
                boardid=boardid,
                engine_name=engine_name,
                market=market,
            )

            total_history_rows += inserted

        except Exception as e:
            print(
                f"[{i}/{len(securities)}] "
                f"ERROR {secid} {boardid}: {e}"
            )

        time.sleep(REQUEST_SLEEP)

    print("Done")
    print(f"history rows inserted: {total_history_rows}")
    print(f"skipped securities: {skipped}")


if __name__ == "__main__":
    main()