# Hướng dẫn workflow preprocessing - Đề tài 04

Tài liệu này giải thích file `preprocessing.py` theo thứ tự chương trình chạy,
các pool dữ liệu được tạo ra, cách gọi từng section và các cú pháp Python/pandas
được dùng. Phần mô tả bám theo code hiện tại trong thư mục `CODE_XSTK`.

## 1. Mục đích của file

File `preprocessing.py` làm hai việc:

1. Đọc dữ liệu giờ một lần và chuẩn bị các trung bình ngày hợp lệ dùng chung.
2. Gọi đúng một hàm `sec1` đến `sec6` để chuẩn bị dữ liệu đầu vào cho phần
   thống kê trong `secN/solving.py`.

Trong bài này:

- `Y` là trung bình ngày tại Biên Hòa, cột CSV `BienHoa`.
- `X` là trung bình ngày tại Thủ Dầu Một, cột CSV `ThuDau1`.
- Mỗi dòng của file CSV gốc là một quan sát theo giờ.
- Mỗi dòng trong pool ngày hợp lệ là trung bình của một ngày, không phải một
  quan sát theo giờ.

## 2. Workflow tổng quát

Khi chạy file, luồng dữ liệu là:

1. Đọc `hourly_cleaned_wide.csv` một lần.
2. Chỉ lấy bốn cột `date`, `hour`, `BienHoa`, `ThuDau1`.
3. Chuyển ngày, giờ và giá trị trạm sang kiểu dữ liệu phù hợp.
4. Bỏ dòng không có ngày hoặc giờ hợp lệ. Giá trị thiếu của trạm được giữ lại
   đến bước kiểm tra ngày đủ dữ liệu.
5. Tính trung bình theo từng ngày riêng cho Biên Hòa và Thủ Dầu Một.
6. Với từng trạm, chỉ giữ ngày có đủ đúng 24 dòng, đủ 24 giá trị không thiếu,
   và đủ 24 giờ khác nhau từ 0 đến 23.
7. Tách pool Y thành giai đoạn tham chiếu 1985-1999 và giai đoạn nghiên cứu
   2000-2020; lấy pool X trong giai đoạn 2000-2020.
8. Ghép Y và X theo ngày để tạo pool các cặp cùng ngày hợp lệ.
9. Chạy hàm section được chọn ở dòng cuối file.

Các bước 1-8 là phần chung. Mỗi lần chạy chỉ có một hàm `secN` được gọi; những
hàm section còn lại không được thực thi.

Sau bước 8, các biến chính có dạng:

| Biến | Index | Cột | Ý nghĩa của mỗi dòng |
| --- | --- | --- | --- |
| `y_study` | `date` | `Y` | Trung bình ngày hợp lệ ở Biên Hòa, 2000-2020 |
| `y_reference` | `date` | `Y` | Trung bình ngày hợp lệ ở Biên Hòa, 1985-1999 |
| `x_study` | `date` | `X` | Trung bình ngày hợp lệ ở Thủ Dầu Một, 2000-2020 |
| `paired_study` | `date` | `Y`, `X` | Cùng một ngày hợp lệ tại cả hai trạm |

`index` là nhãn dòng của pandas. Trong các pool này, index là ngày; các giá trị
ở cột là trung bình ngày tương ứng.

## 3. Vì sao phải tính trung bình ngày trước khi lấy mẫu?

Với mỗi ngày hợp lệ `d`, giá trị Y là:

\[
Y_d = \frac{1}{24}\sum_{h=0}^{23} \text{BienHoa}_{d,h}.
\]

Nghĩa là code lấy 24 giá trị giờ của **một ngày**, tính trung bình của chúng,
rồi đưa đúng một giá trị `Y_d` vào pool. Sau khi có pool ngày hợp lệ trong
2000-2020, sec1 mới rút 200 dòng từ pool này có hoàn lại.

Code không gộp toàn bộ giờ của 2000-2020 thành một trung bình duy nhất để đem
đi lấy mẫu. Trung bình toàn bộ pool chỉ được tính riêng trong sec1 để đối chiếu
với trung bình của 200 mẫu.

