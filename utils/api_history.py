#!/usr/bin/env python3
"""
API History - Track and store API usage history

Stores API call history, rate limit events, and usage statistics
for analysis and dashboard display.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class APIHistory:
    """Track and store API usage history"""
    
    def __init__(self, history_file: Optional[Path] = None, retention_days: int = 30):
        """
        Initialize API history tracker
        
        Args:
            history_file: Path to history file (default: ~/.cursor_rotation/api_history.json)
            retention_days: Number of days to retain history (default: 30)
        """
        if history_file is None:
            history_file = Path.home() / ".cursor_rotation" / "api_history.json"
        
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self._history: Dict[str, Any] = self._load_history()
    
    def _load_history(self) -> Dict[str, Any]:
        """Load history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                    # Clean old entries
                    return self._clean_history(data)
            else:
                return {
                    "api_calls": [],
                    "rate_limits": [],
                    "errors": [],
                    "statistics": {},
                }
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return {
                "api_calls": [],
                "rate_limits": [],
                "errors": [],
                "statistics": {},
            }
    
    def _clean_history(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove entries older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        cutoff_iso = cutoff.isoformat()
        
        cleaned = {
            "api_calls": [],
            "rate_limits": [],
            "errors": [],
            "statistics": data.get("statistics", {}),
        }
        
        # Clean API calls
        for call in data.get("api_calls", []):
            if call.get("timestamp", "") >= cutoff_iso:
                cleaned["api_calls"].append(call)
        
        # Clean rate limits
        for limit in data.get("rate_limits", []):
            if limit.get("timestamp", "") >= cutoff_iso:
                cleaned["rate_limits"].append(limit)
        
        # Clean errors
        for error in data.get("errors", []):
            if error.get("timestamp", "") >= cutoff_iso:
                cleaned["errors"].append(error)
        
        return cleaned
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def log_api_call(self, endpoint: str, method: str = "GET", 
                     status_code: Optional[int] = None,
                     response_time_ms: Optional[float] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Log an API call
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            metadata: Additional metadata
        """
        call = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "metadata": metadata or {},
        }
        
        self._history["api_calls"].append(call)
        
        # Keep only last 10000 calls
        if len(self._history["api_calls"]) > 10000:
            self._history["api_calls"] = self._history["api_calls"][-10000:]
        
        self._save_history()
    
    def log_rate_limit(self, reason: str, endpoint: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None):
        """
        Log a rate limit event
        
        Args:
            reason: Reason for rate limit
            endpoint: API endpoint (if applicable)
            metadata: Additional metadata
        """
        limit = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "endpoint": endpoint,
            "metadata": metadata or {},
        }
        
        self._history["rate_limits"].append(limit)
        
        # Keep only last 1000 rate limits
        if len(self._history["rate_limits"]) > 1000:
            self._history["rate_limits"] = self._history["rate_limits"][-1000:]
        
        self._save_history()
    
    def log_error(self, error_type: str, message: str,
                  endpoint: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Log an API error
        
        Args:
            error_type: Type of error (e.g., "401", "500")
            message: Error message
            endpoint: API endpoint (if applicable)
            metadata: Additional metadata
        """
        error = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "endpoint": endpoint,
            "metadata": metadata or {},
        }
        
        self._history["errors"].append(error)
        
        # Keep only last 1000 errors
        if len(self._history["errors"]) > 1000:
            self._history["errors"] = self._history["errors"][-1000:]
        
        self._save_history()
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get usage statistics
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Statistics dictionary
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()
        
        stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rate_limits": 0,
            "errors": 0,
            "avg_response_time_ms": 0.0,
            "endpoints": defaultdict(int),
            "status_codes": defaultdict(int),
            "time_period_hours": hours,
        }
        
        response_times = []
        
        # Analyze API calls
        for call in self._history.get("api_calls", []):
            if call.get("timestamp", "") >= cutoff_iso:
                stats["total_calls"] += 1
                endpoint = call.get("endpoint", "unknown")
                stats["endpoints"][endpoint] += 1
                
                status_code = call.get("status_code")
                if status_code:
                    stats["status_codes"][status_code] += 1
                    if 200 <= status_code < 300:
                        stats["successful_calls"] += 1
                    else:
                        stats["failed_calls"] += 1
                
                if call.get("response_time_ms"):
                    response_times.append(call["response_time_ms"])
        
        # Analyze rate limits
        for limit in self._history.get("rate_limits", []):
            if limit.get("timestamp", "") >= cutoff_iso:
                stats["rate_limits"] += 1
        
        # Analyze errors
        for error in self._history.get("errors", []):
            if error.get("timestamp", "") >= cutoff_iso:
                stats["errors"] += 1
        
        # Calculate average response time
        if response_times:
            stats["avg_response_time_ms"] = sum(response_times) / len(response_times)
        
        # Convert defaultdicts to regular dicts
        stats["endpoints"] = dict(stats["endpoints"])
        stats["status_codes"] = dict(stats["status_codes"])
        
        return stats
    
    def get_recent_rate_limits(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent rate limit events"""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()
        
        recent = []
        for limit in self._history.get("rate_limits", []):
            if limit.get("timestamp", "") >= cutoff_iso:
                recent.append(limit)
        
        return recent
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent error events"""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()
        
        recent = []
        for error in self._history.get("errors", []):
            if error.get("timestamp", "") >= cutoff_iso:
                recent.append(error)
        
        return recent
    
    def export_history(self, output_file: Path, format: str = "json") -> bool:
        """
        Export history to file
        
        Args:
            output_file: Output file path
            format: Export format ("json" or "csv")
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self._history, f, indent=2)
                return True
            elif format == "csv":
                # Simple CSV export
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Type", "Timestamp", "Details"])
                    
                    for call in self._history.get("api_calls", []):
                        writer.writerow([
                            "API_CALL",
                            call.get("timestamp", ""),
                            f"{call.get('method', '')} {call.get('endpoint', '')} - {call.get('status_code', '')}"
                        ])
                    
                    for limit in self._history.get("rate_limits", []):
                        writer.writerow([
                            "RATE_LIMIT",
                            limit.get("timestamp", ""),
                            limit.get("reason", "")
                        ])
                    
                    for error in self._history.get("errors", []):
                        writer.writerow([
                            "ERROR",
                            error.get("timestamp", ""),
                            f"{error.get('error_type', '')}: {error.get('message', '')}"
                        ])
                return True
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            return False
    
    def clear_history(self):
        """Clear all history"""
        self._history = {
            "api_calls": [],
            "rate_limits": [],
            "errors": [],
            "statistics": {},
        }
        self._save_history()

