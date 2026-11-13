"""Tiền xử lý chung và chuẩn bị dữ liệu cho từng section của Đề tài 04."""

from pathlib import Path

import pandas as pd


CODE_DIR = Path(__file__).resolve().parent
DATA_FILE = CODE_DIR / "hourly_cleaned_wide.csv"
OUTPUT_DIR = CODE_DIR / "outputs"

REFERENCE_START = "1985-01-01"
REFERENCE_END = "1999-12-31"
STUDY_START = "2000-01-01"
STUDY_END = "2020-12-31"

SAMPLE_SIZE = 200
SEED_SEC1 = 2026
SEED_SEC3 = 2027
SEED_SEC4 = 2028
SEED_SEC5 = 2029


def _daily_mean(df, station):
    """Tính trung bình ngày và chỉ giữ ngày đủ 24 giờ ở một trạm."""
    daily = df.groupby("date", sort=True).agg(
        mean=(station, "mean"),
        n_rows=("hour", "size"),
        n_values=(station, "count"),
        n_hours=("hour", "nunique"),
        first_hour=("hour", "min"),
        last_hour=("hour", "max"),
    )

    valid_day = (
        (daily["n_rows"] == 24)
        & (daily["n_values"] == 24)
        & (daily["n_hours"] == 24)
        & (daily["first_hour"] == 0)
        & (daily["last_hour"] == 23)
    )
    result = daily.loc[valid_day, "mean"]
    result.index.name = "date"
    return result


def _sample_with_replacement(pool, size, seed):
    """Rút mẫu có hoàn lại và đánh số từng lượt rút."""
    if pool.empty:
        raise ValueError("Không có ngày hợp lệ để lấy mẫu.")

    sample = pool.sample(n=size, replace=True, random_state=seed).reset_index()
    sample.insert(0, "draw_id", range(1, size + 1))
    return sample


def _save(data, section, filename):
    output_file = OUTPUT_DIR / section / filename
    output_file.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"Đã lưu: {output_file}")
    return output_file


def sec1(y_study):
    # Workflow: dùng Y hợp lệ 2000-2020 -> lưu mean tổng thể -> rút 200 mẫu.
    sample = _sample_with_replacement(y_study, SAMPLE_SIZE, SEED_SEC1)
    population_summary = pd.DataFrame(
        [{
            "valid_days": len(y_study),
            "population_mean": y_study["Y"].mean(),
        }]
    )
    _save(sample, "sec1", "sample_200_Y.csv")
    _save(population_summary, "sec1", "population_summary.csv")
    print(f"Số ngày Y hợp lệ trong 2000-2020: {len(y_study)}")
    return sample


def sec2(y_study, y_reference):
    # Workflow: tính mốc Y 1985-1999 -> tái tạo mẫu sec1 bằng cùng seed -> lưu cả hai.
    sample = _sample_with_replacement(y_study, SAMPLE_SIZE, SEED_SEC1)
    mu0 = y_reference["Y"].mean()
    reference = pd.DataFrame(
        [{
            "reference_start": REFERENCE_START,
            "reference_end": REFERENCE_END,
            "valid_days": len(y_reference),
            "mu0": mu0,
        }]
    )

    _save(sample, "sec2", "sample_200_Y.csv")
    _save(reference, "sec2", "reference_mean.csv")
    print(f"Trung bình tham chiếu mu0: {mu0}")
    return sample, reference


def sec3(paired_study):
    # Workflow: dùng các ngày hợp lệ cùng ngày -> rút 200 cặp -> thêm D = Y - X.
    sample = _sample_with_replacement(paired_study, SAMPLE_SIZE, SEED_SEC3)
    sample["D"] = sample["Y"] - sample["X"]
    _save(sample, "sec3", "sample_200_paired_days.csv")
    print(f"Số ngày hợp lệ ở cả hai trạm: {len(paired_study)}")
    return sample