## 4. Cách `main()` chuẩn bị dữ liệu chung

### Đọc và chọn cột

```python
df = pd.read_csv(
    DATA_FILE,
    usecols=["date", "hour", "BienHoa", "ThuDau1"],
)
```

- `pd.read_csv(...)` đọc CSV và trả về một `DataFrame` tên là `df`.
- `usecols` giới hạn các cột được nạp vào bộ nhớ.
- `DATA_FILE` là đường dẫn được tạo từ vị trí file code, nên không phụ thuộc
  terminal đang mở ở thư mục nào.

### Chuẩn hóa kiểu dữ liệu

```python
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
```

- `df["date"]` lấy một cột trong DataFrame.
- `pd.to_datetime` đổi dữ liệu ngày sang kiểu ngày giờ mà pandas hiểu được.
- `pd.to_numeric` đổi cột sang số.
- `errors="coerce"` biến giá trị không đổi được thành `NaN`, để code nhận diện
  và loại ở bước phù hợp.

### Tạo điều kiện giờ hợp lệ

```python
valid_hour = (
    df["hour"].notna()
    & df["hour"].between(0, 23)
    & (df["hour"] % 1 == 0)
)
```

`valid_hour` là một dãy giá trị đúng/sai cho từng dòng. Ba điều kiện yêu cầu
giờ có dữ liệu, nằm trong khoảng 0-23 và là số nguyên.

Trong pandas, `&` kết hợp điều kiện theo từng dòng. Mỗi điều kiện được đặt
trong ngoặc; không dùng `and` ở đây vì `and` không so sánh từng dòng của một
cột pandas.

```python
df = df.loc[df["date"].notna() & valid_hour].copy()
```

- `.loc[điều_kiện]` giữ các dòng có điều kiện đúng.
- `.copy()` tạo DataFrame độc lập để các phép gán sau đó không sửa một lát cắt
  ngầm của DataFrame cũ.
- Dòng này chỉ loại ngày/giờ lỗi. NaN của `BienHoa` hoặc `ThuDau1` chưa bị xóa
  toàn cục, vì mỗi trạm phải được kiểm tra tính đầy đủ riêng.

## 5. Hàm `_daily_mean(df, station)`

Hàm này nhận DataFrame giờ và tên trạm, ví dụ:

```python
y_all = _daily_mean(df, "BienHoa")
```

### Nhóm dữ liệu theo ngày

```python
daily = df.groupby("date", sort=True).agg(
    mean=(station, "mean"),
    n_rows=("hour", "size"),
    n_values=(station, "count"),
    n_hours=("hour", "nunique"),
    first_hour=("hour", "min"),
    last_hour=("hour", "max"),
)
```

- `.groupby("date")` chia dữ liệu thành các nhóm; mỗi nhóm là một ngày.
- `.agg(...)` tính các đặc trưng cho từng nhóm.
- Cú pháp `tên_cột_mới=(cột_đầu_vào, phép_tính)` tạo các cột tổng hợp:
  - `mean`: trung bình của trạm trong ngày.
  - `n_rows`: số dòng giờ của ngày, kể cả dòng có NaN ở trạm.
  - `n_values`: số giá trị trạm không thiếu.
  - `n_hours`: số nhãn giờ khác nhau.
  - `first_hour`, `last_hour`: giờ nhỏ nhất và lớn nhất.

### Giữ ngày đủ 24 giờ

```python
valid_day = (
    (daily["n_rows"] == 24)
    & (daily["n_values"] == 24)
    & (daily["n_hours"] == 24)
    & (daily["first_hour"] == 0)
    & (daily["last_hour"] == 23)
)
```

Chỉ giữ ngày thỏa tất cả điều kiện. Việc kiểm tra cả số dòng, số giá trị hợp
lệ và số giờ khác nhau giúp loại ngày thiếu giờ, thiếu giá trị hoặc có giờ lặp.

```python
result = daily.loc[valid_day, "mean"]
```

Kết quả là một `Series`: index là ngày, value là trung bình của trạm trong
ngày. Sau đó `main()` đổi tên Series thành `Y` hoặc `X` và chuyển thành
DataFrame bằng `.to_frame()`.

