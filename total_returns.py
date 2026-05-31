# pip install pandas numpy sqlalchemy "psycopg[binary]"

import os
import math
from bisect import bisect_left

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text


HISTORY_TABLE = "moex_daily_history"
DIVIDENDS_TABLE = "moex_dividends"
COUPONS_TABLE = "moex_coupons"
RESULT_TABLE = "moex_total_return_daily"

T1_START_DATE = pd.Timestamp("2023-07-31").date()

# Эти board-ы соответствуют тому, для чего выше собирались купоны.
BOND_BOARDS = {"TQCB", "TQOB", "TQOD", "TQOY", "TQRD"}


def settlement_days_for_share(secid, boardid, trade_date):
    """
    Для дивидендов нужно понять, когда наступает первый день торгов без дивиденда.

    Упрощенно:
    - до 31.07.2023 обычные акции были T+2;
    - с 31.07.2023 обычные акции стали T+1;
    - иностранные акции с суффиксом -RM оставляем T+2.
    """
    if str(secid).endswith("-RM"):
        return 2

    if trade_date >= T1_START_DATE:
        return 1

    return 2


def settlement_days_for_bond(secid, boardid, trade_date):
    """
    Для облигаций:
    - TQCB, TQOB, TQRD считаем T+1;
    - TQOD, TQOY до 31.07.2023 были T+2, потом T+1.
    """
    if trade_date >= T1_START_DATE:
        return 1

    if boardid in {"TQOD", "TQOY"}:
        return 2

    return 1


def shift_trading_days(trading_dates, date_value, n):
    """
    Сдвиг на n торговых дней вперед по фактическому календарю торгов бумаги.
    """
    i = bisect_left(trading_dates, date_value)

    if i >= len(trading_dates):
        return None

    # Если дата есть в календаре, стартуем с нее.
    # Если даты нет, bisect_left уже поставит нас на ближайшую следующую торговую дату.
    if trading_dates[i] != date_value:
        start_i = i
    else:
        start_i = i

    target_i = start_i + n

    if target_i >= len(trading_dates):
        return None

    return trading_dates[target_i]


def first_trading_date_on_or_after(trading_dates, date_value):
    i = bisect_left(trading_dates, date_value)

    if i >= len(trading_dates):
        return None

    return trading_dates[i]


def record_date_to_ex_date(trading_dates, record_date, settlement_days_func):
    """
    record_date -> ex-date.

    Логика:
    1. Ищем последний день, когда можно купить бумагу так, чтобы settlement
       успел пройти не позже record_date.
    2. Следующий торговый день после него — первый день без права на cashflow.

    Это работает и для T+1, и для T+2, и для случаев, когда record_date попадает на выходной.
    """
    if pd.isna(record_date):
        return None

    record_date = pd.Timestamp(record_date).date()

    last_cum_date = None

    for trade_date in trading_dates:
        days = settlement_days_func(trade_date)
        settlement_date = shift_trading_days(trading_dates, trade_date, days)

        if settlement_date is not None and settlement_date <= record_date:
            last_cum_date = trade_date

    if last_cum_date is None:
        return None

    i = bisect_left(trading_dates, last_cum_date)

    if i + 1 >= len(trading_dates):
        return None

    return trading_dates[i + 1]


def recreate_result_table(engine):
    with engine.begin() as conn:
        conn.execute(text(f"""
            DROP TABLE IF EXISTS {RESULT_TABLE};

            CREATE TABLE {RESULT_TABLE} (
                id bigserial PRIMARY KEY,

                secid text NOT NULL,
                boardid text NOT NULL,
                market text NOT NULL,
                tradedate date NOT NULL,

                legalcloseprice numeric,
                accint numeric,
                facevalue numeric,

                base_price numeric,
                cashflow numeric,

                gross_return numeric,
                log_return numeric,

                total_return_index numeric,
                adjusted_close numeric,

                price_type text,

                loaded_at timestamptz DEFAULT now()
            );

            CREATE UNIQUE INDEX ux_{RESULT_TABLE}_key
            ON {RESULT_TABLE} (secid, boardid, tradedate);

            CREATE INDEX idx_{RESULT_TABLE}_secid
            ON {RESULT_TABLE} (secid);

            CREATE INDEX idx_{RESULT_TABLE}_boardid
            ON {RESULT_TABLE} (boardid);

            CREATE INDEX idx_{RESULT_TABLE}_tradedate
            ON {RESULT_TABLE} (tradedate);
        """))


