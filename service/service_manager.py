#!/usr/bin/env python3
"""
Service Manager - Install, uninstall, and manage Windows service
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import win32serviceutil
    import win32service
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    if sys.platform == "win32":
        logging.warning("pywin32 not available, service management disabled")

from service.rotation_service import RotationService

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manage Windows service installation and status"""
    
    def __init__(self):
        """Initialize service manager"""
        if not WIN32_AVAILABLE:
            raise RuntimeError("pywin32 not available. Install with: pip install pywin32")
        
        self.service_name = RotationService.ServiceFramework._svc_name_
        self.service_display_name = RotationService.ServiceFramework._svc_display_name_
        self.service_description = RotationService.ServiceFramework._svc_description_
    
    def is_admin(self) -> bool:
        """Check if running with admin privileges"""
        try:
            return win32api.GetTokenInformation(
                win32api.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY),
                win32con.TokenElevation
            )
        except Exception:
            # Fallback: try to open a registry key that requires admin
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    "SYSTEM\\CurrentControlSet\\Services",
                    0,
                    winreg.KEY_WRITE
                )
                winreg.CloseKey(key)
                return True
            except Exception:
                return False
    
    def install_service(self, python_exe: Optional[str] = None, script_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Install the Windows service
        
        Args:
            python_exe: Path to Python executable (default: sys.executable)
            script_path: Path to service script (default: auto-detect)
        
        Returns:
            Dict with success status and message
        """
        if not self.is_admin():
            return {
                "success": False,
                "error": "Administrator privileges required to install service"
            }
        
        try:
            if python_exe is None:
                python_exe = sys.executable
            
            if script_path is None:
                # Auto-detect service script
                script_path = Path(__file__).parent / "rotation_service.py"
            
            # Install service using win32serviceutil
            win32serviceutil.InstallService(
                python_exe,
                self.service_name,
                self.service_display_name,
                description=self.service_description,
                startType=win32service.SERVICE_AUTO_START,
                exeName=python_exe,
                exeArgs=f'"{script_path}"'
            )
            
            logger.info(f"Service '{self.service_name}' installed successfully")
            return {
                "success": True,
                "message": f"Service '{self.service_display_name}' installed successfully"
            }
        
        except Exception as e:
            logger.error(f"Failed to install service: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def uninstall_service(self) -> Dict[str, Any]:
        """Uninstall the Windows service"""
        if not self.is_admin():
            return {
                "success": False,
                "error": "Administrator privileges required to uninstall service"
            }
        
        try:
            win32serviceutil.RemoveService(self.service_name)
            logger.info(f"Service '{self.service_name}' uninstalled successfully")
            return {
                "success": True,
                "message": f"Service '{self.service_display_name}' uninstalled successfully"
            }
        
        except Exception as e:
            logger.error(f"Failed to uninstall service: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def start_service(self) -> Dict[str, Any]:
        """Start the Windows service"""
        if not self.is_admin():
            return {
                "success": False,
                "error": "Administrator privileges required to start service"
            }
        
        try:
            win32serviceutil.StartService(self.service_name)
            logger.info(f"Service '{self.service_name}' started")
            return {
                "success": True,
                "message": f"Service '{self.service_display_name}' started"
            }
        
        except Exception as e:
            logger.error(f"Failed to start service: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop_service(self) -> Dict[str, Any]:
        """Stop the Windows service"""
        if not self.is_admin():
            return {
                "success": False,
                "error": "Administrator privileges required to stop service"
            }
        
        try:
            win32serviceutil.StopService(self.service_name)
            logger.info(f"Service '{self.service_name}' stopped")
            return {
                "success": True,
                "message": f"Service '{self.service_display_name}' stopped"
            }
        
        except Exception as e:
            logger.error(f"Failed to stop service: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        try:
            status = win32serviceutil.QueryServiceStatus(self.service_name)
            state = status[1]
            
            # Map Windows service states
            state_map = {
                win32service.SERVICE_STOPPED: "stopped",
                win32service.SERVICE_START_PENDING: "starting",
                win32service.SERVICE_STOP_PENDING: "stopping",
                win32service.SERVICE_RUNNING: "running",
                win32service.SERVICE_CONTINUE_PENDING: "continuing",
                win32service.SERVICE_PAUSE_PENDING: "pausing",
                win32service.SERVICE_PAUSED: "paused",
            }
            
            return {
                "success": True,
                "status": state_map.get(state, "unknown"),
                "state_code": state
            }
        
        except Exception as e:
            logger.error(f"Failed to get service status: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "status": "unknown"
            }
    
    def is_service_installed(self) -> bool:
        """Check if service is installed"""
        try:
            self.get_service_status()
            return True
        except Exception:
            return False


def main():
    """CLI for service management"""
    if not WIN32_AVAILABLE:
        print("ERROR: pywin32 not available. Install with: pip install pywin32")
        sys.exit(1)
    
    manager = ServiceManager()
    
    if len(sys.argv) < 2:
        print("Usage: python service_manager.py [install|uninstall|start|stop|status]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "install":
        result = manager.install_service()
        print(result.get("message", result.get("error", "Unknown error")))
        sys.exit(0 if result.get("success") else 1)
    
    elif command == "uninstall":
        result = manager.uninstall_service()
        print(result.get("message", result.get("error", "Unknown error")))
        sys.exit(0 if result.get("success") else 1)
    
    elif command == "start":
        result = manager.start_service()
        print(result.get("message", result.get("error", "Unknown error")))
        sys.exit(0 if result.get("success") else 1)
    
    elif command == "stop":
        result = manager.stop_service()
        print(result.get("message", result.get("error", "Unknown error")))
        sys.exit(0 if result.get("success") else 1)
    
    elif command == "status":
        result = manager.get_service_status()
        if result.get("success"):
            print(f"Service status: {result.get('status')}")
        else:
            print(f"Error: {result.get('error')}")
        sys.exit(0 if result.get("success") else 1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()

