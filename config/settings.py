"""
Cấu hình cho AugmentCode Unlimited
Hệ thống bỏ qua giới hạn AugmentCode
"""

import os
import sys
from pathlib import Path

# Thông tin phiên bản
VERSION = "2.0.0"
APP_NAME = "AugmentCode Unlimited"

# Cài đặt mặc định
DEFAULT_SETTINGS = {
    "create_backups": True,      # Tự động tạo backup
    "lock_files": True,           # Khóa file sau khi sửa
    "clean_database": True,       # Dọn dẹp database
    "clean_workspace": True,      # Dọn dẹp workspace
    "verbose": False,             # Hiển thị log chi tiết
    "force_delete": True,        # Xóa mạnh mẽ
}

# Cấu hình JetBrains
JETBRAINS_CONFIG = {
    "id_files": [
        "PermanentDeviceId",  # Base64: UGVybWFuZW50RGV2aWNlSWQ=
        "PermanentUserId",    # Base64: UGVybWFuZW50VXNlcklk
    ],
    # Tên file mã hóa Base64 (tương thích augment-vip)
    "id_files_encoded": [
        "UGVybWFuZW50RGV2aWNlSWQ=",  # PermanentDeviceId
        "UGVybWFuZW50VXNlcklk",      # PermanentUserId
    ],
    "config_dirs": [
        "JetBrains",
    ],
    "database_files": [
        "app-internal-state.db",
        "updatedBrokenPlugins.db",
        "statistics.db",
        "usage.db",
        "device.db",
    ],
    "database_patterns": [
        "*.db",
        "*.sqlite",
        "*.sqlite3",
    ],
    "augment_patterns": [
        "%augment%",
        "%Augment%",
        "%AUGMENT%",
        "%device%",
        "%user%",
        "%machine%",
        "%telemetry%",
    ],
    "cache_dirs": [
        "caches",
        "logs",
        "system",
        "temp",
    ]
}

# Cấu hình VSCode (bao gồm Cursor)
VSCODE_CONFIG = {
    "telemetry_keys": [
        "telemetry.machineId",      # Base64: dGVsZW1ldHJ5Lm1hY2hpbmVJZA==
        "telemetry.devDeviceId",    # Base64: dGVsZW1ldHJ5LmRldkRldmljZUlk
        "telemetry.macMachineId",   # Base64: dGVsZW1ldHJ5Lm1hY01hY2hpbmVJZA==
        "telemetry.sqmId",          # Base64: dGVsZW1ldHJ5LnNxbUlk (trường thiếu)
    ],
    "storage_patterns": {
        "global": [
            ["User", "globalStorage"],
            ["data", "User", "globalStorage"],
        ],
        "workspace": [
            ["User", "workspaceStorage"],
            ["data", "User", "workspaceStorage"],
        ],
        "machine_id": [
            ["User"],
            ["data"],
        ]
    },
    "vscode_variants": [
        "Code",
        "Code - Insiders",
        "VSCodium",
        "Cursor",
        "code-server",
    ],
    "database_files": [
        "state.vscdb",
        "state.vscdb.backup",
    ],
    "service_worker_patterns": [
        ["User", "CachedExtensions"],
        ["User", "logs"],
        ["User", "CachedData"],
        ["CachedData"],
        ["logs"],
    ],
    "cache_directories": [
        "CachedExtensions",
        "CachedData",
        "logs",
        "GPUCache",
        "Service Worker",
    ]
}

# Cấu hình Database
DATABASE_CONFIG = {
    "augment_patterns": [
        "%augment%",
        "%Augment%",
        "%AUGMENT%",
    ],
    "queries": {
        "count": "SELECT COUNT(*) FROM ItemTable WHERE key LIKE ?",
        "delete": "DELETE FROM ItemTable WHERE key LIKE ?",
    },
    # Truy vấn tương thích chính xác với augment-vip
    "precise_queries": {
        "count_augment": "SELECT COUNT(*) FROM ItemTable WHERE key LIKE '%augment%'",
        "delete_augment": "DELETE FROM ItemTable WHERE key LIKE '%augment%'",
    }
}

# Đường dẫn theo nền tảng
def get_platform_paths():
    """Lấy thư mục cơ sở theo nền tảng"""
    if sys.platform == "win32":
        return {
            "config": os.getenv("APPDATA", ""),
            "data": os.getenv("LOCALAPPDATA", ""),
            "home": Path.home(),
        }
    elif sys.platform == "darwin":
        return {
            "config": Path.home() / "Library" / "Application Support",
            "data": Path.home() / "Library" / "Application Support",
            "home": Path.home(),
        }
    else:  # Linux và các hệ thống Unix-like khác
        return {
            "config": Path.home() / ".config",
            "data": Path.home() / ".local" / "share",
            "home": Path.home(),
        }

# Cấu hình Backup
BACKUP_CONFIG = {
    "timestamp_format": "%Y%m%d_%H%M%S",
    "backup_extension": ".bak",
    "max_backups": 10,  # Chỉ giữ 10 backup mới nhất
}

# Cấu hình Logging
LOGGING_CONFIG = {
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "level": "INFO",
}

# Cấu hình thao tác File
FILE_CONFIG = {
    "encoding": "utf-8",
    "chunk_size": 8192,  # Kích thước chunk cho thao tác file
    "max_retries": 3,
    "retry_delay": 1,  # giây
}

# Cài đặt Bảo mật
SECURITY_CONFIG = {
    "verify_paths": True,
    "safe_mode": True,  # Kiểm tra thêm trước các thao tác phá hủy
    "confirm_destructive": False,  # Hỏi xác nhận cho các thao tác phá hủy
}

# Cấu hình Rotation System
ROTATION_CONFIG = {
    "scheduled_interval_hours": 12.0,  # Scheduled rotation interval
    "enable_token_check": True,       # Enable token expiration check
    "enable_rate_limit_check": True,   # Enable rate limit check
    "enable_scheduled_rotation": True,  # Enable scheduled rotation
    "enable_advanced_fingerprint": False,  # Enable advanced fingerprinting (requires admin)
    "log_discovery_cache_duration": 3600,  # Log discovery cache duration (seconds)
    "token_check_cache_duration": 60,      # Token check cache duration (seconds)
    "api_check_cache_duration": 30,        # API check cache duration (seconds)
    "rotation_timeout_seconds": 60,        # Rotation timeout
    "max_rotation_retries": 3,             # Maximum rotation retries
}

# Export all configurations
__all__ = [
    "VERSION",
    "APP_NAME",
    "DEFAULT_SETTINGS",
    "JETBRAINS_CONFIG",
    "VSCODE_CONFIG",
    "DATABASE_CONFIG",
    "BACKUP_CONFIG",
    "LOGGING_CONFIG",
    "FILE_CONFIG",
    "SECURITY_CONFIG",
    "ROTATION_CONFIG",
    "get_platform_paths",
]
