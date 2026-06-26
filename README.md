# Health Booking Ultra

## Chức năng

- Giao diện web cực đẹp bằng Flask + Bootstrap
- Đăng ký / đăng nhập
- Phân quyền Admin/User
- Admin xem toàn bộ lịch hẹn, tài khoản, bệnh nhân
- User chỉ xem và hủy lịch của chính mình
- CSV đầy đủ: users, clinics, doctors, patients, appointments
- Nhiều dữ liệu mẫu: 20 phòng khám, 30 bác sĩ, lịch hẹn mẫu
- Tìm phòng khám gần nhất bằng distance_km giả lập
- Chọn bác sĩ theo symptom_keyword
- Đặt lịch theo thời gian mong muốn
- Kiểm tra trùng lịch bác sĩ
- Tự động đề xuất giờ khác, cộng thêm 30 phút
- Gửi email thật đến patient_email bằng Gmail App Password
- Tìm kiếm, lọc, xem chi tiết, hủy lịch

## Tài khoản demo

Admin:

```text
username: admin
password: 123456
```

User:

```text
username: user
password: 123456
```

## Cách chạy

```bash
py -m pip install -r requirements.txt
py app.py
```

Mở:

```text
http://127.0.0.1:5000
```

## Cấu hình gửi email thật

Copy `.env.example` thành `.env`, điền:

```env
EMAIL_SENDER=gmail_cua_ban@gmail.com
EMAIL_APP_PASSWORD=app_password_16_ky_tu
```

Không dùng mật khẩu Gmail thường, phải dùng Gmail App Password.


## Bổ sung ảnh bác sĩ

- Mỗi bác sĩ có ảnh avatar riêng trong thư mục `static/images/doctors/`.
- File `doctors.csv` có thêm cột `image`.
- Trang danh sách bác sĩ, chi tiết lịch hẹn và đặt lịch thành công đều hiển thị ảnh bác sĩ.


## Bổ sung ảnh phòng khám

- Mỗi phòng khám có ảnh riêng trong thư mục `static/images/clinics/`.
- File `clinics.csv` có thêm cột `image`.
- Trang danh sách phòng khám, chi tiết lịch hẹn và đặt lịch thành công đều hiển thị ảnh phòng khám.
