#!/usr/bin/env python3
"""
Windows Service for Cursor Trial Rotation

Implements a Windows background service that continuously monitors
for rotation triggers and performs rotations automatically.
"""

import sys
import os
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    if sys.platform == "win32":
        logging.warning("pywin32 not available, Windows service disabled")

from core.rotation_scheduler import HybridRotationScheduler, RotationTrigger
from core.rotation_engine import RotationEngine
from core.token_monitor import TokenExpirationMonitor
from core.api_monitor import OpusAPIMonitor
from utils.paths import PathManager
from utils.backup import BackupManager
from core.vscode_handler import VSCodeHandler
from utils.rotation_validator import RotationValidator
from utils.notifier import Notifier
from config.settings import ROTATION_CONFIG, SERVICE_CONFIG
from .service_coordinator import ServiceCoordinator

logger = logging.getLogger(__name__)


class RotationService:
    """Windows Service for automated rotation"""
    
    if WIN32_AVAILABLE:
        class ServiceFramework(win32serviceutil.ServiceFramework):
            """Windows Service Framework implementation"""
            
            _svc_name_ = "CursorRotationService"
            _svc_display_name_ = "Cursor Trial Rotation Service"
            _svc_description_ = "Automated Cursor Pro trial rotation service with hybrid scheduling"
            
            def __init__(self, args):
                win32serviceutil.ServiceFramework.__init__(self, args)
                self.stop_event = win32event.CreateEvent(None, 0, 0, None)
                self.service_instance = None
            
            def SvcStop(self):
                """Stop the service"""
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                if self.service_instance:
                    self.service_instance.stop()
                win32event.SetEvent(self.stop_event)
            
            def SvcDoRun(self):
                """Main service execution"""
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )
                self.service_instance = RotationService()
                self.service_instance.run()
    
    def __init__(self):
        """Initialize rotation service"""
        self.running = False
        self.stop_event = threading.Event()
        self.coordinator = ServiceCoordinator()
        
        # Initialize components
        self.path_manager = PathManager()
        self.backup_manager = BackupManager()
        self.vscode_handler = VSCodeHandler(self.path_manager, self.backup_manager)
        self.token_monitor = TokenExpirationMonitor(self.path_manager)
        self.api_monitor = OpusAPIMonitor()
        from utils.file_locker import FileLockManager
        file_locker = FileLockManager()
        self.validator = RotationValidator(
            self.path_manager,
            self.vscode_handler
        )
        self.rotation_engine = RotationEngine(
            self.vscode_handler,
            self.backup_manager,
            self.path_manager,
            self.validator
        )
        self.scheduler = HybridRotationScheduler(
            self.token_monitor,
            self.api_monitor,
            ROTATION_CONFIG.get("scheduled_interval_hours", 12.0)
        )
        self.notifier = Notifier()
        
        # Register rotation callback
        self.scheduler.register_rotation_callback(self._on_rotation_needed)
        
        # Service configuration
        self.poll_interval = SERVICE_CONFIG.get("poll_interval_seconds", 60)
        self.rotation_timeout = ROTATION_CONFIG.get("rotation_timeout_seconds", 60)
    
    def run(self):
        """Main service loop"""
        self.running = True
        logger.info("Rotation service started")
        
        # Mark service as running in coordinator
        self.coordinator.mark_service_running()
        
        try:
            while self.running and not self.stop_event.is_set():
                try:
                    # Check if rotation is needed
                    should_rotate, trigger, reason = self.scheduler.should_rotate()
                    
                    if should_rotate:
                        logger.info(f"Rotation triggered: {trigger.value}, reason: {reason}")
                        self._perform_rotation(trigger, reason)
                    
                    # Update coordinator status
                    self.coordinator.update_status(
                        last_check=time.time(),
                        rotation_in_progress=False
                    )
                    
                    # Sleep for poll interval
                    self.stop_event.wait(self.poll_interval)
                    
                except Exception as e:
                    logger.error(f"Error in service loop: {e}", exc_info=True)
                    self.notifier.notify_error(f"Service error: {e}")
                    # Continue running despite errors
                    self.stop_event.wait(self.poll_interval)
        
        except KeyboardInterrupt:
            logger.info("Service interrupted")
        finally:
            self.running = False
            self.coordinator.mark_service_stopped()
            logger.info("Rotation service stopped")
    
    def stop(self):
        """Stop the service"""
        logger.info("Stopping rotation service...")
        self.running = False
        self.stop_event.set()
    
    def _on_rotation_needed(self, trigger: RotationTrigger):
        """Callback when rotation is needed"""
        logger.info(f"Rotation callback triggered: {trigger.value}")
        self._perform_rotation(trigger, None)
    
    def _perform_rotation(self, trigger: RotationTrigger, reason: Optional[str]):
        """Perform rotation"""
        try:
            # Check if rotation already in progress (via coordinator)
            if self.coordinator.is_rotation_in_progress():
                logger.warning("Rotation already in progress, skipping")
                return
            
            # Mark rotation in progress
            self.coordinator.mark_rotation_in_progress()
            
            # Notify rotation start
            self.notifier.notify_rotation_start(trigger, reason)
            
            # Perform rotation
            result = self.rotation_engine.perform_rotation(trigger)
            
            # Notify rotation complete
            success = result.get("success", False)
            self.notifier.notify_rotation_complete(trigger, success, result)
            
            # Update coordinator
            self.coordinator.mark_rotation_complete(success)
            
            logger.info(f"Rotation completed: success={success}")
            
        except Exception as e:
            logger.error(f"Rotation failed: {e}", exc_info=True)
            self.notifier.notify_error(f"Rotation failed: {e}")
            self.coordinator.mark_rotation_complete(False)
        finally:
            self.coordinator.mark_rotation_idle()
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "running": self.running,
            "last_check": self.coordinator.get_last_check(),
            "rotation_in_progress": self.coordinator.is_rotation_in_progress(),
            "last_rotation": self.coordinator.get_last_rotation(),
        }


def main():
    """Main entry point for service"""
    if not WIN32_AVAILABLE:
        print("ERROR: pywin32 not available. Install with: pip install pywin32")
        sys.exit(1)
    
    if len(sys.argv) == 1:
        # Run as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RotationService.ServiceFramework)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Handle service commands (install, start, stop, remove)
        win32serviceutil.HandleCommandLine(RotationService.ServiceFramework)


if __name__ == '__main__':
    main()