def load_data(engine):
    history = pd.read_sql(text(f"""
        SELECT
            secid,
            boardid,
            market,
            tradedate::date AS tradedate,
            legalcloseprice::numeric AS legalcloseprice,

            NULLIF(raw->>'TRADINGSESSION', '') AS trading_session,

            COALESCE(
                NULLIF(raw->>'ACCINT', '')::numeric,
                NULLIF(raw->>'ACCRUEDINT', '')::numeric
            ) AS accint,

            COALESCE(
                NULLIF(raw->>'FACEVALUE', '')::numeric,
                NULLIF(raw->>'FACEVALUEONSETTLEDATE', '')::numeric,
                NULLIF(raw->>'INITIALFACEVALUE', '')::numeric
            ) AS facevalue

        FROM {HISTORY_TABLE}
        WHERE secid IS NOT NULL
          AND boardid IS NOT NULL
          AND tradedate IS NOT NULL
          AND legalcloseprice IS NOT NULL
          AND legalcloseprice > 0
          AND (
                market = 'shares'
                OR market = 'bonds'
                OR boardid IN ('TQCB', 'TQOB', 'TQOD', 'TQOY', 'TQRD')
          )
    """), engine)

    dividends = pd.read_sql(text(f"""
        SELECT
            secid,
            boardid,
            registryclosedate::date AS record_date,
            value::numeric AS value,
            currencyid
        FROM {DIVIDENDS_TABLE}
        WHERE secid IS NOT NULL
          AND boardid IS NOT NULL
          AND registryclosedate IS NOT NULL
          AND value IS NOT NULL
          AND value > 0
    """), engine)

    coupons = pd.read_sql(text(f"""
        SELECT
            secid,
            boardid,
            coupondate::date AS coupon_date,
            recorddate::date AS record_date,

            COALESCE(
                value::numeric,
                value_rub::numeric
            ) AS value
        FROM {COUPONS_TABLE}
        WHERE secid IS NOT NULL
          AND boardid IS NOT NULL
          AND coupondate IS NOT NULL
          AND COALESCE(value, value_rub) IS NOT NULL
          AND COALESCE(value, value_rub) > 0
    """), engine)

    for df in [history, dividends, coupons]:
        for col in df.columns:
            if col.endswith("date") or col in {"tradedate", "record_date", "coupon_date"}:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    history["legalcloseprice"] = pd.to_numeric(history["legalcloseprice"], errors="coerce")
    history["accint"] = pd.to_numeric(history["accint"], errors="coerce")
    history["facevalue"] = pd.to_numeric(history["facevalue"], errors="coerce")

    dividends["value"] = pd.to_numeric(dividends["value"], errors="coerce")
    coupons["value"] = pd.to_numeric(coupons["value"], errors="coerce")

    return history, dividends, coupons


def clean_history(history, dividends, coupons):
    """
    Оставляем только акции и облигации, для которых мы действительно собирали
    соответствующие cashflow-таблицы.

    Акции берем только по boardid, которые присутствуют в moex_dividends.
    Облигации берем только по boardid, которые присутствуют в moex_coupons.
    """
    dividend_boards = set(dividends["boardid"].dropna().unique())
    coupon_boards = set(coupons["boardid"].dropna().unique())

    history = history[
        (
            (history["market"] == "shares")
            & history["boardid"].isin(dividend_boards)
        )
        |
        (
            (
                (history["market"] == "bonds")
                | history["boardid"].isin(BOND_BOARDS)
            )
            & history["boardid"].isin(coupon_boards)
        )
    ].copy()

    # Если у одной бумаги за один день несколько строк, предпочитаем TRADINGSESSION=3.
    history["session_rank"] = np.where(history["trading_session"] == "3", 1, 0)

    history = (
        history
        .sort_values(["secid", "boardid", "tradedate", "session_rank"])
        .drop_duplicates(["secid", "boardid", "tradedate"], keep="last")
        .drop(columns=["session_rank"])
    )

    return history


def build_cashflows_for_group(group, dividends, coupons):
    secid = group["secid"].iloc[0]
    boardid = group["boardid"].iloc[0]
    market = group["market"].iloc[0]

    trading_dates = list(group["tradedate"])
    cashflows = {d: 0.0 for d in trading_dates}

    if market == "shares":
        divs = dividends[
            (dividends["secid"] == secid)
            & (dividends["boardid"] == boardid)
        ]

        for _, div in divs.iterrows():
            ex_date = record_date_to_ex_date(
                trading_dates=trading_dates,
                record_date=div["record_date"],
                settlement_days_func=lambda trade_date: settlement_days_for_share(
                    secid=secid,
                    boardid=boardid,
                    trade_date=trade_date,
                ),
            )

            if ex_date in cashflows:
                cashflows[ex_date] += float(div["value"])
    else:
        cps = coupons[
            (coupons["secid"] == secid)
            & (coupons["boardid"] == boardid)
        ]

        for _, coupon in cps.iterrows():
            cashflow_date = first_trading_date_on_or_after(
                trading_dates=trading_dates,
                date_value=coupon["coupon_date"],
            )

            if cashflow_date in cashflows:
                cashflows[cashflow_date] += float(coupon["value"])
    return pd.Series(cashflows)


