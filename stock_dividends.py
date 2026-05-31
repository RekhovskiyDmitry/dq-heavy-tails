# pip install requests sqlalchemy "psycopg[binary]"

import os
import json
import time

import requests
from sqlalchemy import create_engine, text


HISTORY_TABLE = "moex_daily_history"
DIVIDENDS_TABLE = "moex_dividends"

BASE_URL = "https://iss.moex.com/iss/securities"


def main():
    PG_DSN="postgresql+psycopg://postgres:password2544@localhost:5432/heavy_tails_data"
    engine = create_engine(PG_DSN)

    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {DIVIDENDS_TABLE} (
                id bigserial PRIMARY KEY,

                secid text NOT NULL,
                boardid text NOT NULL,

                isin text,
                registryclosedate date,
                value numeric,
                currencyid text,

                raw jsonb NOT NULL,

                loaded_at timestamptz DEFAULT now()
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_{DIVIDENDS_TABLE}_key
            ON {DIVIDENDS_TABLE} (
                secid,
                boardid,
                registryclosedate,
                value,
                currencyid
            );

            CREATE INDEX IF NOT EXISTS idx_{DIVIDENDS_TABLE}_secid
            ON {DIVIDENDS_TABLE} (secid);

            CREATE INDEX IF NOT EXISTS idx_{DIVIDENDS_TABLE}_boardid
            ON {DIVIDENDS_TABLE} (boardid);

            CREATE INDEX IF NOT EXISTS idx_{DIVIDENDS_TABLE}_registryclosedate
            ON {DIVIDENDS_TABLE} (registryclosedate);
        """))

    with engine.begin() as conn:
        tickers = conn.execute(text(f"""
            SELECT DISTINCT
                secid,
                boardid
            FROM {HISTORY_TABLE}
            WHERE market = 'shares'
              AND secid IS NOT NULL
              AND boardid IS NOT NULL
            ORDER BY secid, boardid
        """)).mappings().all()

    print(f"shares tickers from {HISTORY_TABLE}: {len(tickers)}")

    total_inserted = 0

    for i, item in enumerate(tickers, start=1):
        secid = item["secid"]
        boardid = item["boardid"]

        url = f"{BASE_URL}/{secid}/dividends.json"

        try:
            response = requests.get(url, params={
                "iss.meta": "off",
                "lang": "ru",
            }, timeout=30)

            response.raise_for_status()
            payload = response.json()

            block = payload.get("dividends")

            if not block:
                print(f"[{i}/{len(tickers)}] {secid} {boardid}: no dividends block")
                continue

            columns = block["columns"]
            rows = block["data"]

            if not rows:
                print(f"[{i}/{len(tickers)}] {secid} {boardid}: 0 dividends")
                continue

            records = []

            for row in rows:
                dividend = dict(zip(columns, row))

                records.append({
                    "secid": dividend.get("secid") or secid,
                    "boardid": boardid,
                    "isin": dividend.get("isin"),
                    "registryclosedate": dividend.get("registryclosedate"),
                    "value": dividend.get("value"),
                    "currencyid": dividend.get("currencyid"),
                    "raw": json.dumps(dividend, ensure_ascii=False),
                })

            with engine.begin() as conn:
                result = conn.execute(text(f"""
                    INSERT INTO {DIVIDENDS_TABLE} (
                        secid,
                        boardid,
                        isin,
                        registryclosedate,
                        value,
                        currencyid,
                        raw
                    )
                    VALUES (
                        :secid,
                        :boardid,
                        :isin,
                        :registryclosedate,
                        :value,
                        :currencyid,
                        CAST(:raw AS jsonb)
                    )
                    ON CONFLICT (
                        secid,
                        boardid,
                        registryclosedate,
                        value,
                        currencyid
                    ) DO NOTHING
                """), records)

            inserted = result.rowcount or 0
            total_inserted += inserted

            print(
                f"[{i}/{len(tickers)}] "
                f"{secid} {boardid}: dividends={len(records)}, inserted={inserted}"
            )

        except Exception as e:
            print(f"[{i}/{len(tickers)}] ERROR {secid} {boardid}: {e}")

        time.sleep(0.05)

    print(f"Done. Total inserted: {total_inserted}")


if __name__ == "__main__":
    main()