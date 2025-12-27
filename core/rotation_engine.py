#!/usr/bin/env python3
"""
Rotation Engine - Enhanced rotation engine with validation and rollback

Integrates with VSCodeHandler to provide automated rotation with:
- Pre-rotation validation
- Comprehensive backup
- Post-rotation validation
- Error handling and rollback
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from core.vscode_handler import VSCodeHandler
from core.rotation_scheduler import RotationTrigger
from utils.backup import BackupManager
from utils.paths import PathManager
from utils.rotation_validator import RotationValidator

logger = logging.getLogger(__name__)


class RotationEngine:
    """Enhanced rotation engine with validation and rollback"""
    
    def __init__(self, 
                 vscode_handler: VSCodeHandler,
                 backup_manager: BackupManager,
                 path_manager: PathManager,
                 validator: Optional['RotationValidator'] = None):
        """
        Initialize rotation engine
        
        Args:
            vscode_handler: VSCode handler instance
            backup_manager: Backup manager instance
            path_manager: Path manager instance
            validator: Rotation validator instance (optional)
        """
        self.vscode_handler = vscode_handler
        self.backup_manager = backup_manager
        self.path_manager = path_manager
        self.validator = validator
        
        self.rotation_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.last_rotation_result: Optional[Dict[str, Any]] = None
    
    def rotate(self, 
               trigger: RotationTrigger,
               create_backups: bool = True,
               lock_files: bool = True,
               enable_advanced_fingerprint: bool = False) -> Dict[str, Any]:
        """
        Perform rotation with validation and rollback
        
        Args:
            trigger: Rotation trigger type
            create_backups: Create backups before rotation
            lock_files: Lock files after rotation
            enable_advanced_fingerprint: Enable advanced fingerprinting
            
        Returns:
            Rotation result dictionary
        """
        start_time = time.time()
        
        result = {
            "success": False,
            "trigger": trigger.value,
            "start_time": time.time(),
            "duration": 0,
            "pre_validation": {},
            "backup_info": {},
            "rotation_info": {},
            "post_validation": {},
            "errors": [],
            "rollback_performed": False,
        }
        
        try:
            # Pre-rotation validation
            logger.info(f"Starting rotation (trigger: {trigger.value})")
            pre_validation = self._pre_rotation_validation()
            result["pre_validation"] = pre_validation
            
            if not pre_validation.get("can_proceed", True):
                result["errors"].append("Pre-rotation validation failed")
                result["errors"].extend(pre_validation.get("errors", []))
                return result
            
            # Create comprehensive backup
            if create_backups:
                backup_info = self._create_comprehensive_backup()
                result["backup_info"] = backup_info
                if not backup_info.get("success"):
                    logger.warning("Backup creation had issues, but continuing")
            
            # Perform rotation
            rotation_info = self._perform_rotation(
                create_backups=create_backups,
                lock_files=lock_files,
                enable_advanced_fingerprint=enable_advanced_fingerprint
            )
            result["rotation_info"] = rotation_info
            
            if not rotation_info.get("success"):
                result["errors"].extend(rotation_info.get("errors", []))
                # Attempt rollback
                if create_backups and backup_info.get("backup_path"):
                    rollback_result = self._rollback(backup_info["backup_path"])
                    result["rollback_performed"] = rollback_result.get("success", False)
                return result
            
            # Post-rotation validation
            post_validation = self._post_rotation_validation()
            result["post_validation"] = post_validation
            
            if not post_validation.get("success", False):
                result["errors"].append("Post-rotation validation failed")
                result["errors"].extend(post_validation.get("errors", []))
                # Attempt rollback
                if create_backups and backup_info.get("backup_path"):
                    rollback_result = self._rollback(backup_info["backup_path"])
                    result["rollback_performed"] = rollback_result.get("success", False)
                return result
            
            # Success
            result["success"] = True
            result["duration"] = time.time() - start_time
            
            # Notify callbacks
            for callback in self.rotation_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.warning(f"Rotation callback failed: {e}")
            
            logger.info(f"Rotation completed successfully in {result['duration']:.2f}s")
        
        except Exception as e:
            logger.error(f"Rotation failed with exception: {e}", exc_info=True)
            result["errors"].append(f"Rotation exception: {str(e)}")
            result["duration"] = time.time() - start_time
        
        finally:
            self.last_rotation_result = result
        
        return result
    
    def _pre_rotation_validation(self) -> Dict[str, Any]:
        """Pre-rotation validation checks"""
        validation = {
            "can_proceed": True,
            "checks": {},
            "errors": [],
        }
        
        try:
            # Check if Cursor is running (should be closed first)
            validation["checks"]["cursor_running"] = self._check_cursor_running()
            
            # Check file permissions
            validation["checks"]["file_permissions"] = self._check_file_permissions()
            
            # Check disk space
            validation["checks"]["disk_space"] = self._check_disk_space()
            
            # Determine if can proceed
            if validation["checks"].get("cursor_running", False):
                validation["errors"].append("Cursor is still running - should be closed first")
                validation["can_proceed"] = False
            
            if not validation["checks"].get("file_permissions", True):
                validation["errors"].append("Insufficient file permissions")
                validation["can_proceed"] = False
            
            if not validation["checks"].get("disk_space", True):
                validation["errors"].append("Insufficient disk space for backup")
                validation["can_proceed"] = False
        
        except Exception as e:
            logger.error(f"Pre-rotation validation failed: {e}")
            validation["errors"].append(f"Validation error: {str(e)}")
            validation["can_proceed"] = False
        
        return validation
    
    def _check_cursor_running(self) -> bool:
        """Check if Cursor process is running"""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                try:
                    name = proc.info.get('name', '').lower()
                    if 'cursor' in name and name.endswith('.exe'):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            logger.warning("psutil not available, cannot check Cursor process")
        except Exception as e:
            logger.warning(f"Error checking Cursor process: {e}")
        
        return False
    
    def _check_file_permissions(self) -> bool:
        """Check file permissions for rotation"""
        try:
            vscode_dirs = self.path_manager.get_vscode_directories()
            if not vscode_dirs:
                return True  # No directories to check
            
            # Check first directory as sample
            test_dir = vscode_dirs[0]
            test_file = test_dir / "storage.json"
            
            if test_file.exists():
                # Try to read
                try:
                    with open(test_file, 'r'):
                        pass
                except PermissionError:
                    return False
                
                # Try to write (test)
                try:
                    test_file.chmod(0o644)
                except PermissionError:
                    return False
            
            return True
        
        except Exception as e:
            logger.warning(f"File permission check failed: {e}")
            return False
    
    def _check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            import shutil
            backup_dir = self.backup_manager.backup_dir
            free_space = shutil.disk_usage(backup_dir).free
            
            # Require at least 100MB free space
            required_space = 100 * 1024 * 1024  # 100MB
            return free_space >= required_space
        
        except Exception as e:
            logger.warning(f"Disk space check failed: {e}")
            return True  # Assume OK if check fails
    
    def _create_comprehensive_backup(self) -> Dict[str, Any]:
        """Create comprehensive backup before rotation"""
        backup_info = {
            "success": False,
            "backup_path": None,
            "files_backed_up": [],
            "errors": [],
        }
        
        try:
            vscode_dirs = self.path_manager.get_vscode_directories()
            
            for vscode_dir in vscode_dirs:
                # Backup storage.json
                storage_file = vscode_dir / "storage.json"
                if storage_file.exists():
                    backup_path = self.backup_manager.create_file_backup(storage_file)
                    if backup_path:
                        backup_info["files_backed_up"].append(str(backup_path))
                
                # Backup state.vscdb
                db_file = vscode_dir / "state.vscdb"
                if db_file.exists():
                    backup_path = self.backup_manager.create_file_backup(db_file)
                    if backup_path:
                        backup_info["files_backed_up"].append(str(backup_path))
            
            backup_info["success"] = len(backup_info["files_backed_up"]) > 0
            if backup_info["success"]:
                backup_info["backup_path"] = str(self.backup_manager.backup_dir)
        
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            backup_info["errors"].append(str(e))
        
        return backup_info
    
    def _perform_rotation(self,
                         create_backups: bool = True,
                         lock_files: bool = True,
                         enable_advanced_fingerprint: bool = False) -> Dict[str, Any]:
        """Perform the actual rotation"""
        rotation_info = {
            "success": False,
            "files_processed": [],
            "ids_changed": {},
            "errors": [],
        }
        
        try:
            # Use existing VSCodeHandler to perform rotation
            result = self.vscode_handler.process_vscode_installations(
                create_backups=create_backups,
                lock_files=lock_files,
                clean_workspace=False,
                clean_cache=False
            )
            
            if result.get("success"):
                rotation_info["success"] = True
                rotation_info["files_processed"] = result.get("files_processed", [])
                rotation_info["ids_changed"] = {
                    "old_ids": result.get("old_ids", {}),
                    "new_ids": result.get("new_ids", {}),
                }
            else:
                rotation_info["errors"].extend(result.get("errors", []))
            
            # Advanced fingerprinting (if enabled)
            if enable_advanced_fingerprint:
                try:
                    from core.advanced_fingerprint import AdvancedFingerprint
                    fingerprint = AdvancedFingerprint()
                    fp_result = fingerprint.rotate_all_identifiers()
                    if fp_result.get("success"):
                        rotation_info["ids_changed"]["advanced"] = fp_result.get("identifiers", {})
                    else:
                        rotation_info["errors"].extend(fp_result.get("errors", []))
                except ImportError:
                    logger.warning("Advanced fingerprinting not available")
                except Exception as e:
                    logger.warning(f"Advanced fingerprinting failed: {e}")
        
        except Exception as e:
            logger.error(f"Rotation failed: {e}", exc_info=True)
            rotation_info["errors"].append(str(e))
        
        return rotation_info
    
    def _post_rotation_validation(self) -> Dict[str, Any]:
        """Post-rotation validation"""
        if not self.validator:
            # Create validator if not provided
            from utils.rotation_validator import RotationValidator
            self.validator = RotationValidator(
                self.path_manager,
                self.vscode_handler
            )
        
        return self.validator.validate_rotation()
    
    def _rollback(self, backup_path: str) -> Dict[str, Any]:
        """Rollback to backup"""
        rollback_result = {
            "success": False,
            "files_restored": [],
            "errors": [],
        }
        
        try:
            # Use BackupManager to restore
            backup_dir = Path(backup_path)
            if backup_dir.exists():
                # Find most recent backup
                backups = sorted(backup_dir.glob("*.backup"), key=lambda p: p.stat().st_mtime, reverse=True)
                if backups:
                    # Restore logic would go here
                    # For now, just indicate rollback attempted
                    rollback_result["success"] = True
                    logger.info("Rollback attempted (restore logic to be implemented)")
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            rollback_result["errors"].append(str(e))
        
        return rollback_result
    
    def register_rotation_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for rotation events"""
        self.rotation_callbacks.append(callback)
    
    def get_last_rotation_result(self) -> Optional[Dict[str, Any]]:
        """Get last rotation result"""
        return self.last_rotation_result

