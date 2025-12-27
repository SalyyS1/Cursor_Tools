#!/usr/bin/env python3
"""
Advanced Fingerprinting - Windows Machine GUID and MAC address rotation

Advanced fingerprinting techniques for better trial rotation:
- Windows Machine GUID rotation
- MAC address spoofing (temporary)
- Registry backup and rollback
"""

import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import time

logger = logging.getLogger(__name__)

# Windows-only module
if sys.platform != "win32":
    logger.warning("Advanced fingerprinting only available on Windows")


class AdvancedFingerprint:
    """Advanced fingerprinting for Windows"""
    
    def __init__(self):
        """Initialize advanced fingerprinting"""
        self.registry_backup_path: Optional[Path] = None
        self.original_guid: Optional[str] = None
        self.requires_admin = True
    
    def rotate_all_identifiers(self) -> Dict[str, Any]:
        """
        Rotate all machine identifiers
        
        Returns:
            Result dictionary
        """
        result = {
            "success": False,
            "identifiers": {},
            "backup_created": False,
            "errors": [],
        }
        
        if sys.platform != "win32":
            result["errors"].append("Advanced fingerprinting only available on Windows")
            return result
        
        try:
            # Check admin rights
            if not self._check_admin_rights():
                result["errors"].append("Admin rights required for advanced fingerprinting")
                return result
            
            # Create registry backup
            backup_result = self._backup_registry()
            result["backup_created"] = backup_result.get("success", False)
            if backup_result.get("backup_path"):
                self.registry_backup_path = Path(backup_result["backup_path"])
            
            # Rotate Windows Machine GUID
            guid_result = self._rotate_windows_machine_guid()
            if guid_result.get("success"):
                result["identifiers"]["machine_guid"] = guid_result.get("new_guid")
            else:
                result["errors"].extend(guid_result.get("errors", []))
            
            # MAC address spoofing (optional, temporary)
            # Note: MAC spoofing requires network adapter manipulation
            # This is complex and may require restart
            # For now, we'll skip it or make it optional
            
            result["success"] = len(result["errors"]) == 0
        
        except Exception as e:
            logger.error(f"Advanced fingerprinting failed: {e}", exc_info=True)
            result["errors"].append(str(e))
        
        return result
    
    def _check_admin_rights(self) -> bool:
        """Check if running with admin rights"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    
    def _backup_registry(self) -> Dict[str, Any]:
        """Backup Windows registry before changes"""
        backup_result = {
            "success": False,
            "backup_path": None,
            "errors": [],
        }
        
        try:
            import winreg
            
            # Backup Machine GUID registry key
            backup_dir = Path.home() / ".cursor_rotation" / "registry_backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"machine_guid_backup_{timestamp}.reg"
            
            # Export registry key using reg.exe
            key_path = r"HKLM\SOFTWARE\Microsoft\Cryptography"
            try:
                result = subprocess.run(
                    ["reg", "export", key_path, str(backup_file), "/y"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and backup_file.exists():
                    backup_result["success"] = True
                    backup_result["backup_path"] = str(backup_file)
                    logger.info(f"Registry backup created: {backup_file}")
                else:
                    backup_result["errors"].append(f"Registry export failed: {result.stderr}")
            
            except subprocess.TimeoutExpired:
                backup_result["errors"].append("Registry backup timeout")
            except Exception as e:
                backup_result["errors"].append(f"Registry backup error: {e}")
        
        except ImportError:
            backup_result["errors"].append("winreg not available")
        except Exception as e:
            logger.error(f"Registry backup failed: {e}")
            backup_result["errors"].append(str(e))
        
        return backup_result
    
    def _rotate_windows_machine_guid(self) -> Dict[str, Any]:
        """Rotate Windows Machine GUID"""
        result = {
            "success": False,
            "old_guid": None,
            "new_guid": None,
            "errors": [],
        }
        
        try:
            import winreg
            import uuid
            
            # Read current GUID
            key_path = r"SOFTWARE\Microsoft\Cryptography"
            value_name = "MachineGuid"
            
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    current_guid, _ = winreg.QueryValueEx(key, value_name)
                    result["old_guid"] = current_guid
                    self.original_guid = current_guid
            except FileNotFoundError:
                result["errors"].append("Machine GUID registry key not found")
                return result
            except Exception as e:
                result["errors"].append(f"Error reading Machine GUID: {e}")
                return result
            
            # Generate new GUID
            new_guid = str(uuid.uuid4())
            result["new_guid"] = new_guid
            
            # Write new GUID
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, new_guid)
                    result["success"] = True
                    logger.info(f"Machine GUID rotated: {current_guid} -> {new_guid}")
            except PermissionError:
                result["errors"].append("Permission denied - admin rights required")
            except Exception as e:
                result["errors"].append(f"Error writing Machine GUID: {e}")
        
        except ImportError:
            result["errors"].append("winreg not available")
        except Exception as e:
            logger.error(f"Machine GUID rotation failed: {e}")
            result["errors"].append(str(e))
        
        return result
    
    def rollback(self) -> Dict[str, Any]:
        """Rollback registry changes"""
        rollback_result = {
            "success": False,
            "errors": [],
        }
        
        if not self.registry_backup_path or not self.registry_backup_path.exists():
            rollback_result["errors"].append("No backup found for rollback")
            return rollback_result
        
        try:
            # Import registry backup
            result = subprocess.run(
                ["reg", "import", str(self.registry_backup_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                rollback_result["success"] = True
                logger.info("Registry rollback successful")
            else:
                rollback_result["errors"].append(f"Registry import failed: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            rollback_result["errors"].append(str(e))
        
        return rollback_result

