# Đề bài: Tính trung bình của Y từ các ngày hợp lệ thuộc giai đoạn 1985–1999 và xem giá trị này
# là mốc tham chiếu cố định

import pandas as pd

# 1. Đọc và chọn cột
df = pd.read_csv("data.csv")
df = df[["datetime", "date", "year", "month", "day", "hour", "BienHoa"]]
df["date"] = pd.to_datetime(df["date"])

# 2. Trung bình ngày, chỉ giữ ngày đủ 24 giờ
ngay_Y = df.groupby("date")["BienHoa"].agg(["mean", "count"])
ngay_Y = ngay_Y[ngay_Y["count"] == 24]

# 3. Tách hai giai đoạn
tham_chieu = ngay_Y.loc["1985-01-01":"1999-12-31"]
suy_luan = ngay_Y.loc["2000-01-01":"2020-12-31"]

mu0 = tham_chieu["Y"].mean()

# 4. Rút mẫu 200 ngày (có hoàn lại) và lưu seed
HAT_GIONG = 2026
mau = suy_luan.sample(n=200, replace=True, random_state=HAT_GIONG)
mau.to_csv("task1_mau_200_ngay.csv")
