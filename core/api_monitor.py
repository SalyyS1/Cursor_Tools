#!/usr/bin/env python3
"""
API Monitor - Opus 4.5 API health and rate limit monitoring

Monitors API health and detects rate limits from:
1. Log file parsing (passive)
2. API response analysis (active - future)
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from core.log_discovery import CursorLogDiscovery

logger = logging.getLogger(__name__)


class OpusAPIMonitor:
    """Monitors Opus 4.5 API health and rate limits"""
    
    # Rate limit error patterns
    RATE_LIMIT_PATTERNS = [
        r'429\s+Too\s+Many\s+Requests',
        r'403\s+Forbidden.*rate',
        r'rate\s+limit',
        r'quota\s+exceeded',
        r'too\s+many\s+requests',
    ]
    
    # API error patterns
    API_ERROR_PATTERNS = [
        r'401\s+Unauthorized',
        r'403\s+Forbidden',
        r'500\s+Internal\s+Server\s+Error',
        r'503\s+Service\s+Unavailable',
    ]
    
    def __init__(self, log_discovery: Optional[CursorLogDiscovery] = None):
        """
        Initialize API monitor
        
        Args:
            log_discovery: Log discovery instance (optional)
        """
        self.log_discovery = log_discovery or CursorLogDiscovery()
        self._last_check_time: Optional[float] = None
        self._cached_status: Optional[Dict[str, Any]] = None
        self._rate_limit_history: List[Dict[str, Any]] = []
    
    def check_api_status(self, use_cache: bool = True,
                        cache_duration_seconds: int = 30) -> Dict[str, Any]:
        """
        Check API health and rate limit status
        
        Args:
            use_cache: Use cached status if available and fresh
            cache_duration_seconds: Cache duration in seconds
            
        Returns:
            Dictionary with API status information
        """
        import time
        
        # Check cache
        if use_cache and self._cached_status and self._last_check_time:
            age = time.time() - self._last_check_time
            if age < cache_duration_seconds:
                return self._cached_status
        
        status = {
            "rate_limited": False,
            "api_healthy": True,
            "last_rate_limit": None,
            "rate_limit_count": 0,
            "errors_found": [],
            "sources_checked": [],
            "last_check": datetime.now().isoformat(),
        }
        
        # Check log files for rate limits
        log_status = self._check_log_files()
        status["sources_checked"].append("logs")
        
        if log_status.get("rate_limited"):
            status["rate_limited"] = True
            status["last_rate_limit"] = log_status.get("last_rate_limit_time")
            status["rate_limit_count"] = log_status.get("rate_limit_count", 0)
        
        if log_status.get("errors"):
            status["errors_found"].extend(log_status["errors"])
            if log_status.get("api_unhealthy"):
                status["api_healthy"] = False
        
        # Update rate limit history
        if status["rate_limited"]:
            self._rate_limit_history.append({
                "timestamp": datetime.now().isoformat(),
                "reason": log_status.get("reason"),
            })
            # Keep only last 100 entries
            if len(self._rate_limit_history) > 100:
                self._rate_limit_history = self._rate_limit_history[-100:]
        
        # Cache result
        self._cached_status = status
        self._last_check_time = time.time()
        
        return status
    
    def _check_log_files(self) -> Dict[str, Any]:
        """Check log files for API errors and rate limits"""
        result = {
            "rate_limited": False,
            "api_unhealthy": False,
            "last_rate_limit_time": None,
            "rate_limit_count": 0,
            "errors": [],
            "reason": None,
        }
        
        try:
            # Get log files
            log_dirs = self.log_discovery.discover_cursor_logs()
            if not log_dirs:
                return result
            
            rate_limit_times = []
            
            # Check recent log files
            for log_dir in log_dirs:
                log_files = list(log_dir.glob("*.log"))
                
                for log_file in log_files[:5]:  # Check up to 5 most recent logs
                    try:
                        # Read last 2000 lines
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            recent_lines = lines[-2000:] if len(lines) > 2000 else lines
                        
                        # Check for rate limit patterns
                        for i, line in enumerate(recent_lines):
                            # Check rate limit patterns
                            for pattern in self.RATE_LIMIT_PATTERNS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    result["rate_limited"] = True
                                    result["rate_limit_count"] += 1
                                    
                                    # Try to extract timestamp
                                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})', line)
                                    if timestamp_match:
                                        try:
                                            rate_limit_times.append(
                                                datetime.fromisoformat(timestamp_match.group(1).replace(' ', 'T'))
                                            )
                                        except:
                                            pass
                                    
                                    if not result["reason"]:
                                        result["reason"] = f"Rate limit detected: {pattern}"
                            
                            # Check API error patterns
                            for pattern in self.API_ERROR_PATTERNS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    result["api_unhealthy"] = True
                                    result["errors"].append({
                                        "file": str(log_file),
                                        "pattern": pattern,
                                        "line": line.strip()[:200],
                                    })
                    
                    except (PermissionError, OSError) as e:
                        logger.debug(f"Cannot read {log_file}: {e}")
                    except Exception as e:
                        logger.debug(f"Error processing {log_file}: {e}")
            
            # Get most recent rate limit time
            if rate_limit_times:
                result["last_rate_limit_time"] = max(rate_limit_times).isoformat()
        
        except Exception as e:
            logger.error(f"Log check failed: {e}")
            result["errors"].append(f"Log check error: {e}")
        
        return result
    
    def is_rate_limited(self) -> bool:
        """
        Quick check if API is rate limited
        
        Returns:
            True if rate limited, False otherwise
        """
        status = self.check_api_status()
        return status.get("rate_limited", False)
    
    def get_rate_limit_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get rate limit history
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of rate limit events
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        history = []
        for event in self._rate_limit_history:
            try:
                event_time = datetime.fromisoformat(event["timestamp"])
                if event_time >= cutoff:
                    history.append(event)
            except:
                continue
        
        return history
    
    def get_api_health(self) -> Dict[str, Any]:
        """
        Get overall API health status
        
        Returns:
            Health status dictionary
        """
        status = self.check_api_status()
        
        return {
            "healthy": status.get("api_healthy", True),
            "rate_limited": status.get("rate_limited", False),
            "last_check": status.get("last_check"),
            "recent_rate_limits": len(self.get_rate_limit_history(hours=1)),
        }

