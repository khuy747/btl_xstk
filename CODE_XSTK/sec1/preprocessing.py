# OUTPUT 1: Tìm và bốc ra 200 mẫu trung bình ngày ngẫu nhiên có hoàn lại của biến Biên Hòa trong 2000-2020.
# Tính trung bình mẫu, trung vị, độ lệch chuẩn mẫu và khoảng tin cậy 95% cho
# trung bình theo phân phối t

# Tiếp theo, lập khoảng tin cậy bootstrap percentile từ 999 mẫu
# bootstrap và so sánh hai kết quả

import pandas as pd


#Doc du lieu va gan no bang dataframe
df = pd.read_csv("hourly_cleaned_wide.csv")

#Tim` list cac cot
# print(df.columns) 
#OUTPUT: 'datetime', 'date', 'year', 'month', 'day', 'hour', 'BenLuc', 'BienHoa',
#'PhuAn', 'VungTau', 'ThuDau1', 'NhaBe', 'TanAn'

#Loc ra cac cot can thiet truoc: Thu dau mot, bien hoa, datetime, date, year, month, day, hour
df = df[["datetime", "date", "year", "month", "day", "hour", "BienHoa", "ThuDau1"]]

# Tìm các ngày có số giờ dữ liệu 24. 
ngay_Y = df.groupby("date")["BienHoa"].agg(["mean", "count"])

#Lọc các giá trị NaN 
ngay_Y = ngay_Y.dropna()

# Chỉ giữ ngày đủ 24 giờ
ngay_Y = ngay_Y[ngay_Y["count"] == 24] #Already count not NaN 
print("Số ngày hợp lệ của Y:", len(ngay_Y))


# Giai đoạn tham chiếu 1985-1999
tham_chieu = ngay_Y.loc["1985-01-01":"1999-12-31"]

# Giai đoạn suy luận 2000-2020
suy_luan = ngay_Y.loc["2000-01-01":"2020-12-31"]

print("Số ngày tham chiếu (Y):", len(tham_chieu))
print("Số ngày suy luận (Y):", len(suy_luan))
