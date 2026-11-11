# Chọn các ngày có số liệu hợp lệ ở cả hai trạm trong giai đoạn 2000–2020 và rút ngẫu nhiên
# 200 cặp cùng ngày có hoàn lại. Đặt D = Y −X là chênh lệch chỉ tiêu ngày của hai trạm

import pandas as pd

df = pd.read_csv('hourly_cleaned_wide')
df = df[['date', 'BienHoa', 'ThuDau1']]
df['date'] = pd.to_datetime(df["date"])

# Lọc data mà có thể bốc cặp cùng ngày.

ngay_Y = df.groupby("date")["BienHoa"].agg(["mean", "count"])
ngay_Y = ngay_Y[ngay_Y["count"] == 24].rename(columns={"mean": "Y"})[["Y"]]

ngay_X = df.groupby("date")["ThuDau1"].agg(["mean", "count"])
ngay_X = ngay_X[ngay_X["count"] == 24].rename(columns={"mean": "X"})[["X"]]

cap = ngay_Y.join(ngay_X, how="inner")

# 4. Giai đoạn 2000-2020
cap = cap.loc["2000-01-01":"2020-12-31"]


# 5. Rút 200 cặp cùng ngày, có hoàn lại
HAT_GIONG = 2026
mau_cap = cap.sample(n=200, replace=True, random_state=HAT_GIONG)

# 6. Tính D = Y - X và lưu danh sách ngày
mau_cap["D"] = mau_cap["Y"] - mau_cap["X"]
