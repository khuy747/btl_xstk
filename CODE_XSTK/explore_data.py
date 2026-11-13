"""Create exploratory plots from the daily and hourly station CSV files."""

from pathlib import Path

import matplotlib

# Save charts without requiring a desktop GUI backend.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


CODE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CODE_DIR / "outputs" / "eda"
DAILY_FILE = CODE_DIR / "daily_7stations_1985_2025.csv"
HOURLY_FILE = CODE_DIR / "hourly_cleaned_wide.csv"

STUDY_START = "2000-01-01"
STUDY_END = "2020-12-31"
STATIONS = ["BenLuc", "BienHoa", "PhuAn", "VungTau", "ThuDau1", "NhaBe", "TanAn"]
STATION_NAMES = {
    "BenLuc": "Ben Luc",
    "BienHoa": "Bien Hoa",
    "PhuAn": "Phu An",
    "VungTau": "Vung Tau",
    "ThuDau1": "Thu Dau Mot",
    "NhaBe": "Nha Be",
    "TanAn": "Tan An",
}
Y_COLUMN = "BienHoa_mean"
X_COLUMN = "ThuDau1_mean"
VALUE_LABEL = "Giá trị trung bình ngày (đơn vị gốc, chưa xác nhận)"

sns.set_theme(style="whitegrid")


def load_daily_data():
    """Read daily means once and mask any station-day that is not complete."""
    columns = ["date"]
    for station in STATIONS:
        columns.extend([f"{station}_n_valid", f"{station}_mean"])

    daily = pd.read_csv(DAILY_FILE, usecols=columns)
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily = daily.dropna(subset=["date"]).sort_values("date")

    # Keep station values only when all 24 hourly readings were present.
    for station in STATIONS:
        count_column = f"{station}_n_valid"
        mean_column = f"{station}_mean"
        daily.loc[daily[count_column] != 24, mean_column] = np.nan

    return daily


def load_hourly_data():
    """Read the hourly file once for the within-day profile plot."""
    hourly = pd.read_csv(
        HOURLY_FILE,
        usecols=["date", "hour", "BienHoa", "ThuDau1"],
    )
    hourly["date"] = pd.to_datetime(hourly["date"], errors="coerce")
    hourly["hour"] = pd.to_numeric(hourly["hour"], errors="coerce")
    for station in ("BienHoa", "ThuDau1"):
        hourly[station] = pd.to_numeric(hourly[station], errors="coerce")

    in_study_period = hourly["date"].between(STUDY_START, STUDY_END)
    valid_hour = hourly["hour"].between(0, 23) & (hourly["hour"] % 1 == 0)
    return hourly.loc[in_study_period & valid_hour].copy()