## 6. Tách giai đoạn và ghép cặp ngày

```python
y_study = y_all.loc[STUDY_START:STUDY_END]
y_reference = y_all.loc[REFERENCE_START:REFERENCE_END]
x_study = x_all.loc[STUDY_START:STUDY_END]
```

`.loc[start:end]` lọc theo khoảng ngày trên `DatetimeIndex`. Vì index đã được
sắp xếp theo ngày, code lấy được giai đoạn nghiên cứu và giai đoạn tham chiếu.

```python
paired_study = pd.concat([y_study, x_study], axis=1).dropna()
```

- `pd.concat(..., axis=1)` ghép hai DataFrame thành hai cột, căn theo index
  ngày. Nhờ vậy Y và X của cùng một dòng luôn thuộc cùng ngày.
- `.dropna()` ở đây chỉ áp dụng lên bảng đã ghép hai pool ngày hợp lệ. Ngày
  thiếu Y hoặc X bị bỏ khỏi pool cặp; pool Y riêng vẫn giữ ngày Y hợp lệ.

## 7. Các hàm section làm gì?

Cú pháp tổng quát để khai báo hàm là:

```python
def sec1(y_study):
    ...
    return sample
```

- `def` bắt đầu khai báo hàm.
- `sec1` là tên hàm; `y_study` là dữ liệu đầu vào mà `main()` truyền vào.
- Thân hàm chỉ chạy khi được gọi, ví dụ `sec1(y_study)`.
- `return sample` trả kết quả về nơi đã gọi hàm. Trong code hiện tại, hàm còn
  lưu CSV để `solving.py` dùng.
- Tên bắt đầu bằng `_`, như `_daily_mean`, là quy ước để đánh dấu hàm trợ giúp
  nội bộ của file; dấu gạch dưới không làm hàm “ẩn” hay thay đổi cách chạy.

| Hàm | Dữ liệu nhận vào | Việc riêng của section | File đầu ra |
| --- | --- | --- | --- |
| `sec1(y_study)` | Y ngày hợp lệ, 2000-2020 | Lưu trung bình toàn pool; rút 200 ngày có hoàn lại bằng seed 2026 | `outputs/sec1/sample_200_Y.csv`, `population_summary.csv` |
| `sec2(y_study, y_reference)` | Pool Y nghiên cứu và tham chiếu | Tính `mu0`; tái tạo đúng mẫu sec1 bằng cùng seed | `outputs/sec2/sample_200_Y.csv`, `reference_mean.csv` |
| `sec3(paired_study)` | Pool Y-X cùng ngày hợp lệ | Rút 200 cặp bằng seed 2027; thêm cột `D = Y - X` | `outputs/sec3/sample_200_paired_days.csv` |
| `sec4(y_study)` | Pool Y nghiên cứu | Chia tháng 1-4, 5-8, 9-12; rút 80 ngày có hoàn lại mỗi nhóm | `outputs/sec4/sample_80_each_month_group.csv` |
| `sec5(paired_study)` | Pool Y-X cùng ngày hợp lệ | Rút 200 cặp bằng seed 2029 cho tương quan/hồi quy | `outputs/sec5/sample_200_paired_days.csv` |
| `sec6(paired_study)` | Pool Y-X cùng ngày hợp lệ | Dịch hai cột về cùng trung bình, giữ từng cặp cho mô phỏng | `outputs/sec6/paired_equal_mean_base.csv` |

Sec2 dùng seed của sec1 vì đề yêu cầu dùng cùng mẫu 200 quan sát. Sec4 dùng
seed 2028, cộng thêm số thứ tự nhóm để mỗi nhóm có lần rút tái lập riêng.

Sec6 chỉ chuẩn bị bảng cặp đã dịch trung bình. Các lần lặp Monte Carlo
`R=1000`, các cỡ mẫu và phép kiểm định là phần xử lý ở `solving.py`.

Trong sec4, `enumerate(month_groups)` tạo hai giá trị mỗi vòng lặp: số thứ tự
nhóm (`group_number`) và thông tin của nhóm (`label`, tháng đầu, tháng cuối).
Điều kiện `months >= first_month` kết hợp với `months <= last_month` tạo một
mặt nạ đúng/sai để lấy các ngày thuộc nhóm tháng đó.