def calculate_group_returns(group, dividends, coupons):
    group = group.sort_values("tradedate").copy()

    secid = group["secid"].iloc[0]
    boardid = group["boardid"].iloc[0]
    market = group["market"].iloc[0]

    if market == "shares":
        group["base_price"] = group["legalcloseprice"]
        group["price_type"] = "legalcloseprice"
    else:
        group = group[
            group["facevalue"].notna()
            & group["accint"].notna()
            & (group["facevalue"] > 0)
        ].copy()

        if len(group) < 2:
            return pd.DataFrame()

        group["base_price"] = (
            group["legalcloseprice"] / 100.0 * group["facevalue"]
            + group["accint"]
        )
        group["price_type"] = "dirty_price_from_legalcloseprice_plus_accint"

    group = group[group["base_price"].notna() & (group["base_price"] > 0)].copy()

    if len(group) < 2:
        return pd.DataFrame()

    cashflows = build_cashflows_for_group(group, dividends, coupons)

    group["cashflow"] = group["tradedate"].map(cashflows).fillna(0.0)

    group["prev_base_price"] = group["base_price"].shift(1)

    group["gross_return"] = (
        (group["base_price"] + group["cashflow"])
        / group["prev_base_price"]
    )

    group.loc[group["prev_base_price"].isna(), "gross_return"] = np.nan
    group.loc[group["gross_return"] <= 0, "gross_return"] = np.nan

    group["log_return"] = np.log(group["gross_return"])

    # Total return index: первая дата = 100.
    group["total_return_index"] = (
        group["gross_return"]
        .fillna(1.0)
        .cumprod()
        * 100.0
    )

    # Back-adjusted price:
    # последняя adjusted_close равна последней base_price,
    # а прошлое пересчитано назад через total return.
    last_index = group["total_return_index"].iloc[-1]
    last_base_price = group["base_price"].iloc[-1]

    group["adjusted_close"] = (
        group["total_return_index"]
        / last_index
        * last_base_price
    )

    return group[[
        "secid",
        "boardid",
        "market",
        "tradedate",
        "legalcloseprice",
        "accint",
        "facevalue",
        "base_price",
        "cashflow",
        "gross_return",
        "log_return",
        "total_return_index",
        "adjusted_close",
        "price_type",
    ]]


def insert_result(engine, result):
    if result.empty:
        print("No rows to insert")
        return

    result = result.copy()

    result = result.replace([np.inf, -np.inf], np.nan)
    result = result.astype(object).where(pd.notnull(result), None)

    records = result.to_dict("records")

    query = text(f"""
        INSERT INTO {RESULT_TABLE} (
            secid,
            boardid,
            market,
            tradedate,
            legalcloseprice,
            accint,
            facevalue,
            base_price,
            cashflow,
            gross_return,
            log_return,
            total_return_index,
            adjusted_close,
            price_type
        )
        VALUES (
            :secid,
            :boardid,
            :market,
            :tradedate,
            :legalcloseprice,
            :accint,
            :facevalue,
            :base_price,
            :cashflow,
            :gross_return,
            :log_return,
            :total_return_index,
            :adjusted_close,
            :price_type
        )
        ON CONFLICT (secid, boardid, tradedate) DO NOTHING
    """)

    chunk_size = 5000

    with engine.begin() as conn:
        for start in range(0, len(records), chunk_size):
            conn.execute(query, records[start:start + chunk_size])


def main():
    PG_DSN="postgresql+psycopg://postgres:password2544@localhost:5432/heavy_tails_data"
    engine = create_engine(PG_DSN)


    recreate_result_table(engine)

    history, dividends, coupons = load_data(engine)
    history = clean_history(history, dividends, coupons)

    print(f"history rows after filter: {len(history)}")
    print(f"dividend rows: {len(dividends)}")
    print(f"coupon rows: {len(coupons)}")

    all_results = []

    groups = history.groupby(["secid", "boardid"], sort=True)
    total_groups = len(groups)

    for i, ((secid, boardid), group) in enumerate(groups, start=1):
        try:
            result = calculate_group_returns(
                group=group,
                dividends=dividends,
                coupons=coupons,
            )

            if not result.empty:
                all_results.append(result)

            print(
                f"[{i}/{total_groups}] "
                f"{secid} {boardid}: input={len(group)}, output={len(result)}"
            )

        except Exception as e:
            print(f"[{i}/{total_groups}] ERROR {secid} {boardid}: {e}")

    if all_results:
        final = pd.concat(all_results, ignore_index=True)
    else:
        final = pd.DataFrame()

    insert_result(engine, final)

    print(f"Done. Inserted rows: {len(final)}")


if __name__ == "__main__":
    main()