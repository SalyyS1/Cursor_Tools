"""
Service Configuration - Windows service and scheduled task settings
"""

from config.settings import ROTATION_CONFIG

# Service Configuration
SERVICE_CONFIG = {
    "poll_interval_seconds": 60,  # How often to check for rotation triggers
    "service_name": "CursorRotationService",
    "service_display_name": "Cursor Trial Rotation Service",
    "service_description": "Automated Cursor Pro trial rotation service with hybrid scheduling",
    "auto_start": True,  # Start service automatically on boot
    "restart_on_failure": True,  # Auto-restart service on failure
    "max_restart_attempts": 3,  # Maximum restart attempts
    "restart_delay_seconds": 10,  # Delay before restart
}

# Scheduled Task Configuration
SCHEDULED_TASK_CONFIG = {
    "task_name": "CursorRotationTask",
    "task_description": "Backup rotation task for Cursor trial rotation",
    "interval_hours": ROTATION_CONFIG.get("scheduled_interval_hours", 12.0),
    "start_time": None,  # None = start immediately, or "HH:mm" format
    "enabled": True,  # Enable scheduled task
}

# Coordination Configuration
COORDINATION_CONFIG = {
    "state_file": None,  # None = auto-detect (~/.cursor_rotation/service_state.json)
    "lock_timeout_seconds": 5.0,  # Timeout for acquiring lock
    "service_priority": True,  # Service takes priority over scheduled task
    "conflict_resolution": "skip",  # "skip" or "wait"
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    "enable_toast": True,  # Enable Windows toast notifications
    "enable_tray": False,  # Enable system tray notifications (requires GUI)
    "enable_log": True,  # Enable log notifications
    "respect_quiet_hours": True,  # Respect quiet hours
    "quiet_hours_start": 22,  # Quiet hours start (10 PM)
    "quiet_hours_end": 8,  # Quiet hours end (8 AM)
    "notification_on_rotation": True,  # Notify on every rotation
    "notification_on_error": True,  # Notify on errors
    "notification_on_service_start": True,  # Notify on service start
    "notification_on_service_stop": True,  # Notify on service stop
}

# Export all configurations
__all__ = [
    "SERVICE_CONFIG",
    "SCHEDULED_TASK_CONFIG",
    "COORDINATION_CONFIG",
    "NOTIFICATION_CONFIG",
]

