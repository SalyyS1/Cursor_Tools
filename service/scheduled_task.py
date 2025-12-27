#!/usr/bin/env python3
"""
Scheduled Task Integration - Create and manage Windows scheduled tasks
"""

import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ScheduledTaskManager:
    """Manage Windows scheduled tasks"""
    
    def __init__(self, task_name: str = "CursorRotationTask"):
        """
        Initialize scheduled task manager
        
        Args:
            task_name: Name of the scheduled task
        """
        self.task_name = task_name
    
    def is_admin(self) -> bool:
        """Check if running with admin privileges"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    
    def create_task(self, 
                   script_path: str,
                   interval_hours: float = 12.0,
                   start_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Create scheduled task
        
        Args:
            script_path: Path to Python script to run
            interval_hours: Interval in hours (default: 12)
            start_time: Start time in HH:mm format (default: now)
        
        Returns:
            Dict with success status and message
        """
        if not self.is_admin():
            return {
                "success": False,
                "error": "Administrator privileges required to create scheduled task"
            }
        
        try:
            # Get Python executable
            python_exe = sys.executable
            
            # Build schtasks command
            # Run every N hours
            if start_time is None:
                # Start immediately
                schedule = f"/SC HOURLY /MO {int(interval_hours)}"
            else:
                # Start at specific time, repeat daily
                schedule = f"/SC DAILY /ST {start_time} /RI {int(interval_hours * 60)}"
            
            # Validate script_path to prevent path traversal
            script_path_obj = Path(script_path).resolve()
            if not script_path_obj.exists():
                return {
                    "success": False,
                    "error": f"Script path does not exist: {script_path}"
                }
            
            # Sanitize task name to prevent injection
            if not self.task_name.replace("_", "").replace("-", "").isalnum():
                return {
                    "success": False,
                    "error": "Task name contains invalid characters"
                }
            
            command = [
                "schtasks", "/CREATE",
                "/TN", self.task_name,
                "/TR", f'"{python_exe}" "{script_path_obj}"',
                schedule,
                "/F"  # Force (overwrite if exists)
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Scheduled task '{self.task_name}' created successfully")
            return {
                "success": True,
                "message": f"Scheduled task '{self.task_name}' created successfully"
            }
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create scheduled task: {e.stderr}")
            return {
                "success": False,
                "error": e.stderr
            }
        except Exception as e:
            logger.error(f"Failed to create scheduled task: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_task(self) -> Dict[str, Any]:
        """Delete scheduled task"""
        if not self.is_admin():
            return {
                "success": False,
                "error": "Administrator privileges required to delete scheduled task"
            }
        
        try:
            result = subprocess.run(
                ["schtasks", "/DELETE", "/TN", self.task_name, "/F"],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Scheduled task '{self.task_name}' deleted successfully")
            return {
                "success": True,
                "message": f"Scheduled task '{self.task_name}' deleted successfully"
            }
        
        except subprocess.CalledProcessError as e:
            # Task might not exist
            if "does not exist" in e.stderr.lower():
                return {
                    "success": True,
                    "message": f"Scheduled task '{self.task_name}' does not exist"
                }
            logger.error(f"Failed to delete scheduled task: {e.stderr}")
            return {
                "success": False,
                "error": e.stderr
            }
        except Exception as e:
            logger.error(f"Failed to delete scheduled task: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def task_exists(self) -> bool:
        """Check if scheduled task exists"""
        try:
            result = subprocess.run(
                ["schtasks", "/QUERY", "/TN", self.task_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get scheduled task status"""
        try:
            result = subprocess.run(
                ["schtasks", "/QUERY", "/TN", self.task_name, "/FO", "LIST", "/V"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse output
            status = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    status[key.strip()] = value.strip()
            
            return {
                "success": True,
                "exists": True,
                "status": status
            }
        
        except subprocess.CalledProcessError:
            return {
                "success": True,
                "exists": False,
                "status": {}
            }
        except Exception as e:
            logger.error(f"Failed to get task status: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "exists": False
            }


def main():
    """CLI for scheduled task management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Windows scheduled task")
    parser.add_argument("command", choices=["create", "delete", "status"], help="Command to execute")
    parser.add_argument("--script", help="Path to script (for create)")
    parser.add_argument("--interval", type=float, default=12.0, help="Interval in hours (for create)")
    parser.add_argument("--start-time", help="Start time in HH:mm format (for create)")
    
    args = parser.parse_args()
    
    manager = ScheduledTaskManager()
    
    if args.command == "create":
        if not args.script:
            print("ERROR: --script required for create command")
            sys.exit(1)
        result = manager.create_task(args.script, args.interval, args.start_time)
        print(result.get("message", result.get("error", "Unknown error")))
        sys.exit(0 if result.get("success") else 1)
    
    elif args.command == "delete":
        result = manager.delete_task()
        print(result.get("message", result.get("error", "Unknown error")))
        sys.exit(0 if result.get("success") else 1)
    
    elif args.command == "status":
        result = manager.get_task_status()
        if result.get("success"):
            if result.get("exists"):
                print(f"Task exists: {result.get('status')}")
            else:
                print("Task does not exist")
        else:
            print(f"Error: {result.get('error')}")
        sys.exit(0 if result.get("success") else 1)


if __name__ == '__main__':
    main()

