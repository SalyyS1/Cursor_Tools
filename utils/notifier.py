#!/usr/bin/env python3
"""
Notification System - Toast, tray, and log notifications
"""

import sys
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from core.rotation_scheduler import RotationTrigger
from config.settings import NOTIFICATION_CONFIG

logger = logging.getLogger(__name__)


class Notifier:
    """Notification system for rotation events"""
    
    def __init__(self):
        """Initialize notifier"""
        self.config = NOTIFICATION_CONFIG
        self.enable_toast = self.config.get("enable_toast", True)
        self.enable_tray = self.config.get("enable_tray", False)  # Tray requires GUI
        self.enable_log = self.config.get("enable_log", True)
        self.quiet_hours_start = self.config.get("quiet_hours_start", 22)  # 10 PM
        self.quiet_hours_end = self.config.get("quiet_hours_end", 8)  # 8 AM
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours"""
        current_hour = datetime.now().hour
        if self.quiet_hours_start > self.quiet_hours_end:
            # Quiet hours span midnight
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end
        else:
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end
    
    def _should_notify(self) -> bool:
        """Check if notification should be sent (respect quiet hours)"""
        if not self._is_quiet_hours():
            return True
        
        # Check if quiet hours are enabled
        if not self.config.get("respect_quiet_hours", True):
            return True
        
        return False
    
    def _toast_notify(self, title: str, message: str, duration: int = 5):
        """Send Windows toast notification"""
        if not self.enable_toast or not self._should_notify():
            return
        
        try:
            if sys.platform == "win32":
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=duration, threaded=True)
                except ImportError:
                    # Fallback to Windows API
                    try:
                        import win32api
                        import win32con
                        win32api.MessageBox(0, message, title, win32con.MB_OK | win32con.MB_ICONINFORMATION)
                    except Exception:
                        logger.warning("Toast notification not available")
        except Exception as e:
            logger.error(f"Failed to send toast notification: {e}")
    
    def _log_notify(self, level: str, message: str):
        """Send log notification"""
        if not self.enable_log:
            return
        
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)
    
    def notify_rotation_start(self, trigger: RotationTrigger, reason: Optional[str] = None):
        """Notify rotation start"""
        trigger_name = trigger.value.replace("_", " ").title()
        message = f"Rotation started: {trigger_name}"
        if reason:
            message += f" ({reason})"
        
        self._toast_notify("Cursor Rotation", message)
        self._log_notify("info", f"NOTIFICATION: {message}")
    
    def notify_rotation_complete(self, trigger: RotationTrigger, success: bool, result: Optional[Dict[str, Any]] = None):
        """Notify rotation complete"""
        trigger_name = trigger.value.replace("_", " ").title()
        status = "Success" if success else "Failed"
        message = f"Rotation {status}: {trigger_name}"
        
        if result and not success:
            error = result.get("error", "Unknown error")
            message += f" - {error}"
        
        self._toast_notify("Cursor Rotation", message)
        self._log_notify("info" if success else "error", f"NOTIFICATION: {message}")
    
    def notify_error(self, error_message: str):
        """Notify error"""
        message = f"Error: {error_message}"
        self._toast_notify("Cursor Rotation Error", message, duration=10)
        self._log_notify("error", f"NOTIFICATION: {message}")
    
    def notify_service_started(self):
        """Notify service started"""
        message = "Rotation service started"
        self._toast_notify("Cursor Rotation Service", message)
        self._log_notify("info", f"NOTIFICATION: {message}")
    
    def notify_service_stopped(self):
        """Notify service stopped"""
        message = "Rotation service stopped"
        self._toast_notify("Cursor Rotation Service", message)
        self._log_notify("info", f"NOTIFICATION: {message}")
    
    def notify_token_expired(self):
        """Notify token expired"""
        message = "Token expired - Rotation will be triggered"
        self._toast_notify("Cursor Rotation", message)
        self._log_notify("warning", f"NOTIFICATION: {message}")
    
    def notify_rate_limited(self):
        """Notify rate limited"""
        message = "API rate limited - Rotation will be triggered"
        self._toast_notify("Cursor Rotation", message)
        self._log_notify("warning", f"NOTIFICATION: {message}")


def main():
    """Test notifications"""
    notifier = Notifier()
    
    print("Testing notifications...")
    notifier.notify_rotation_start(RotationTrigger.MANUAL, "Test rotation")
    notifier.notify_rotation_complete(RotationTrigger.MANUAL, True, {})
    notifier.notify_error("Test error")
    print("Notifications sent")


if __name__ == '__main__':
    main()

