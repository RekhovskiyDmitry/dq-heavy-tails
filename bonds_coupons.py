# pip install requests sqlalchemy "psycopg[binary]"

import os
import json
import time

import requests
from sqlalchemy import create_engine, text


HISTORY_TABLE = "moex_daily_history"
COUPONS_TABLE = "moex_coupons"

BASE_URL = "https://iss.moex.com/iss/securities"


def main():
    PG_DSN="postgresql+psycopg://postgres:password2544@localhost:5432/heavy_tails_data"
    engine = create_engine(PG_DSN)

    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {COUPONS_TABLE} (
                id bigserial PRIMARY KEY,

                secid text NOT NULL,
                boardid text NOT NULL,

                isin text,
                name text,
                issuevalue numeric,

                coupondate date,
                recorddate date,
                startdate date,

                initialfacevalue numeric,
                facevalue numeric,
                faceunit text,

                value numeric,
                valueprc numeric,
                value_rub numeric,

                raw jsonb NOT NULL,

                loaded_at timestamptz DEFAULT now()
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_{COUPONS_TABLE}_key
            ON {COUPONS_TABLE} (
                secid,
                boardid,
                coupondate,
                value,
                facevalue
            );

            CREATE INDEX IF NOT EXISTS idx_{COUPONS_TABLE}_secid
            ON {COUPONS_TABLE} (secid);

            CREATE INDEX IF NOT EXISTS idx_{COUPONS_TABLE}_boardid
            ON {COUPONS_TABLE} (boardid);

            CREATE INDEX IF NOT EXISTS idx_{COUPONS_TABLE}_coupondate
            ON {COUPONS_TABLE} (coupondate);
        """))

    with engine.begin() as conn:
        tickers = conn.execute(text(f"""
            SELECT DISTINCT
                secid,
                boardid
            FROM {HISTORY_TABLE}
            WHERE secid IS NOT NULL
              AND boardid IS NOT NULL
              AND (
                    market = 'bonds'
                    OR boardid IN ('TQCB', 'TQOB', 'TQOD', 'TQOY', 'TQRD')
              )
            ORDER BY secid, boardid
        """)).mappings().all()

    print(f"bond tickers from {HISTORY_TABLE}: {len(tickers)}")

    total_inserted = 0

    for i, item in enumerate(tickers, start=1):
        secid = item["secid"]
        boardid = item["boardid"]

        url = f"{BASE_URL}/{secid}/bondization.json"

        try:
            response = requests.get(url, params={
                "iss.meta": "off",
                "iss.only": "coupons",
                "lang": "ru",
                "limit": "unlimited",
            }, timeout=30)

            response.raise_for_status()
            payload = response.json()

            block = payload.get("coupons")

            if not block:
                print(f"[{i}/{len(tickers)}] {secid} {boardid}: no coupons block")
                continue

            columns = block["columns"]
            rows = block["data"]

            if not rows:
                print(f"[{i}/{len(tickers)}] {secid} {boardid}: 0 coupons")
                continue

            records = []

            for row in rows:
                coupon = dict(zip(columns, row))

                records.append({
                    "secid": secid,
                    "boardid": boardid,

                    "isin": coupon.get("isin"),
                    "name": coupon.get("name"),
                    "issuevalue": coupon.get("issuevalue"),

                    "coupondate": coupon.get("coupondate"),
                    "recorddate": coupon.get("recorddate"),
                    "startdate": coupon.get("startdate"),

                    "initialfacevalue": coupon.get("initialfacevalue"),
                    "facevalue": coupon.get("facevalue"),
                    "faceunit": coupon.get("faceunit"),

                    "value": coupon.get("value"),
                    "valueprc": coupon.get("valueprc"),
                    "value_rub": coupon.get("value_rub"),

                    "raw": json.dumps(coupon, ensure_ascii=False),
                })

            with engine.begin() as conn:
                result = conn.execute(text(f"""
                    INSERT INTO {COUPONS_TABLE} (
                        secid,
                        boardid,
                        isin,
                        name,
                        issuevalue,
                        coupondate,
                        recorddate,
                        startdate,
                        initialfacevalue,
                        facevalue,
                        faceunit,
                        value,
                        valueprc,
                        value_rub,
                        raw
                    )
                    VALUES (
                        :secid,
                        :boardid,
                        :isin,
                        :name,
                        :issuevalue,
                        :coupondate,
                        :recorddate,
                        :startdate,
                        :initialfacevalue,
                        :facevalue,
                        :faceunit,
                        :value,
                        :valueprc,
                        :value_rub,
                        CAST(:raw AS jsonb)
                    )
                    ON CONFLICT (
                        secid,
                        boardid,
                        coupondate,
                        value,
                        facevalue
                    ) DO NOTHING
                """), records)

            inserted = result.rowcount or 0
            total_inserted += inserted

            print(
                f"[{i}/{len(tickers)}] "
                f"{secid} {boardid}: coupons={len(records)}, inserted={inserted}"
            )

        except Exception as e:
            print(f"[{i}/{len(tickers)}] ERROR {secid} {boardid}: {e}")

        time.sleep(0.05)

    print(f"Done. Total inserted: {total_inserted}")


if __name__ == "__main__":
    main()