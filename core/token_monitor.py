#!/usr/bin/env python3
"""
Token Monitor - Token expiration detection for Cursor

Monitors token status from multiple sources:
1. storage.json - Access/refresh tokens
2. state.vscdb - Database records
3. Log files - API error messages
"""

import json
import sqlite3
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from core.log_discovery import CursorLogDiscovery
from utils.paths import PathManager

logger = logging.getLogger(__name__)


class TokenExpirationMonitor:
    """Monitors token expiration status from multiple sources"""
    
    # Token keys to check in storage.json
    TOKEN_KEYS = [
        'cursorAuth/accessToken',
        'cursorAuth/refreshToken',
        'cursorAuth/cachedSignUpType',
        'augmentcode.accessToken',
        'augmentcode.refreshToken',
        'augmentcode.userInfo',
        'augmentcode.sessionId',
        'workos.accessToken',
        'workos.refreshToken',
        'workos.userInfo',
    ]
    
    # Database patterns for token records
    DB_TOKEN_PATTERNS = [
        '%token%',
        '%auth%',
        '%augment%',
        '%workos%',
        '%cursorAuth%',
    ]
    
    # Log patterns for token errors
    LOG_TOKEN_ERRORS = [
        r'401\s+Unauthorized',
        r'token\s+expired',
        r'token\s+invalid',
        r'authentication\s+failed',
        r'access\s+denied',
    ]
    
    def __init__(self, path_manager: Optional[PathManager] = None, 
                 log_discovery: Optional[CursorLogDiscovery] = None):
        """
        Initialize token monitor
        
        Args:
            path_manager: Path manager instance (optional)
            log_discovery: Log discovery instance (optional)
        """
        self.path_manager = path_manager or PathManager()
        self.log_discovery = log_discovery or CursorLogDiscovery()
        self._last_check_time: Optional[float] = None
        self._cached_status: Optional[Dict[str, Any]] = None
    
    def check_token_status(self, use_cache: bool = True, 
                          cache_duration_seconds: int = 60) -> Dict[str, Any]:
        """
        Check token expiration status from all sources
        
        Args:
            use_cache: Use cached status if available and fresh
            cache_duration_seconds: Cache duration in seconds
            
        Returns:
            Dictionary with token status information
        """
        import time
        
        # Check cache
        if use_cache and self._cached_status and self._last_check_time:
            age = time.time() - self._last_check_time
            if age < cache_duration_seconds:
                return self._cached_status
        
        status = {
            "expired": False,
            "reason": None,
            "sources_checked": [],
            "tokens_found": {},
            "errors": [],
            "last_check": datetime.now().isoformat(),
        }
        
        # Check storage.json
        storage_status = self._check_storage_json()
        status["sources_checked"].append("storage.json")
        if storage_status.get("expired"):
            status["expired"] = True
            status["reason"] = storage_status.get("reason", "Token expired in storage.json")
        status["tokens_found"]["storage"] = storage_status.get("tokens", {})
        if storage_status.get("errors"):
            status["errors"].extend(storage_status["errors"])
        
        # Check state.vscdb
        db_status = self._check_state_database()
        status["sources_checked"].append("state.vscdb")
        if db_status.get("expired"):
            status["expired"] = True
            if not status["reason"]:
                status["reason"] = db_status.get("reason", "Token expired in database")
        status["tokens_found"]["database"] = db_status.get("tokens", {})
        if db_status.get("errors"):
            status["errors"].extend(db_status["errors"])
        
        # Check log files
        log_status = self._check_log_files()
        status["sources_checked"].append("logs")
        if log_status.get("expired"):
            status["expired"] = True
            if not status["reason"]:
                status["reason"] = log_status.get("reason", "Token error detected in logs")
        status["tokens_found"]["logs"] = log_status.get("errors_found", [])
        if log_status.get("errors"):
            status["errors"].extend(log_status["errors"])
        
        # Cache result
        self._cached_status = status
        self._last_check_time = time.time()
        
        return status
    
    def _check_storage_json(self) -> Dict[str, Any]:
        """Check tokens in storage.json files"""
        result = {
            "expired": False,
            "tokens": {},
            "errors": [],
        }
        
        try:
            vscode_dirs = self.path_manager.get_vscode_directories()
            
            for vscode_dir in vscode_dirs:
                storage_file = vscode_dir / "storage.json"
                if not storage_file.exists():
                    continue
                
                try:
                    with open(storage_file, 'r', encoding='utf-8-sig') as f:
                        data = json.load(f)
                    
                    # Check for token keys
                    for key in self.TOKEN_KEYS:
                        if key in data:
                            token_value = data[key]
                            result["tokens"][key] = {
                                "exists": True,
                                "value_length": len(str(token_value)) if token_value else 0,
                                "is_empty": not token_value or token_value == "",
                            }
                            
                            # Check if token is empty (expired/removed)
                            if not token_value or token_value == "":
                                result["expired"] = True
                                result["reason"] = f"Token {key} is empty in storage.json"
                    
                    # Check for subscription/trial info
                    subscription_keys = [
                        'cursorAuth/subscription',
                        'cursorAuth/trialExpiration',
                        'augmentcode.subscription',
                    ]
                    for key in subscription_keys:
                        if key in data:
                            value = data[key]
                            # If expiration date exists, check if expired
                            if isinstance(value, (int, float)) and value > 0:
                                exp_date = datetime.fromtimestamp(value / 1000 if value > 1e10 else value)
                                if exp_date < datetime.now():
                                    result["expired"] = True
                                    result["reason"] = f"Subscription expired: {key}"
                
                except json.JSONDecodeError as e:
                    result["errors"].append(f"JSON decode error in {storage_file}: {e}")
                except Exception as e:
                    result["errors"].append(f"Error reading {storage_file}: {e}")
        
        except Exception as e:
            result["errors"].append(f"Storage check failed: {e}")
        
        return result
    
    def _check_state_database(self) -> Dict[str, Any]:
        """Check tokens in state.vscdb database"""
        result = {
            "expired": False,
            "tokens": {},
            "errors": [],
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
                    
                    # Check if ItemTable exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ItemTable'")
                    if not cursor.fetchone():
                        conn.close()
                        continue
                    
                    # Search for token-related records
                    for pattern in self.DB_TOKEN_PATTERNS:
                        cursor.execute(
                            "SELECT key, value FROM ItemTable WHERE key LIKE ? LIMIT 10",
                            (pattern,)
                        )
                        rows = cursor.fetchall()
                        
                        if rows:
                            result["tokens"][pattern] = len(rows)
                            
                            # Check if tokens are empty/null
                            for key, value in rows:
                                if not value or value == "" or value == "null":
                                    result["expired"] = True
                                    result["reason"] = f"Token record {key} is empty in database"
                    
                    conn.close()
                
                except sqlite3.Error as e:
                    result["errors"].append(f"Database error in {db_file}: {e}")
                except Exception as e:
                    result["errors"].append(f"Error reading {db_file}: {e}")
        
        except Exception as e:
            result["errors"].append(f"Database check failed: {e}")
        
        return result
    
    def _check_log_files(self) -> Dict[str, Any]:
        """Check log files for token error messages"""
        result = {
            "expired": False,
            "errors_found": [],
            "errors": [],
        }
        
        try:
            # Get log files
            log_dirs = self.log_discovery.discover_cursor_logs()
            if not log_dirs:
                return result
            
            # Check recent log files (last 1000 lines)
            for log_dir in log_dirs:
                log_files = list(log_dir.glob("*.log"))
                
                for log_file in log_files[:5]:  # Check up to 5 most recent logs
                    try:
                        # Read last 1000 lines
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                        
                        # Check for token error patterns
                        for line in recent_lines:
                            for pattern in self.LOG_TOKEN_ERRORS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    result["expired"] = True
                                    result["errors_found"].append({
                                        "file": str(log_file),
                                        "pattern": pattern,
                                        "line": line.strip()[:200],  # First 200 chars
                                    })
                                    result["reason"] = f"Token error found in logs: {pattern}"
                                    break
                    
                    except (PermissionError, OSError) as e:
                        result["errors"].append(f"Cannot read {log_file}: {e}")
                    except Exception as e:
                        result["errors"].append(f"Error processing {log_file}: {e}")
        
        except Exception as e:
            result["errors"].append(f"Log check failed: {e}")
        
        return result
    
    def is_token_expired(self) -> bool:
        """
        Quick check if token is expired
        
        Returns:
            True if token is expired, False otherwise
        """
        status = self.check_token_status()
        return status.get("expired", False)
    
    def get_expiration_reason(self) -> Optional[str]:
        """
        Get reason for token expiration
        
        Returns:
            Expiration reason string or None
        """
        status = self.check_token_status()
        return status.get("reason")

