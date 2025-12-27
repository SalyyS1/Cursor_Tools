# 🚀 Cursor Tools - Hệ thống Quản lý Trial & Rotation

**Công cụ hỗ trợ tạo và xoay account Cursor Pro trial không giới hạn**

*✅ **Hoàn toàn miễn phí** | 🚫 **Không cần đăng ký** | 🎯 **Tự động hóa hoàn toàn** | 🧠 **Thông minh & An toàn** | 🛡️ **Bảo mật cao***

**🚀 Tự động phát hiện token hết hạn | 📊 Dashboard theo dõi real-time | 🔄 Rotation tự động | 🔒 Bảo mật dữ liệu**

---

## 🌟 Tổng quan

**Cursor Tools** là công cụ hỗ trợ quản lý và xoay account Cursor Pro trial một cách tự động và thông minh. Với hệ thống phát hiện token expiration, rotation engine mạnh mẽ, và giao diện dashboard trực quan, bạn có thể dễ dàng quản lý nhiều account và duy trì quyền truy cập không giới hạn.

### ✨ Tính năng nổi bật

| **🎯 Tính năng** | **📝 Mô tả** |
|:---|:---|
| **🔄 Auto Rotation** | Tự động xoay account khi token hết hạn hoặc bị rate limit |
| **📊 Trial Dashboard** | Hiển thị real-time: token còn lại, expiration date, account info |
| **🔍 Token Monitor** | Phát hiện token expiration từ storage.json, database, và log files |
| **📈 API Monitor** | Theo dõi API health, rate limits, và usage patterns |
| **🛡️ Advanced Fingerprinting** | Xoay Machine GUID, MAC address để bypass trial detection |
| **⏰ Scheduled Rotation** | Tự động rotation theo lịch (hybrid: scheduled + reactive) |
| **🖥️ Windows Service** | Chạy background service để monitoring liên tục |
| **📜 Rotation History** | Lưu lịch sử rotation và thống kê chi tiết |
| **🎨 Interactive Menu** | Menu tương tác khi chạy `run.bat` |
| **🌐 Vietnamese UI** | Giao diện hoàn toàn bằng tiếng Việt |

---

## 🚀 Bắt đầu nhanh

### Cài đặt

1. **Clone repository**
   ```bash
   git clone https://github.com/SalyyS1/Cursor_Tools.git
   cd Cursor_Tools
   ```

2. **Cài đặt dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Chạy ứng dụng**
   ```bash
   # Sử dụng menu tương tác (khuyến nghị)
   run.bat
   
   # Hoặc chạy GUI trực tiếp
   python gui_main.py
   ```

### Sử dụng Menu tương tác

Chạy `run.bat` để mở menu tương tác:

```
╔══════════════════════════════════════╗
║   Cursor Tools - Interactive Menu    ║
╚══════════════════════════════════════╝

[1] Launch GUI - Khởi động giao diện
[2] Quick Rotation - Xoay account nhanh
[3] Check Status - Kiểm tra trạng thái
[4] Service Management - Quản lý service
[5] View Rotation History - Xem lịch sử
[6] API Dashboard - Bảng điều khiển API
[7] Configuration - Cấu hình
[0] Exit - Thoát
```

---

## 📊 Trial Dashboard

Dashboard hiển thị thông tin real-time về account Cursor của bạn:

### Thông tin hiển thị

- **🆔 Token Status**: Trạng thái token (Valid/Expired)
- **📊 Remaining Tokens**: Số token còn lại (tự động cập nhật)
- **📅 Expiration Date**: Ngày hết hạn trial
- **⏳ Days Remaining**: Số ngày còn lại
- **👤 Account Info**: Email, Plan, Subscription type
- **🌐 API Status**: Trạng thái API health và rate limits

### Tính năng đặc biệt

- **Auto-refresh**: Tự động cập nhật mỗi 5 giây
- **Debug Info**: Nút "Show Debug Info" để xem chi tiết
- **Color Coding**: Màu sắc thay đổi theo trạng thái (xanh/vàng/đỏ)

---

## 🔄 Rotation System

### Các trigger tự động

1. **Token Expired**: Phát hiện token hết hạn từ:
   - `storage.json` (globalStorage)
   - `state.vscdb` database
   - Log files

2. **Rate Limited**: Phát hiện rate limit từ:
   - API response headers
   - Log file patterns
   - Usage pattern analysis

3. **Scheduled**: Rotation theo lịch (mặc định: 12 giờ)

4. **Manual**: Trigger thủ công từ GUI hoặc menu

### Quy trình rotation

```
1. Pre-validation → Kiểm tra điều kiện
2. Backup → Tạo backup tự động
3. Clean → Dọn dẹp storage và database
4. Advanced Fingerprinting → Xoay Machine GUID, MAC
5. Post-validation → Xác minh rotation thành công
6. Rollback (nếu cần) → Khôi phục nếu lỗi
```

