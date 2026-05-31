# pip install requests sqlalchemy "psycopg[binary]"

import os
import json
from decimal import Decimal

import requests
from sqlalchemy import create_engine, text


BASE_URL = "https://iss.moex.com/iss/apps/infogrid/stock/rates.json"
TABLE_NAME = "moex_stocks"


def create_table_if_not_exists(engine, columns):
    cols_sql = ",\n".join(
        f'"{col.lower()}" text'
        for col in columns
    )

    query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id bigserial PRIMARY KEY,
        {cols_sql},
        loaded_at timestamptz DEFAULT now()
    );
    """

    with engine.begin() as conn:
        conn.execute(text(query))


def fetch_page(start, limit=100):
    params = {
        "_": "1778783423465",
        "lang": "ru",
        "iss.meta": "off",
        "sort_order": "asc",
        "sort_column": "SECID",
        "start": start,
        "limit": limit,
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    return json.loads(response.text, parse_float=Decimal)


def insert_rows(engine, columns, rows):
    if not rows:
        return 0

    db_columns = [col.lower() for col in columns]

    records = []
    for row in rows:
        record = {
            col.lower(): None if value is None else str(value)
            for col, value in zip(columns, row)
        }
        records.append(record)

    columns_sql = ", ".join(f'"{col}"' for col in db_columns)
    values_sql = ", ".join(f":{col}" for col in db_columns)

    query = text(f"""
        INSERT INTO {TABLE_NAME} ({columns_sql})
        VALUES ({values_sql})
    """)

    with engine.begin() as conn:
        conn.execute(query, records)

    return len(records)


def main():
    # Пример:
    PG_DSN="postgresql+psycopg://postgres:password2544@localhost:5432/heavy_tails_data"
    engine = create_engine(PG_DSN)

    table_created = False
    total_inserted = 0

    for start in range(0, 5601, 100):
        payload = fetch_page(start)

        columns = payload["rates"]["columns"]
        rows = payload["rates"]["data"]

        if not table_created:
            create_table_if_not_exists(engine, columns)
            table_created = True

        inserted = insert_rows(engine, columns, rows)
        total_inserted += inserted

        print(f"start={start}: inserted={inserted}")

    print(f"Done. Total inserted: {total_inserted}")


if __name__ == "__main__":
    main()