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
        'cursorAuth/token',
        'cursorAuth/apiToken',
        'augmentcode.accessToken',
        'augmentcode.refreshToken',
        'augmentcode.userInfo',
        'augmentcode.sessionId',
        'augmentcode.token',
        'workos.accessToken',
        'workos.refreshToken',
        'workos.userInfo',
        'workos.token',
        # Also check common patterns
        'authToken',
        'apiToken',
        'sessionToken',
    ]
    
    # Account info keys to check in storage.json
    ACCOUNT_KEYS = [
        'cursorAuth/user',
        'cursorAuth/email',
        'cursorAuth/userId',
        'cursorAuth/subscription',
        'cursorAuth/plan',
        'cursorAuth/trialActive',
        'cursorAuth/trialDaysRemaining',
        'cursorAuth/trialExpiration',
        'augmentcode.userInfo',
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
            
            # Filter to only check globalStorage, not workspaceStorage
            global_storage_dirs = []
            for vscode_dir in vscode_dirs:
                dir_str = str(vscode_dir)
                if 'globalStorage' in dir_str and 'workspaceStorage' not in dir_str:
                    global_storage_dirs.append(vscode_dir)
                elif 'workspaceStorage' not in dir_str:
                    global_storage_dirs.append(vscode_dir)
            
            # Fallback: construct globalStorage path manually if needed
            if not global_storage_dirs:
                import os
                appdata = Path(os.getenv('APPDATA', ''))
                for variant in ['Cursor', 'Code']:
                    global_storage = appdata / variant / 'User' / 'globalStorage'
                    if global_storage.exists():
                        global_storage_dirs.append(global_storage)
            
            for vscode_dir in global_storage_dirs:
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
            
            # Filter to only check globalStorage, not workspaceStorage
            global_storage_dirs = []
            for vscode_dir in vscode_dirs:
                dir_str = str(vscode_dir)
                if 'globalStorage' in dir_str and 'workspaceStorage' not in dir_str:
                    global_storage_dirs.append(vscode_dir)
                elif 'workspaceStorage' not in dir_str:
                    global_storage_dirs.append(vscode_dir)
            
            # Fallback: construct globalStorage path manually if needed
            if not global_storage_dirs:
                import os
                appdata = Path(os.getenv('APPDATA', ''))
                for variant in ['Cursor', 'Code']:
                    global_storage = appdata / variant / 'User' / 'globalStorage'
                    if global_storage.exists():
                        global_storage_dirs.append(global_storage)
            
            for vscode_dir in global_storage_dirs:
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
    
    def get_account_info_from_database(self, vscode_dir: Path) -> Dict[str, Any]:
        """
        Get account information from state.vscdb database
        
        Args:
            vscode_dir: VSCode/Cursor directory path
            
        Returns:
            Dictionary with account information
        """
        account_info = {
            "email": None,
            "user_id": None,
            "plan": None,
            "subscription": None,
        }
        
        try:
            db_file = vscode_dir / "state.vscdb"
            if not db_file.exists():
                return account_info
            
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Check if ItemTable exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ItemTable'")
            if not cursor.fetchone():
                conn.close()
                return account_info
            
            # Search for account-related keys
            account_patterns = [
                '%email%',
                '%user%',
                '%account%',
                '%subscription%',
                '%plan%',
                '%cursorAuth%',
            ]
            
            for pattern in account_patterns:
                cursor.execute(
                    "SELECT key, value FROM ItemTable WHERE key LIKE ? LIMIT 20",
                    (pattern,)
                )
                rows = cursor.fetchall()
                
                for key, value in rows:
                    if not value:
                        continue
                    
                    # Try to parse value as JSON
                    try:
                        if isinstance(value, str):
                            value_obj = json.loads(value)
                            if isinstance(value_obj, dict):
                                if 'email' in value_obj and not account_info["email"]:
                                    account_info["email"] = value_obj['email']
                                if 'plan' in value_obj and not account_info["plan"]:
                                    account_info["plan"] = value_obj['plan']
                                if 'subscription' in value_obj and not account_info["subscription"]:
                                    account_info["subscription"] = value_obj['subscription']
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, check if it's a direct email
                        if isinstance(value, str) and '@' in value and 'email' in key.lower():
                            if not account_info["email"]:
                                account_info["email"] = value
            
            conn.close()
            logger.debug(f"Found account info from database: {account_info}")
        
        except Exception as e:
            logger.debug(f"Error reading database {db_file}: {e}")
        
        return account_info
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get detailed token information including count, expiration, and account info
        
        Returns:
            Dictionary with token count, expiration time, account info, and other info
        """
        import json
        from datetime import datetime
        
        info = {
            "token_count": 0,  # Number of token keys found (for debugging)
            "remaining_tokens": None,  # Actual remaining token quota/credits
            "token_quota": None,  # Total token quota/limit
            "token_usage": None,  # Token usage/consumed
            "expiration_date": None,
            "expiration_timestamp": None,
            "days_remaining": None,
            "trial_active": False,
            "subscription_type": None,
            "plan_type": None,
            "account_email": None,
            "account_user": None,
            "account_user_id": None,
            "tokens": {},
            "account_info": {},
        }
        
        try:
            vscode_dirs = self.path_manager.get_vscode_directories()
            logger.info(f"Found {len(vscode_dirs)} VSCode/Cursor directories: {[str(d) for d in vscode_dirs]}")
            
            if not vscode_dirs:
                logger.warning("No VSCode/Cursor directories found!")
                return info
            
            # Filter to only check globalStorage, not workspaceStorage
            # storage.json is only in globalStorage, not in individual workspace folders
            global_storage_dirs = []
            for vscode_dir in vscode_dirs:
                dir_str = str(vscode_dir)
                # Only check globalStorage directories, skip workspaceStorage subdirectories
                if 'globalStorage' in dir_str and 'workspaceStorage' not in dir_str:
                    global_storage_dirs.append(vscode_dir)
                elif 'workspaceStorage' not in dir_str:  # Also include other non-workspace paths
                    global_storage_dirs.append(vscode_dir)
            
            if not global_storage_dirs:
                logger.warning("No globalStorage directories found! Only workspaceStorage directories were found.")
                # Fallback: try to construct globalStorage path manually
                import os
                appdata = Path(os.getenv('APPDATA', ''))
                for variant in ['Cursor', 'Code']:
                    global_storage = appdata / variant / 'User' / 'globalStorage'
                    if global_storage.exists():
                        global_storage_dirs.append(global_storage)
                        logger.info(f"Found globalStorage via fallback: {global_storage}")
            
            logger.info(f"Checking {len(global_storage_dirs)} globalStorage directories for account info")
            
            for vscode_dir in global_storage_dirs:
                storage_file = vscode_dir / "storage.json"
                logger.debug(f"Checking storage.json: {storage_file}")
                
                if not storage_file.exists():
                    # Only log as debug, not warning, since this is expected for some directories
                    logger.debug(f"storage.json not found: {storage_file}")
                    continue
                
                try:
                    with open(storage_file, 'r', encoding='utf-8-sig') as f:
                        data = json.load(f)
                    
                    # Debug: Log all keys in storage.json to understand structure
                    all_keys = list(data.keys())
                    cursor_keys = [k for k in all_keys if 'cursor' in k.lower() or 'augment' in k.lower() or 'workos' in k.lower()]
                    logger.info(f"Found {len(all_keys)} total keys in storage.json, {len(cursor_keys)} cursor-related keys")
                    logger.debug(f"Cursor-related keys: {cursor_keys[:20]}")  # First 20 keys
                    
                    # Count token keys (for debugging) - Check both known keys and scan for token-like keys
                    for key in self.TOKEN_KEYS:
                        if key in data and data[key]:
                            token_value = data[key]
                            if token_value and str(token_value).strip():  # Not empty
                                info["token_count"] += 1
                                info["tokens"][key] = {
                                    "exists": True,
                                    "length": len(str(token_value)),
                                }
                    
                    # Also scan all keys for token-like patterns (for debugging)
                    for key in all_keys:
                        if key not in info["tokens"]:  # Not already counted
                            key_lower = key.lower()
                            if any(pattern in key_lower for pattern in ['token', 'auth', 'session', 'access', 'refresh']):
                                value = data[key]
                                if value and isinstance(value, str) and len(value) > 10:  # Likely a token
                                    info["token_count"] += 1
                                    info["tokens"][key] = {
                                        "exists": True,
                                        "length": len(str(value)),
                                        "detected_by_pattern": True,
                                    }
                                    logger.debug(f"Detected token-like key: {key}")
                    
                    # Find remaining tokens/quota - This is what we actually want to display
                    remaining_token_keys = [
                        'cursorAuth/remainingTokens',
                        'cursorAuth/tokenQuota',
                        'cursorAuth/tokenLimit',
                        'cursorAuth/remainingCredits',
                        'cursorAuth/creditsRemaining',
                        'cursorAuth/tokenBalance',
                        'cursorAuth/balance',
                        'augmentcode.remainingTokens',
                        'augmentcode.tokenQuota',
                        'augmentcode.creditsRemaining',
                        'workos.remainingTokens',
                        'workos.tokenQuota',
                    ]
                    
                    for key in remaining_token_keys:
                        if key in data and data[key] is not None:
                            value = data[key]
                            logger.debug(f"Found remaining token key {key}: {type(value)} = {value}")
                            
                            if isinstance(value, (int, float)):
                                if info["remaining_tokens"] is None:
                                    info["remaining_tokens"] = int(value)
                                    logger.info(f"Found remaining tokens from {key}: {info['remaining_tokens']}")
                            elif isinstance(value, str):
                                try:
                                    # Try parsing as number
                                    num_value = float(value)
                                    if info["remaining_tokens"] is None:
                                        info["remaining_tokens"] = int(num_value)
                                        logger.info(f"Found remaining tokens from {key}: {info['remaining_tokens']}")
                                except (ValueError, TypeError):
                                    pass
                    
                    # Also check in subscription/userInfo objects
                    for sub_key in ['cursorAuth/subscription', 'cursorAuth/user', 'augmentcode.userInfo', 'workos.userInfo']:
                        if sub_key in data and data[sub_key]:
                            sub_data = data[sub_key]
                            
                            # If it's a string, try parsing as JSON
                            if isinstance(sub_data, str):
                                try:
                                    sub_data = json.loads(sub_data)
                                except (json.JSONDecodeError, TypeError):
                                    continue
                            
                            if isinstance(sub_data, dict):
                                # Check for remaining tokens in subscription object
                                for token_key in ['remainingTokens', 'tokenQuota', 'remainingCredits', 'creditsRemaining', 
                                                 'tokenBalance', 'balance', 'quota', 'remaining', 'tokensRemaining']:
                                    if token_key in sub_data and sub_data[token_key] is not None:
                                        value = sub_data[token_key]
                                        if isinstance(value, (int, float)):
                                            if info["remaining_tokens"] is None:
                                                info["remaining_tokens"] = int(value)
                                                logger.info(f"Found remaining tokens from {sub_key}.{token_key}: {info['remaining_tokens']}")
                                                break
                                
                                # Also check for quota/limit/usage
                                for quota_key in ['tokenQuota', 'quota', 'limit', 'tokenLimit', 'maxTokens']:
                                    if quota_key in sub_data and sub_data[quota_key] is not None:
                                        value = sub_data[quota_key]
                                        if isinstance(value, (int, float)):
                                            if info["token_quota"] is None:
                                                info["token_quota"] = int(value)
                                                logger.debug(f"Found token quota from {sub_key}.{quota_key}: {info['token_quota']}")
                                
                                for usage_key in ['tokenUsage', 'usage', 'tokensUsed', 'consumed']:
                                    if usage_key in sub_data and sub_data[usage_key] is not None:
                                        value = sub_data[usage_key]
                                        if isinstance(value, (int, float)):
                                            if info["token_usage"] is None:
                                                info["token_usage"] = int(value)
                                                logger.debug(f"Found token usage from {sub_key}.{usage_key}: {info['token_usage']}")
                    
                    # Scan all keys for remaining token patterns
                    if info["remaining_tokens"] is None:
                        for key in all_keys:
                            key_lower = key.lower()
                            if any(pattern in key_lower for pattern in ['remainingtoken', 'tokenremaining', 'remainingcredit', 
                                                                      'creditremaining', 'tokenbalance', 'tokenquota']):
                                value = data[key]
                                if isinstance(value, (int, float)) and value >= 0:
                                    info["remaining_tokens"] = int(value)
                                    logger.info(f"Found remaining tokens from pattern scan key {key}: {info['remaining_tokens']}")
                                    break
                                elif isinstance(value, str):
                                    try:
                                        num_value = float(value)
                                        if num_value >= 0:
                                            info["remaining_tokens"] = int(num_value)
                                            logger.info(f"Found remaining tokens from pattern scan key {key}: {info['remaining_tokens']}")
                                            break
                                    except (ValueError, TypeError):
                                        pass
                    
                    # Calculate remaining tokens from quota - usage if we have both
                    if info["remaining_tokens"] is None and info["token_quota"] is not None and info["token_usage"] is not None:
                        info["remaining_tokens"] = max(0, info["token_quota"] - info["token_usage"])
                        logger.info(f"Calculated remaining tokens from quota ({info['token_quota']}) - usage ({info['token_usage']}) = {info['remaining_tokens']}")
                    
                    # Parse account information - Try multiple key patterns
                    # Method 1: Direct cursorAuth keys
                    for key_pattern in ['cursorAuth/email', 'cursorAuth/userEmail', 'cursorAuth/user/email']:
                        if key_pattern in data and data[key_pattern]:
                            info["account_email"] = str(data[key_pattern]).strip()
                            logger.debug(f"Found email from {key_pattern}: {info['account_email']}")
                            break
                    
                    # Method 2: cursorAuth/user object
                    if 'cursorAuth/user' in data and data['cursorAuth/user']:
                        user_data = data['cursorAuth/user']
                        logger.debug(f"Found cursorAuth/user: {type(user_data)}")
                        
                        if isinstance(user_data, dict):
                            info["account_email"] = user_data.get('email') or user_data.get('userEmail') or info["account_email"]
                            info["account_user"] = user_data.get('name') or user_data.get('username') or user_data.get('displayName')
                            info["account_user_id"] = user_data.get('id') or user_data.get('userId') or user_data.get('user_id')
                            logger.debug(f"Parsed user object: email={info['account_email']}, user={info['account_user']}")
                        elif isinstance(user_data, str):
                            # Try parsing as JSON string
                            try:
                                user_obj = json.loads(user_data)
                                if isinstance(user_obj, dict):
                                    info["account_email"] = user_obj.get('email') or info["account_email"]
                                    info["account_user"] = user_obj.get('name') or info["account_user"]
                                    info["account_user_id"] = user_obj.get('id') or info["account_user_id"]
                            except (json.JSONDecodeError, TypeError):
                                info["account_user"] = user_data
                    
                    if 'cursorAuth/userId' in data and data['cursorAuth/userId']:
                        info["account_user_id"] = str(data['cursorAuth/userId'])
                    
                    # Method 3: Check all keys that might contain account info
                    for key in all_keys:
                        if 'email' in key.lower() and data[key]:
                            if not info["account_email"]:
                                email_value = data[key]
                                if isinstance(email_value, str) and '@' in email_value:
                                    info["account_email"] = email_value.strip()
                                    logger.debug(f"Found email from key {key}: {info['account_email']}")
                                    break
                        elif 'user' in key.lower() and 'id' in key.lower() and data[key]:
                            if not info["account_user_id"]:
                                info["account_user_id"] = str(data[key])
                                logger.debug(f"Found user_id from key {key}: {info['account_user_id']}")
                    
                    # Parse userInfo (may be JSON string)
                    for userinfo_key in ['augmentcode.userInfo', 'workos.userInfo']:
                        if userinfo_key in data and data[userinfo_key]:
                            try:
                                userinfo = data[userinfo_key]
                                # If it's a string, try to parse as JSON
                                if isinstance(userinfo, str):
                                    userinfo = json.loads(userinfo)
                                
                                if isinstance(userinfo, dict):
                                    info["account_email"] = userinfo.get('email') or userinfo.get('userEmail') or info["account_email"]
                                    info["account_user"] = userinfo.get('name') or userinfo.get('username') or userinfo.get('userName') or info["account_user"]
                                    info["account_user_id"] = userinfo.get('id') or userinfo.get('userId') or userinfo.get('user_id') or info["account_user_id"]
                                    info["plan_type"] = userinfo.get('plan') or userinfo.get('planType') or info["plan_type"]
                                    info["subscription_type"] = userinfo.get('subscription') or userinfo.get('subscriptionType') or info["subscription_type"]
                            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                                logger.debug(f"Error parsing {userinfo_key}: {e}")
                    
                    # Check subscription/plan type - Try multiple patterns
                    subscription_keys_to_check = [
                        'cursorAuth/subscription',
                        'cursorAuth/subscriptionType',
                        'cursorAuth/subscriptionType',
                        'cursorAuth/plan',
                        'cursorAuth/planType',
                        'cursorAuth/tier',
                        'cursorAuth/currentPlan',
                        'augmentcode.plan',
                        'augmentcode.subscription',
                        'workos.plan',
                        'workos.subscription',
                    ]
                    
                    for sub_key in subscription_keys_to_check:
                        if sub_key in data and data[sub_key]:
                            sub_data = data[sub_key]
                            logger.debug(f"Found subscription/plan key {sub_key}: {type(sub_data)} = {sub_data}")
                            
                            if isinstance(sub_data, dict):
                                # Extract from nested object
                                info["subscription_type"] = sub_data.get('type') or sub_data.get('subscriptionType') or sub_data.get('name') or sub_data.get('subscription') or info["subscription_type"]
                                info["plan_type"] = sub_data.get('plan') or sub_data.get('planType') or sub_data.get('tier') or sub_data.get('currentPlan') or info["plan_type"]
                                
                                logger.info(f"Parsed subscription object: type={info['subscription_type']}, plan={info['plan_type']}")
                                
                                # Check expiration in subscription
                                for exp_key in ['expiresAt', 'expiration', 'expires_at', 'endDate', 'end_date', 'trialExpiration', 'trialEnd']:
                                    if exp_key in sub_data:
                                        exp_value = sub_data[exp_key]
                                        if isinstance(exp_value, (int, float)) and exp_value > 0:
                                            exp_timestamp = exp_value / 1000 if exp_value > 1e10 else exp_value
                                            try:
                                                exp_date = datetime.fromtimestamp(exp_timestamp)
                                                if not info["expiration_date"] or exp_date > info["expiration_date"]:
                                                    info["expiration_date"] = exp_date
                                                    info["expiration_timestamp"] = exp_timestamp
                                                    logger.info(f"Found expiration from {sub_key}.{exp_key}: {exp_date}")
                                                    
                                                    # Calculate days remaining
                                                    if exp_date > datetime.now():
                                                        delta = exp_date - datetime.now()
                                                        info["days_remaining"] = delta.days
                                                        info["trial_active"] = True
                                            except (ValueError, OSError) as e:
                                                logger.debug(f"Error parsing expiration from {sub_key}.{exp_key}: {e}")
                            elif isinstance(sub_data, str):
                                sub_str = sub_data.strip()
                                if sub_str:
                                    if 'plan' in sub_key.lower() or 'tier' in sub_key.lower():
                                        info["plan_type"] = sub_str
                                        logger.info(f"Found plan from {sub_key}: {sub_str}")
                                    else:
                                        info["subscription_type"] = sub_str
                                        logger.info(f"Found subscription from {sub_key}: {sub_str}")
                            elif isinstance(sub_data, (int, float)):
                                # Might be a timestamp or enum
                                if sub_data > 1e10:
                                    try:
                                        exp_date = datetime.fromtimestamp(sub_data / 1000)
                                        if not info["expiration_date"] or exp_date > info["expiration_date"]:
                                            info["expiration_date"] = exp_date
                                            info["expiration_timestamp"] = sub_data
                                    except (ValueError, OSError):
                                        pass
                    
                    # Also scan all keys for plan/subscription patterns
                    if not info["plan_type"]:
                        for key in all_keys:
                            key_lower = key.lower()
                            if ('plan' in key_lower or 'tier' in key_lower) and data[key]:
                                plan_value = data[key]
                                if isinstance(plan_value, str) and plan_value.strip():
                                    info["plan_type"] = plan_value.strip()
                                    logger.info(f"Found plan from pattern scan key {key}: {info['plan_type']}")
                                    break
                                elif isinstance(plan_value, dict):
                                    plan_name = plan_value.get('name') or plan_value.get('type') or plan_value.get('plan')
                                    if plan_name:
                                        info["plan_type"] = str(plan_name)
                                        logger.info(f"Found plan from pattern scan key {key}: {info['plan_type']}")
                                        break
                    
                    if not info["subscription_type"]:
                        for key in all_keys:
                            key_lower = key.lower()
                            if 'subscription' in key_lower and data[key]:
                                sub_value = data[key]
                                if isinstance(sub_value, str) and sub_value.strip():
                                    info["subscription_type"] = sub_value.strip()
                                    logger.info(f"Found subscription from pattern scan key {key}: {info['subscription_type']}")
                                    break
                                elif isinstance(sub_value, dict):
                                    sub_name = sub_value.get('type') or sub_value.get('name') or sub_value.get('subscription')
                                    if sub_name:
                                        info["subscription_type"] = str(sub_name)
                                        logger.info(f"Found subscription from pattern scan key {key}: {info['subscription_type']}")
                                        break
                    
                    # Check subscription/trial expiration - Try multiple patterns
                    expiration_keys_to_check = [
                        'cursorAuth/trialExpiration',
                        'cursorAuth/subscriptionExpiration',
                        'cursorAuth/expiration',
                        'cursorAuth/expiresAt',
                        'augmentcode.subscription',
                        'augmentcode.expiration',
                        'workos.expiration',
                    ]
                    
                    for key in expiration_keys_to_check:
                        if key in data:
                            value = data[key]
                            logger.debug(f"Checking expiration key {key}: {type(value)} = {value}")
                            
                            if isinstance(value, (int, float)) and value > 0:
                                # Convert timestamp
                                exp_timestamp = value / 1000 if value > 1e10 else value
                                try:
                                    exp_date = datetime.fromtimestamp(exp_timestamp)
                                    
                                    if not info["expiration_date"] or exp_date > info["expiration_date"]:
                                        info["expiration_date"] = exp_date
                                        info["expiration_timestamp"] = exp_timestamp
                                        logger.info(f"Found expiration from {key}: {exp_date}")
                                        
                                        # Calculate days remaining
                                        if exp_date > datetime.now():
                                            delta = exp_date - datetime.now()
                                            info["days_remaining"] = delta.days
                                            info["trial_active"] = True
                                            logger.info(f"Days remaining: {info['days_remaining']} days")
                                        else:
                                            info["days_remaining"] = 0
                                            info["trial_active"] = False
                                            logger.info(f"Expiration date has passed")
                                except (ValueError, OSError) as e:
                                    logger.debug(f"Error parsing timestamp from {key}: {e}")
                    
                    # Also scan all keys for expiration-like patterns
                    if not info["expiration_date"]:
                        for key in all_keys:
                            key_lower = key.lower()
                            if any(pattern in key_lower for pattern in ['expiration', 'expires', 'trialend', 'enddate']):
                                value = data[key]
                                if isinstance(value, (int, float)) and value > 0:
                                    exp_timestamp = value / 1000 if value > 1e10 else value
                                    try:
                                        exp_date = datetime.fromtimestamp(exp_timestamp)
                                        if not info["expiration_date"] or exp_date > info["expiration_date"]:
                                            info["expiration_date"] = exp_date
                                            info["expiration_timestamp"] = exp_timestamp
                                            if exp_date > datetime.now():
                                                delta = exp_date - datetime.now()
                                                info["days_remaining"] = delta.days
                                                info["trial_active"] = True
                                            logger.debug(f"Found expiration from pattern scan key {key}: {exp_date}")
                                    except (ValueError, OSError):
                                        pass
                    
                    # Check for trial status - Try multiple patterns
                    trial_keys_to_check = [
                        'cursorAuth/trialActive',
                        'cursorAuth/isTrial',
                        'cursorAuth/trialDaysRemaining',
                        'cursorAuth/trialDaysLeft',
                        'augmentcode.trialActive',
                        'workos.trialActive',
                    ]
                    
                    for trial_key in trial_keys_to_check:
                        if trial_key in data:
                            trial_value = data[trial_key]
                            logger.debug(f"Found trial key {trial_key}: {type(trial_value)} = {trial_value}")
                            
                            if 'active' in trial_key.lower() or 'istrial' in trial_key.lower():
                                if isinstance(trial_value, bool):
                                    info["trial_active"] = trial_value
                                elif trial_value:
                                    info["trial_active"] = True
                                logger.info(f"Trial active: {info['trial_active']}")
                            
                            if 'days' in trial_key.lower():
                                if isinstance(trial_value, (int, float)):
                                    days = int(trial_value)
                                    info["days_remaining"] = days
                                    info["trial_active"] = days > 0
                                    logger.info(f"Trial days remaining: {days}")
                    
                    # Also scan for trial-related keys
                    if info["days_remaining"] is None:
                        for key in all_keys:
                            key_lower = key.lower()
                            if 'trial' in key_lower and 'day' in key_lower and data[key]:
                                days_value = data[key]
                                if isinstance(days_value, (int, float)):
                                    info["days_remaining"] = int(days_value)
                                    info["trial_active"] = info["days_remaining"] > 0
                                    logger.debug(f"Found trial days from pattern scan key {key}: {info['days_remaining']}")
                                    break
                    
                    # Also check database for account info
                    db_account_info = self.get_account_info_from_database(vscode_dir)
                    if db_account_info["email"] and not info["account_email"]:
                        info["account_email"] = db_account_info["email"]
                        logger.debug(f"Found email from database: {info['account_email']}")
                    if db_account_info["plan"] and not info["plan_type"]:
                        info["plan_type"] = db_account_info["plan"]
                    if db_account_info["subscription"] and not info["subscription_type"]:
                        info["subscription_type"] = db_account_info["subscription"]
                    
                    # Store all account info found
                    info["account_info"] = {
                        "email": info["account_email"],
                        "user": info["account_user"],
                        "user_id": info["account_user_id"],
                        "plan": info["plan_type"],
                        "subscription": info["subscription_type"],
                    }
                    
                    # If we found any account info, log it
                    if info["account_email"] or info["account_user"]:
                        logger.info(f"Account detected from {vscode_dir.name}: email={info['account_email']}, user={info['account_user']}, plan={info['plan_type']}")
                
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in {storage_file}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error reading {storage_file}: {e}", exc_info=True)
                    continue
            
            # Log final results
            if info["account_email"]:
                logger.info(f"Successfully detected account: {info['account_email']}")
            else:
                logger.warning("No account email found in storage.json")
            
            if info["plan_type"]:
                logger.info(f"Detected plan: {info['plan_type']}")
        
        except Exception as e:
            logger.error(f"Error getting token info: {e}", exc_info=True)
        
        return info