Trong sec6, mỗi cột được dịch bằng cách trừ trung bình cột ban đầu rồi cộng
trung bình chung:

\[
Y_{eq}=Y-\bar Y+\bar m,\qquad
X_{eq}=X-\bar X+\bar m,\qquad
\bar m=\frac{\bar Y+\bar X}{2}.
\]

Phép dịch này làm hai cột có cùng trung bình nhưng không đổi độ lệch của từng
quan sát. Vì các giá trị Y và X vẫn nằm cùng hàng như ban đầu, cấu trúc cặp và
hiệp phương sai giữa hai cột được giữ lại. `.to_numpy()` lấy các giá trị theo
thứ tự dòng để gán chúng vào DataFrame đã có thêm cột ngày.

## 8. Cú pháp lấy mẫu và lưu file

```python
sample = pool.sample(n=size, replace=True, random_state=seed)
```

- `n=size`: số dòng cần rút.
- `replace=True`: lấy có hoàn lại; một ngày có thể xuất hiện nhiều lần.
- `random_state=seed`: cố định cách bốc để chạy lại cùng dữ liệu và seed sẽ
  cho cùng mẫu.

```python
sample = sample.reset_index()
sample.insert(0, "draw_id", range(1, size + 1))
```

- Trước đó ngày đang nằm ở index; `.reset_index()` biến nó thành cột `date`.
- `.insert(0, ...)` thêm `draw_id` vào vị trí cột đầu tiên. Hai lượt rút trùng
  một ngày vẫn phân biệt được bằng `draw_id`.

```python
output_file.parent.mkdir(parents=True, exist_ok=True)
data.to_csv(output_file, index=False, encoding="utf-8-sig")
```

- `Path / "tên thư mục"` ghép đường dẫn theo hệ điều hành.
- `mkdir(..., exist_ok=True)` tạo thư mục output nếu chưa có.
- `index=False` không ghi index pandas thành cột thừa.
- `utf-8-sig` giúp Excel đọc tiếng Việt trong CSV thuận tiện hơn.

## 9. Chọn section và chạy

Cuối `preprocessing.py` hiện có:

```python
if __name__ == "__main__":
    main("sec2")
```

Đổi chuỗi `"sec2"` thành `"sec1"`, `"sec3"`, ..., `"sec6"` để chọn section.
`if __name__ == "__main__"` nghĩa là chỉ gọi `main()` khi chạy trực tiếp file,
không tự chạy khi file được import từ một file Python khác.

Khai báo `def main(section="sec2")` cũng đặt giá trị mặc định là `"sec2"` nếu
code khác gọi `main()` mà không truyền đối số. Khi chạy trực tiếp, dòng cuối
truyền rõ `"sec2"`; đổi chuỗi đó là cách chọn section hiện tại.

Trong PowerShell, từ thư mục `CODE_XSTK`, chạy:

```powershell
.\.venv\Scripts\python.exe .\preprocessing.py
```

Hoặc mở `preprocessing.py` trong VS Code và dùng nút Run Python File, sau khi
chọn interpreter `.venv` của dự án.

## 10. Đọc kết quả và lỗi thường gặp

- CSV của mỗi section nằm trong `outputs/secN/`.
- Nếu `_sample_with_replacement` báo không có ngày hợp lệ, hãy kiểm tra file
  nguồn, tên cột và quy tắc đủ 24 giờ.
- Nếu `pd.read_csv` báo thiếu cột, kiểm tra header của CSV có đúng
  `date`, `hour`, `BienHoa`, `ThuDau1` không.
- Nếu đổi seed, mẫu ngẫu nhiên sẽ đổi. Nếu giữ seed nhưng sửa dữ liệu hoặc
  thứ tự pool, mẫu cũng có thể đổi.
- Các file `secN/solving.py` hiện lưu đề bài làm comment; phép kiểm định,
  khoảng tin cậy, bootstrap, ANOVA, hồi quy và Monte Carlo chưa được viết ở đó.
