#!/usr/bin/env python3
"""
Rotation History - Track and store rotation events

Stores rotation history, statistics, and analytics for dashboard display.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RotationHistory:
    """Track and store rotation history"""
    
    def __init__(self, history_file: Optional[Path] = None, retention_days: int = 90):
        """
        Initialize rotation history tracker
        
        Args:
            history_file: Path to history file (default: ~/.cursor_rotation/rotation_history.json)
            retention_days: Number of days to retain history (default: 90)
        """
        if history_file is None:
            history_file = Path.home() / ".cursor_rotation" / "rotation_history.json"
        
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
                    "rotations": [],
                    "statistics": {},
                }
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return {
                "rotations": [],
                "statistics": {},
            }
    
    def _clean_history(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove entries older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        cutoff_iso = cutoff.isoformat()
        
        cleaned = {
            "rotations": [],
            "statistics": data.get("statistics", {}),
        }
        
        # Clean rotations
        for rotation in data.get("rotations", []):
            if rotation.get("timestamp", "") >= cutoff_iso:
                cleaned["rotations"].append(rotation)
        
        return cleaned
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def log_rotation(self, trigger: str, success: bool, 
                    account_id: Optional[str] = None,
                    duration_seconds: Optional[float] = None,
                    metadata: Optional[Dict[str, Any]] = None):
        """
        Log a rotation event
        
        Args:
            trigger: Rotation trigger (token_expired, rate_limited, scheduled, manual)
            success: Whether rotation was successful
            account_id: Account ID used (if applicable)
            duration_seconds: Rotation duration in seconds
            metadata: Additional metadata
        """
        rotation = {
            "timestamp": datetime.now().isoformat(),
            "trigger": trigger,
            "success": success,
            "account_id": account_id,
            "duration_seconds": duration_seconds,
            "metadata": metadata or {},
        }
        
        self._history["rotations"].append(rotation)
        
        # Keep only last 10000 rotations
        if len(self._history["rotations"]) > 10000:
            self._history["rotations"] = self._history["rotations"][-10000:]
        
        self._save_history()
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get rotation statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Statistics dictionary
        """
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()
        
        stats = {
            "total_rotations": 0,
            "successful_rotations": 0,
            "failed_rotations": 0,
            "by_trigger": defaultdict(int),
            "by_account": defaultdict(int),
            "avg_duration_seconds": 0.0,
            "time_period_days": days,
        }
        
        durations = []
        
        # Analyze rotations
        for rotation in self._history.get("rotations", []):
            if rotation.get("timestamp", "") >= cutoff_iso:
                stats["total_rotations"] += 1
                
                trigger = rotation.get("trigger", "unknown")
                stats["by_trigger"][trigger] += 1
                
                account_id = rotation.get("account_id")
                if account_id:
                    stats["by_account"][account_id] += 1
                
                if rotation.get("success", False):
                    stats["successful_rotations"] += 1
                else:
                    stats["failed_rotations"] += 1
                
                if rotation.get("duration_seconds"):
                    durations.append(rotation["duration_seconds"])
        
        # Calculate average duration
        if durations:
            stats["avg_duration_seconds"] = sum(durations) / len(durations)
        
        # Convert defaultdicts to regular dicts
        stats["by_trigger"] = dict(stats["by_trigger"])
        stats["by_account"] = dict(stats["by_account"])
        
        return stats
    
    def get_recent_rotations(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent rotation events"""
        rotations = self._history.get("rotations", [])
        return rotations[-count:] if len(rotations) > count else rotations
    
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
                    writer.writerow(["Timestamp", "Trigger", "Success", "Account ID", "Duration (s)"])
                    
                    for rotation in self._history.get("rotations", []):
                        writer.writerow([
                            rotation.get("timestamp", ""),
                            rotation.get("trigger", ""),
                            rotation.get("success", False),
                            rotation.get("account_id", ""),
                            rotation.get("duration_seconds", ""),
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
            "rotations": [],
            "statistics": {},
        }
        self._save_history()