def sec4(y_study):
    # Workflow: chia Y theo ba nhóm tháng -> rút 80 mẫu có hoàn lại mỗi nhóm.
    month_groups = [
        ("Tháng 1-4", 1, 4),
        ("Tháng 5-8", 5, 8),
        ("Tháng 9-12", 9, 12),
    ]
    samples = []

    for group_number, (label, first_month, last_month) in enumerate(month_groups):
        months = y_study.index.month
        in_group = (months >= first_month) & (months <= last_month)
        group_pool = y_study.loc[in_group]
        sample = _sample_with_replacement(group_pool, 80, SEED_SEC4 + group_number)
        sample["month"] = pd.to_datetime(sample["date"]).dt.month
        sample["month_group"] = label
        samples.append(sample)
        print(f"{label}: {len(group_pool)} ngày hợp lệ, đã rút 80 mẫu.")

    result = pd.concat(samples, ignore_index=True)
    _save(result, "sec4", "sample_80_each_month_group.csv")
    return result


def sec5(paired_study):
    # Workflow: dùng ngày hợp lệ ở cả hai trạm -> rút 200 cặp cho tương quan/hồi quy.
    sample = _sample_with_replacement(paired_study, SAMPLE_SIZE, SEED_SEC5)
    _save(sample, "sec5", "sample_200_paired_days.csv")
    return sample


def sec6(paired_study):
    # Workflow: dịch hai cột về cùng trung bình, giữ nguyên từng cặp cho mô phỏng.
    common_mean = (paired_study["Y"].mean() + paired_study["X"].mean()) / 2
    result = paired_study.reset_index().copy()
    result["Y_equal_mean"] = (
        paired_study["Y"].to_numpy() - paired_study["Y"].mean() + common_mean
    )
    result["X_equal_mean"] = (
        paired_study["X"].to_numpy() - paired_study["X"].mean() + common_mean
    )
    _save(result, "sec6", "paired_equal_mean_base.csv")
    return result


def main(section="sec1"):
    # 1. Đọc một lần và chỉ giữ các cột dùng trong sáu section.
    df = pd.read_csv(
        DATA_FILE,
        usecols=["date", "hour", "BienHoa", "ThuDau1"],
    )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
    df["BienHoa"] = pd.to_numeric(df["BienHoa"], errors="coerce")
    df["ThuDau1"] = pd.to_numeric(df["ThuDau1"], errors="coerce")

    # 2. Bỏ dòng thiếu ngày/giờ; giữ NaN của trạm để xét đủ 24 giá trị theo ngày.
    valid_hour = (
        df["hour"].notna()
        & df["hour"].between(0, 23)
        & (df["hour"] % 1 == 0)
    )
    df = df.loc[df["date"].notna() & valid_hour].copy()
    df["hour"] = df["hour"].astype(int)

    # 3. Tạo pool ngày hợp lệ từng trạm, rồi tách giai đoạn dùng chung.
    y_all = _daily_mean(df, "BienHoa").rename("Y").to_frame()
    x_all = _daily_mean(df, "ThuDau1").rename("X").to_frame()

    y_study = y_all.loc[STUDY_START:STUDY_END]
    y_reference = y_all.loc[REFERENCE_START:REFERENCE_END]
    x_study = x_all.loc[STUDY_START:STUDY_END]
    paired_study = pd.concat([y_study, x_study], axis=1).dropna()

    print(f"Ngày Y hợp lệ 2000-2020: {len(y_study)}")
    print(f"Ngày Y hợp lệ 1985-1999: {len(y_reference)}")
    print(f"Ngày hợp lệ cùng ngày ở hai trạm: {len(paired_study)}")

    # 4. Chỉ gọi section được chọn; đổi sec1 thành sec2...sec6 để chạy phần khác.
    if section == "sec1":
        return sec1(y_study)
    if section == "sec2":
        return sec2(y_study, y_reference)
    if section == "sec3":
        return sec3(paired_study)
    if section == "sec4":
        return sec4(y_study)
    if section == "sec5":
        return sec5(paired_study)
    if section == "sec6":
        return sec6(paired_study)
    raise ValueError("section phải là sec1, sec2, sec3, sec4, sec5 hoặc sec6")


if __name__ == "__main__":
    main("sec1")  # Đổi tên section tại đây để chọn phần cần chạy.