def save_figure(fig, filename):
    """Save a figure in the EDA output folder."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / filename
    fig.tight_layout()
    fig.savefig(output_file, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_file}")


def plot_time_series(daily):
    # Show monthly summaries across the full daily-file period.
    series = daily.set_index("date")[[Y_COLUMN, X_COLUMN]]
    monthly = series.resample("MS").mean()

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(monthly.index, monthly[Y_COLUMN], label="Bien Hoa", linewidth=1.2)
    ax.plot(monthly.index, monthly[X_COLUMN], label="Thu Dau Mot", linewidth=1.2)
    ax.axvspan(pd.Timestamp(STUDY_START), pd.Timestamp(STUDY_END), alpha=0.08, color="grey")
    ax.set_title("Monthly average of valid daily means, 1985-2025")
    ax.set_xlabel("Date")
    ax.set_ylabel(VALUE_LABEL)
    ax.legend()
    save_figure(fig, "01_time_series_monthly.png")


def plot_distributions(study):
    # Draw each station separately so missing values are handled independently.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, column, label in zip(
        axes,
        (Y_COLUMN, X_COLUMN),
        ("Bien Hoa", "Thu Dau Mot"),
    ):
        values = study[column].dropna()
        sns.histplot(values, bins=40, kde=True, ax=ax, color="steelblue")
        ax.set_title(f"{label}: daily-mean distribution, 2000-2020")
        ax.set_xlabel(VALUE_LABEL)
        ax.set_ylabel("Number of valid days")

    save_figure(fig, "02_daily_mean_distributions.png")


def plot_monthly_boxplots(study):
    # Reshape the two station columns into one value column for seaborn.
    values = study[["date", Y_COLUMN, X_COLUMN]].melt(
        id_vars="date",
        var_name="station",
        value_name="daily_mean",
    ).dropna(subset=["daily_mean"])
    values["month"] = pd.to_datetime(values["date"]).dt.month
    values["station"] = values["station"].map(
        {Y_COLUMN: "Bien Hoa", X_COLUMN: "Thu Dau Mot"}
    )

    fig, ax = plt.subplots(figsize=(13, 5))
    sns.boxplot(
        data=values,
        x="month",
        y="daily_mean",
        hue="station",
        showfliers=False,
        ax=ax,
    )
    ax.set_title("Daily-mean distributions by calendar month, 2000-2020")
    ax.set_xlabel("Calendar month")
    ax.set_ylabel(VALUE_LABEL)
    ax.legend(title="Station")
    save_figure(fig, "03_monthly_boxplots.png")


def plot_same_day_and_lagged(study):
    # Shift X on the full calendar index before dropping missing pairs.
    indexed = study.set_index("date")[[Y_COLUMN, X_COLUMN]].sort_index()
    same_day = indexed[[X_COLUMN, Y_COLUMN]].dropna()
    lagged = pd.DataFrame(
        {
            "X_previous_day": indexed[X_COLUMN].shift(1),
            "Y_current_day": indexed[Y_COLUMN],
        }
    ).dropna()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    chart_data = [
        (same_day[X_COLUMN], same_day[Y_COLUMN], "Same-day: X(t) and Y(t)", "X(t)"),
        (
            lagged["X_previous_day"],
            lagged["Y_current_day"],
            "Lagged: X(t-1) and Y(t)",
            "X(t-1)",
        ),
    ]

    for ax, (x_values, y_values, title, x_label) in zip(axes, chart_data):
        bins = ax.hexbin(x_values, y_values, gridsize=35, mincnt=1, cmap="viridis")
        fig.colorbar(bins, ax=ax, label="Number of day pairs")
        ax.set_title(f"{title} (n={len(x_values)})")
        ax.set_xlabel(f"{x_label}: {STATION_NAMES['ThuDau1']} daily mean")
        ax.set_ylabel(f"Y(t): {STATION_NAMES['BienHoa']} daily mean")

    save_figure(fig, "04_same_day_vs_lagged.png")


def plot_station_correlations(study):
    # Pairwise correlation uses available values for each station pair.
    columns = [f"{station}_mean" for station in STATIONS]
    values = study[columns]
    correlations = values.corr(method="pearson")
    pair_counts = values.notna().astype(int).T.dot(values.notna().astype(int))
    labels = [STATION_NAMES[station] for station in STATIONS]
    correlations.index = labels
    correlations.columns = labels
    pair_counts.index = labels
    pair_counts.columns = labels

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        correlations,
        annot=True,
        fmt=".2f",
        vmin=-1,
        vmax=1,
        center=0,
        cmap="coolwarm",
        square=True,
        ax=ax,
    )
    ax.set_title("Pairwise correlation of daily means, 2000-2020")
    save_figure(fig, "05_station_correlations.png")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pair_counts.to_csv(OUTPUT_DIR / "05_station_pair_counts.csv", encoding="utf-8-sig")


def complete_days_for_station(hourly, station):
    """Return hourly rows from days complete for one station."""
    daily = hourly.groupby("date").agg(
        n_rows=("hour", "size"),
        n_values=(station, "count"),
        n_hours=("hour", "nunique"),
        first_hour=("hour", "min"),
        last_hour=("hour", "max"),
    )
    valid = (
        (daily["n_rows"] == 24)
        & (daily["n_values"] == 24)
        & (daily["n_hours"] == 24)
        & (daily["first_hour"] == 0)
        & (daily["last_hour"] == 23)
    )
    valid_dates = daily.index[valid]
    return hourly.loc[hourly["date"].isin(valid_dates)]


def plot_hourly_profile(hourly):
    # Use each station's complete days, then show hourly median and IQR.
    fig, ax = plt.subplots(figsize=(10, 5))
    for station, label, color in (
        ("BienHoa", "Bien Hoa", "tab:blue"),
        ("ThuDau1", "Thu Dau Mot", "tab:orange"),
    ):
        complete = complete_days_for_station(hourly, station)
        profile = complete.groupby("hour")[station].agg(
            median="median",
            lower=lambda values: values.quantile(0.25),
            upper=lambda values: values.quantile(0.75),
        )
        ax.plot(profile.index, profile["median"], label=label, color=color)
        ax.fill_between(
            profile.index,
            profile["lower"],
            profile["upper"],
            color=color,
            alpha=0.18,
        )

    ax.set_xticks(range(24))
    ax.set_title("Hourly profiles on complete days, 2000-2020")
    ax.set_xlabel("Hour label in source file (0-23)")
    ax.set_ylabel("Hourly value (original unit, unconfirmed)")
    ax.legend(title="Station; shaded area is the interquartile range")
    save_figure(fig, "06_hourly_profiles.png")


def main():
    # Read each source once; reuse the prepared tables for all charts.
    daily = load_daily_data()
    study = daily.loc[daily["date"].between(STUDY_START, STUDY_END)].copy()
    hourly = load_hourly_data()

    print(f"Daily file: {len(daily)} rows, {daily['date'].min().date()} to {daily['date'].max().date()}")
    for station in ("BienHoa", "ThuDau1"):
        valid_count = int(study[f"{station}_mean"].notna().sum())
        print(f"Valid {station} days in 2000-2020: {valid_count}")

    plot_time_series(daily)
    plot_distributions(study)
    plot_monthly_boxplots(study)
    plot_same_day_and_lagged(study)
    plot_station_correlations(study)
    plot_hourly_profile(hourly)


if __name__ == "__main__":
    main()
