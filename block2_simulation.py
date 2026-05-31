# Блок 2. Генерация и предварительная обработка данных
# Тема: влияние выбора системы налогообложения на чистую прибыль на одного сотрудника
# Язык: Python 3

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.model_selection import train_test_split

SEED = 20260609
N = 3000


def simulate_data(n=N, seed=SEED):
    rng = np.random.default_rng(seed)

    # Ненаблюдаемая организационно-экономическая сложность / качество управления.
    # Используется только при генерации данных и не включается как признак в ML-модели.
    U = rng.normal(0, 1, n)

    # Контроль 1: логарифм годовой выручки, ln(руб.)
    eps_rev = rng.normal(0, 0.55, n)
    ln_revenue = 18.15 + 0.48 * U + eps_rev

    # Контроль 2: капиталоемкость, млн руб. основных средств на сотрудника
    cap_latent = 0.05 + 0.38 * U + 0.28 * (ln_revenue - 18.15) + rng.normal(0, 0.55, n)
    capital_intensity = np.exp(cap_latent)

    # Контроль 3: статус экспортера
    p_exporter = expit(-1.45 + 0.55 * (ln_revenue - 18.15) + 0.48 * U + 0.18 * np.log1p(capital_intensity))
    exporter = rng.binomial(1, p_exporter)

    # Инструмент: 1, если в регионе действует льготная ставка УСН
    Z_USN_preferential = rng.binomial(1, 0.46, n)

    # Потенциальные значения воздействия: D(0), D(1)
    eps_D = rng.logistic(0, 1, n)
    treatment_index_without_instrument = (
        -0.40
        + 0.58 * (ln_revenue - 18.15)
        + 0.32 * np.log1p(capital_intensity)
        + 0.85 * exporter
        + 0.95 * U
        + 0.18 * (ln_revenue - 18.15) ** 2
        + 0.22 * exporter * (ln_revenue - 18.15)
        + eps_D
    )
    D0_if_Z0 = (treatment_index_without_instrument > 0).astype(int)
    D1_if_Z1 = (treatment_index_without_instrument - 0.90 > 0).astype(int)
    D_OSNO = np.where(Z_USN_preferential == 1, D1_if_Z1, D0_if_Z0)

    # Потенциальные исходы зависимой переменной, млн руб. чистой прибыли на сотрудника
    eps_y = rng.normal(0, 0.38, n)
    Y0_USN = (
        1.05
        + 0.34 * (ln_revenue - 18.15)
        + 0.12 * (ln_revenue - 18.15) ** 2
        + 0.22 * np.log1p(capital_intensity)
        + 0.33 * exporter
        + 0.62 * U
        + 0.08 * exporter * (ln_revenue - 18.15)
        + eps_y
    )
    tau = -0.32 - 0.07 * (ln_revenue - 18.15) - 0.10 * exporter - 0.04 * np.log1p(capital_intensity) + 0.05 * U
    Y1_OSNO = Y0_USN + tau
    y_profit_per_employee = np.where(D_OSNO == 1, Y1_OSNO, Y0_USN)

    data = pd.DataFrame(
        {
            "y_profit_per_employee": y_profit_per_employee,
            "D_OSNO": D_OSNO,
            "Z_USN_preferential": Z_USN_preferential,
            "ln_revenue": ln_revenue,
            "capital_intensity": capital_intensity,
            "exporter": exporter,
            "U_complexity": U,
            "D0_if_Z0": D0_if_Z0,
            "D1_if_Z1": D1_if_Z1,
            "Y0_USN": Y0_USN,
            "Y1_OSNO": Y1_OSNO,
            "tau": tau,
        }
    )
    return data


if __name__ == "__main__":
    df = simulate_data()

    continuous = [
        "y_profit_per_employee",
        "ln_revenue",
        "capital_intensity",
        "U_complexity",
        "Y0_USN",
        "Y1_OSNO",
        "tau",
    ]
    binary = ["D_OSNO", "Z_USN_preferential", "exporter", "D0_if_Z0", "D1_if_Z1"]
    corr_vars = [
        "y_profit_per_employee",
        "D_OSNO",
        "Z_USN_preferential",
        "ln_revenue",
        "capital_intensity",
        "exporter",
        "U_complexity",
    ]

    desc_cont = df[continuous].agg(["mean", "std", "median", "min", "max"]).T
    desc_bin = pd.DataFrame({"share_ones": df[binary].mean(), "count_ones": df[binary].sum().astype(int)})
    corr = df[corr_vars].corr()

    train_idx, test_idx = train_test_split(df.index, test_size=0.25, random_state=42, stratify=df["D_OSNO"])
    df["sample"] = "train"
    df.loc[test_idx, "sample"] = "test"

    split_stats = df.groupby("sample").agg(
        n=("D_OSNO", "size"),
        share_D=("D_OSNO", "mean"),
        share_Z=("Z_USN_preferential", "mean"),
        share_exporter=("exporter", "mean"),
        mean_y=("y_profit_per_employee", "mean"),
    )

    from pathlib import Path
    out_dir = Path(__file__).resolve().parent
    df.to_csv(out_dir / "block2_simulated_data.csv", index=False)
    desc_cont.to_csv(out_dir / "block2_desc_continuous.csv")
    desc_bin.to_csv(out_dir / "block2_desc_binary.csv")
    corr.to_csv(out_dir / "block2_correlation_matrix.csv")
    split_stats.to_csv(out_dir / "block2_train_test_split_stats.csv")

    print("Continuous descriptive statistics:")
    print(desc_cont.round(3))
    print("\nBinary descriptive statistics:")
    print(desc_bin.round(3))
    print("\nCorrelation matrix:")
    print(corr.round(3))
    print("\nTrain/test split:")
    print(split_stats.round(3))
