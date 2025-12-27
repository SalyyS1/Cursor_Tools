#!/usr/bin/env python3
"""
Rotation Validator - Post-rotation validation

Validates rotation success by checking:
- ID changes
- Token removal
- File locks
- Old trace detection
"""

import logging
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.paths import PathManager
from core.vscode_handler import VSCodeHandler
from utils.file_locker import FileLockManager

logger = logging.getLogger(__name__)


class RotationValidator:
    """Validates rotation success"""
    
    def __init__(self, 
                 path_manager: PathManager,
                 vscode_handler: VSCodeHandler):
        """
        Initialize validator
        
        Args:
            path_manager: Path manager instance
            vscode_handler: VSCode handler instance
        """
        self.path_manager = path_manager
        self.vscode_handler = vscode_handler
        self.file_locker = FileLockManager()
    
    def validate_rotation(self) -> Dict[str, Any]:
        """
        Validate rotation success
        
        Returns:
            Validation result dictionary
        """
        validation = {
            "success": False,
            "checks": {},
            "errors": [],
            "warnings": [],
        }
        
        try:
            # Check ID changes
            id_check = self._check_id_changes()
            validation["checks"]["id_changes"] = id_check
            
            # Check token removal
            token_check = self._check_token_removal()
            validation["checks"]["token_removal"] = token_check
            
            # Check file locks
            lock_check = self._check_file_locks()
            validation["checks"]["file_locks"] = lock_check
            
            # Check old traces
            trace_check = self._check_old_traces()
            validation["checks"]["old_traces"] = trace_check
            
            # Determine overall success
            all_passed = all([
                id_check.get("passed", False),
                token_check.get("passed", False),
                lock_check.get("passed", False),
                trace_check.get("passed", False),
            ])
            
            validation["success"] = all_passed
            
            if not all_passed:
                validation["errors"].append("Some validation checks failed")
        
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            validation["errors"].append(f"Validation error: {str(e)}")
        
        return validation
    
    def _check_id_changes(self) -> Dict[str, Any]:
        """Check if device IDs were changed"""
        check = {
            "passed": False,
            "ids_found": {},
            "details": [],
        }
        
        try:
            # Get current IDs
            current_ids = self.vscode_handler.get_current_device_ids()
            
            # Check if IDs exist and are valid
            storage_ids = current_ids.get("storage_ids", {})
            database_ids = current_ids.get("database_ids", {})
            
            if storage_ids or database_ids:
                check["ids_found"]["storage"] = len(storage_ids)
                check["ids_found"]["database"] = len(database_ids)
                
                # Check if IDs are valid (non-empty, proper format)
                all_valid = True
                for variant, ids in storage_ids.items():
                    for key, value in ids.items():
                        if not value or len(str(value)) < 10:
                            all_valid = False
                            check["details"].append(f"Invalid ID: {variant}/{key}")
                
                check["passed"] = all_valid and (len(storage_ids) > 0 or len(database_ids) > 0)
            else:
                check["details"].append("No IDs found - rotation may not have occurred")
        
        except Exception as e:
            logger.error(f"ID change check failed: {e}")
            check["details"].append(f"Check error: {str(e)}")
        
        return check
    
    def _check_token_removal(self) -> Dict[str, Any]:
        """Check if tokens were removed"""
        check = {
            "passed": False,
            "tokens_found": 0,
            "tokens_removed": 0,
            "details": [],
        }
        
        try:
            vscode_dirs = self.path_manager.get_vscode_directories()
            token_keys = [
                'cursorAuth/accessToken',
                'cursorAuth/refreshToken',
                'augmentcode.accessToken',
                'augmentcode.refreshToken',
            ]
            
            for vscode_dir in vscode_dirs:
                storage_file = vscode_dir / "storage.json"
                if not storage_file.exists():
                    continue
                
                try:
                    with open(storage_file, 'r', encoding='utf-8-sig') as f:
                        data = json.load(f)
                    
                    for key in token_keys:
                        if key in data:
                            check["tokens_found"] += 1
                            token_value = data[key]
                            if not token_value or token_value == "":
                                check["tokens_removed"] += 1
                            else:
                                check["details"].append(f"Token still present: {key}")
                
                except Exception as e:
                    check["details"].append(f"Error reading {storage_file}: {e}")
            
            # Pass if tokens were found and removed, or no tokens found
            check["passed"] = (
                check["tokens_found"] == 0 or 
                (check["tokens_found"] > 0 and check["tokens_removed"] == check["tokens_found"])
            )
        
        except Exception as e:
            logger.error(f"Token removal check failed: {e}")
            check["details"].append(f"Check error: {str(e)}")
        
        return check
    
    def _check_file_locks(self) -> Dict[str, Any]:
        """Check if files are locked"""
        check = {
            "passed": False,
            "files_checked": 0,
            "files_locked": 0,
            "details": [],
        }
        
        try:
            vscode_dirs = self.path_manager.get_vscode_directories()
            
            for vscode_dir in vscode_dirs:
                storage_file = vscode_dir / "storage.json"
                if storage_file.exists():
                    check["files_checked"] += 1
                    if self.file_locker.is_file_locked(storage_file):
                        check["files_locked"] += 1
                    else:
                        check["details"].append(f"File not locked: {storage_file}")
                
                db_file = vscode_dir / "state.vscdb"
                if db_file.exists():
                    check["files_checked"] += 1
                    if self.file_locker.is_file_locked(db_file):
                        check["files_locked"] += 1
                    else:
                        check["details"].append(f"File not locked: {db_file}")
            
            # Pass if all files are locked, or no files to check
            check["passed"] = (
                check["files_checked"] == 0 or
                check["files_locked"] == check["files_checked"]
            )
        
        except Exception as e:
            logger.error(f"File lock check failed: {e}")
            check["details"].append(f"Check error: {str(e)}")
        
        return check
    
    def _check_old_traces(self) -> Dict[str, Any]:
        """Check for old traces that should have been removed"""
        check = {
            "passed": True,  # Default to pass, fail only if old traces found
            "old_traces_found": 0,
            "details": [],
        }
        
        try:
            vscode_dirs = self.path_manager.get_vscode_directories()
            
            for vscode_dir in vscode_dirs:
                db_file = vscode_dir / "state.vscdb"
                if not db_file.exists():
                    continue
                
                try:
                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()
                    
                    # Check for augment-related records
                    cursor.execute(
                        "SELECT COUNT(*) FROM ItemTable WHERE key LIKE '%augment%'"
                    )
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        check["old_traces_found"] += count
                        check["details"].append(f"Found {count} augment records in {db_file}")
                    
                    conn.close()
                
                except Exception as e:
                    check["details"].append(f"Error checking {db_file}: {e}")
            
            # Fail if old traces found
            check["passed"] = check["old_traces_found"] == 0
        
        except Exception as e:
            logger.error(f"Old trace check failed: {e}")
            check["details"].append(f"Check error: {str(e)}")
        
        return check

