#!/usr/bin/env python3
"""
Account Pool Management - Manage 1-2 Cursor accounts for rotation

Simple account pool for managing 1-2 accounts to rotate unlimited tokens.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AccountPool:
    """Manage pool of 1-2 Cursor accounts"""
    
    def __init__(self, pool_file: Optional[Path] = None, max_accounts: int = 2):
        """
        Initialize account pool
        
        Args:
            pool_file: Path to account pool file (default: ~/.cursor_rotation/account_pool.json)
            max_accounts: Maximum number of accounts (default: 2)
        """
        if pool_file is None:
            pool_file = Path.home() / ".cursor_rotation" / "account_pool.json"
        
        self.pool_file = Path(pool_file)
        self.pool_file.parent.mkdir(parents=True, exist_ok=True)
        self.max_accounts = max_accounts
        self._accounts: Dict[str, Any] = self._load_accounts()
        self._current_account: Optional[str] = None
    
    def _load_accounts(self) -> Dict[str, Any]:
        """Load accounts from file"""
        try:
            if self.pool_file.exists():
                with open(self.pool_file, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                    return data.get("accounts", {})
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to load accounts: {e}")
            return {}
    
    def _save_accounts(self):
        """Save accounts to file"""
        try:
            data = {
                "accounts": self._accounts,
                "current_account": self._current_account,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.pool_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save accounts: {e}")
    
    def add_account(self, account_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add account to pool
        
        Args:
            account_id: Unique account identifier
            metadata: Account metadata (email, etc.)
        
        Returns:
            Result dictionary
        """
        if len(self._accounts) >= self.max_accounts:
            return {
                "success": False,
                "error": f"Maximum {self.max_accounts} accounts allowed"
            }
        
        if account_id in self._accounts:
            return {
                "success": False,
                "error": "Account already exists"
            }
        
        self._accounts[account_id] = {
            "id": account_id,
            "metadata": metadata or {},
            "added_at": datetime.now().isoformat(),
            "last_used": None,
            "rotation_count": 0,
        }
        
        # Set as current if first account
        if not self._current_account:
            self._current_account = account_id
        
        self._save_accounts()
        
        logger.info(f"Account added: {account_id}")
        return {
            "success": True,
            "message": f"Account {account_id} added successfully"
        }
    
    def remove_account(self, account_id: str) -> Dict[str, Any]:
        """
        Remove account from pool
        
        Args:
            account_id: Account identifier
        
        Returns:
            Result dictionary
        """
        if account_id not in self._accounts:
            return {
                "success": False,
                "error": "Account not found"
            }
        
        del self._accounts[account_id]
        
        # Update current account if needed
        if self._current_account == account_id:
            self._current_account = list(self._accounts.keys())[0] if self._accounts else None
        
        self._save_accounts()
        
        logger.info(f"Account removed: {account_id}")
        return {
            "success": True,
            "message": f"Account {account_id} removed successfully"
        }
    
    def get_current_account(self) -> Optional[Dict[str, Any]]:
        """Get current active account"""
        if not self._current_account or self._current_account not in self._accounts:
            return None
        
        return self._accounts[self._current_account].copy()
    
    def switch_account(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Switch to another account
        
        Args:
            account_id: Account to switch to (None = rotate to next)
        
        Returns:
            Result dictionary
        """
        if not self._accounts:
            return {
                "success": False,
                "error": "No accounts in pool"
            }
        
        if account_id is None:
            # Rotate to next account
            account_ids = list(self._accounts.keys())
            if len(account_ids) == 1:
                # Only one account, can't rotate
                return {
                    "success": False,
                    "error": "Only one account in pool"
                }
            
            current_idx = account_ids.index(self._current_account) if self._current_account in account_ids else 0
            next_idx = (current_idx + 1) % len(account_ids)
            account_id = account_ids[next_idx]
        
        if account_id not in self._accounts:
            return {
                "success": False,
                "error": "Account not found"
            }
        
        self._current_account = account_id
        self._accounts[account_id]["last_used"] = datetime.now().isoformat()
        self._save_accounts()
        
        logger.info(f"Switched to account: {account_id}")
        return {
            "success": True,
            "message": f"Switched to account {account_id}",
            "account": self._accounts[account_id].copy()
        }
    
    def record_rotation(self, account_id: Optional[str] = None):
        """
        Record a rotation for an account
        
        Args:
            account_id: Account ID (None = current account)
        """
        if account_id is None:
            account_id = self._current_account
        
        if account_id and account_id in self._accounts:
            self._accounts[account_id]["rotation_count"] = self._accounts[account_id].get("rotation_count", 0) + 1
            self._accounts[account_id]["last_used"] = datetime.now().isoformat()
            self._save_accounts()
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts in pool"""
        return [acc.copy() for acc in self._accounts.values()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get account pool statistics"""
        total_rotations = sum(acc.get("rotation_count", 0) for acc in self._accounts.values())
        
        return {
            "total_accounts": len(self._accounts),
            "current_account": self._current_account,
            "total_rotations": total_rotations,
            "accounts": [
                {
                    "id": acc["id"],
                    "rotation_count": acc.get("rotation_count", 0),
                    "last_used": acc.get("last_used"),
                }
                for acc in self._accounts.values()
            ]
        }
    
    def clear_pool(self):
        """Clear all accounts from pool"""
        self._accounts = {}
        self._current_account = None
        self._save_accounts()
        logger.info("Account pool cleared")