---

## 🛡️ Advanced Fingerprinting

Hệ thống có thể xoay các fingerprint sau để bypass trial detection:

- **Windows Machine GUID**: Registry modification
- **MAC Address**: Network adapter spoofing
- **Storage IDs**: VSCode/Cursor machineId, deviceId
- **Database Records**: OAuth tokens, session data

> ⚠️ **Lưu ý**: Advanced fingerprinting yêu cầu quyền Administrator

---

## ⚙️ Cấu hình

### Rotation Config

Chỉnh sửa `config/settings.py`:

```python
ROTATION_CONFIG = {
    "scheduled_interval_hours": 12.0,  # Lịch rotation
    "enable_token_check": True,         # Bật kiểm tra token
    "enable_rate_limit_check": True,    # Bật kiểm tra rate limit
    "enable_scheduled_rotation": True,   # Bật rotation theo lịch
    "enable_advanced_fingerprint": False,  # Bật advanced fingerprinting
}
```

### Service Config

Cấu hình Windows Service:

```python
SERVICE_CONFIG = {
    "poll_interval_seconds": 60,       # Tần suất kiểm tra
    "state_file_path": "rotation_state.json",
    "notification_enabled": True,       # Bật thông báo
}
```

---

## 📁 Cấu trúc Project

```
Cursor_Tools/
├── core/                    # Core modules
│   ├── token_monitor.py     # Token expiration detection
│   ├── api_monitor.py       # API health monitoring
│   ├── rotation_engine.py   # Rotation logic
│   ├── rotation_scheduler.py # Scheduling system
│   └── advanced_fingerprint.py # Fingerprinting
├── gui/                     # GUI components
│   ├── trial_dashboard.py   # Trial dashboard widget
│   ├── api_dashboard.py     # API dashboard widget
│   ├── control_panel.py     # Control panel
│   └── rotation_history.py  # History viewer
├── service/                 # Windows Service
│   ├── rotation_service.py  # Background service
│   ├── service_manager.py  # Service management
│   └── scheduled_task.py    # Scheduled tasks
├── utils/                   # Utilities
│   ├── rotation_history.py  # History storage
│   ├── account_pool.py      # Account management
│   └── notifier.py          # Notifications
├── config/                  # Configuration
│   └── settings.py          # Main settings
├── locales/                 # Localization
│   └── vi.json              # Vietnamese translations
├── gui_main.py              # Main GUI entry point
├── run.bat                   # Interactive menu
└── requirements.txt          # Dependencies
```

---

## 🔧 Troubleshooting

### Token không được phát hiện

1. Kiểm tra Cursor đang mở folder nào
2. Nhấn "Show Debug Info" trong Trial Dashboard
3. Kiểm tra log files trong `logs/` directory
4. Đảm bảo đang check đúng `globalStorage` (không phải `workspaceStorage`)

### Rotation không hoạt động

1. Kiểm tra quyền Administrator (cho advanced fingerprinting)
2. Đảm bảo Cursor đã đóng hoàn toàn
3. Kiểm tra service status: `python -m service.service_manager status`
4. Xem logs trong `logs/rotation.log`

### Dashboard hiển thị "Unknown"

1. Đảm bảo Cursor đang mở
2. Kiểm tra `storage.json` có tồn tại trong `globalStorage`
3. Sử dụng "Show Debug Info" để xem keys có sẵn
4. Có thể cần thêm patterns trong `token_monitor.py`

---

## 🛡️ Bảo mật & Quyền riêng tư

- **Local Only**: Tất cả dữ liệu chỉ lưu local, không gửi lên server
- **Backup Tự động**: Mọi thay đổi đều được backup trước
- **Rollback Support**: Có thể khôi phục nếu có lỗi
- **No Telemetry**: Không thu thập dữ liệu người dùng

---

## 📝 License

Xem file [LICENSE](./LICENSE) để biết thêm chi tiết.

---

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng:

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

---

## ⚠️ Disclaimer

Công cụ này chỉ dành cho mục đích học tập và nghiên cứu. Người dùng tự chịu trách nhiệm về việc sử dụng công cụ này. Vui lòng tuân thủ các điều khoản sử dụng của Cursor và pháp luật địa phương.

---

## 🌟 Star History

Nếu project này hữu ích, hãy cho một ⭐ để ủng hộ! Star của bạn là động lực lớn nhất để chúng tôi tiếp tục cải thiện!

---

<div align="center">

**⭐ Nếu thấy hữu ích, hãy cho một Star để ủng hộ! Đây là công cụ hoàn toàn miễn phí và mã nguồn mở! ⭐**

**🔥 Hãy để nhiều developer hơn được hưởng lợi, cùng nhau xây dựng giải pháp Cursor Tools tốt nhất! 🔥**

Made with ❤️ by [SalyyS1](https://github.com/SalyyS1)

</div>
