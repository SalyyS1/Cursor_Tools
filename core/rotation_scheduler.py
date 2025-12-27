#!/usr/bin/env python3
"""
Rotation Scheduler - Hybrid rotation trigger logic

Supports multiple rotation triggers:
1. Token expired
2. Rate limited
3. Scheduled time
4. Manual trigger
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum

from core.token_monitor import TokenExpirationMonitor
from core.api_monitor import OpusAPIMonitor

logger = logging.getLogger(__name__)


class RotationTrigger(Enum):
    """Rotation trigger types"""
    TOKEN_EXPIRED = "token_expired"
    RATE_LIMITED = "rate_limited"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    NONE = "none"


class HybridRotationScheduler:
    """Hybrid rotation scheduler with multiple trigger types"""
    
    def __init__(self, 
                 token_monitor: Optional[TokenExpirationMonitor] = None,
                 api_monitor: Optional[OpusAPIMonitor] = None,
                 scheduled_interval_hours: float = 12.0):
        """
        Initialize rotation scheduler
        
        Args:
            token_monitor: Token expiration monitor instance
            api_monitor: API monitor instance
            scheduled_interval_hours: Scheduled rotation interval in hours
        """
        self.token_monitor = token_monitor or TokenExpirationMonitor()
        self.api_monitor = api_monitor or OpusAPIMonitor()
        self.scheduled_interval_hours = scheduled_interval_hours
        
        self.last_rotation_time: Optional[float] = None
        self.manual_trigger_pending: bool = False
        self.rotation_callbacks: List[Callable[[RotationTrigger], None]] = []
        
        # Configuration
        self.enable_token_check = True
        self.enable_rate_limit_check = True
        self.enable_scheduled_rotation = True
    
    def should_rotate(self) -> Tuple[bool, RotationTrigger, Optional[str]]:
        """
        Check if rotation should be triggered
        
        Returns:
            Tuple of (should_rotate: bool, trigger: RotationTrigger, reason: str)
        """
        # Check manual trigger first (highest priority)
        if self.manual_trigger_pending:
            self.manual_trigger_pending = False
            return (True, RotationTrigger.MANUAL, "Manual rotation requested")
        
        # Check token expiration
        if self.enable_token_check:
            if self.token_monitor.is_token_expired():
                reason = self.token_monitor.get_expiration_reason()
                return (True, RotationTrigger.TOKEN_EXPIRED, reason or "Token expired")
        
        # Check rate limit
        if self.enable_rate_limit_check:
            if self.api_monitor.is_rate_limited():
                return (True, RotationTrigger.RATE_LIMITED, "API rate limited")
        
        # Check scheduled rotation
        if self.enable_scheduled_rotation:
            if self._is_scheduled_time():
                return (True, RotationTrigger.SCHEDULED, 
                       f"Scheduled rotation (interval: {self.scheduled_interval_hours}h)")
        
        return (False, RotationTrigger.NONE, None)
    
    def _is_scheduled_time(self) -> bool:
        """Check if scheduled rotation time has arrived"""
        if self.last_rotation_time is None:
            return False
        
        elapsed_hours = (time.time() - self.last_rotation_time) / 3600.0
        return elapsed_hours >= self.scheduled_interval_hours
    
    def trigger_manual_rotation(self):
        """Trigger manual rotation"""
        self.manual_trigger_pending = True
        logger.info("Manual rotation triggered")
    
    def register_rotation_callback(self, callback: Callable[[RotationTrigger], None]):
        """
        Register callback for rotation events
        
        Args:
            callback: Function to call when rotation is triggered
        """
        self.rotation_callbacks.append(callback)
    
    def notify_rotation_complete(self, trigger: RotationTrigger, success: bool):
        """
        Notify scheduler that rotation completed
        
        Args:
            trigger: Trigger that caused rotation
            success: Whether rotation was successful
        """
        if success:
            self.last_rotation_time = time.time()
            logger.info(f"Rotation completed successfully (trigger: {trigger.value})")
        else:
            logger.warning(f"Rotation failed (trigger: {trigger.value})")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status
        
        Returns:
            Status dictionary
        """
        should_rotate, trigger, reason = self.should_rotate()
        
        status = {
            "should_rotate": should_rotate,
            "trigger": trigger.value if trigger != RotationTrigger.NONE else None,
            "reason": reason,
            "last_rotation": None,
            "next_scheduled_rotation": None,
            "enabled_checks": {
                "token_check": self.enable_token_check,
                "rate_limit_check": self.enable_rate_limit_check,
                "scheduled_rotation": self.enable_scheduled_rotation,
            },
        }
        
        if self.last_rotation_time:
            status["last_rotation"] = datetime.fromtimestamp(
                self.last_rotation_time
            ).isoformat()
            
            if self.enable_scheduled_rotation:
                next_rotation = self.last_rotation_time + (
                    self.scheduled_interval_hours * 3600
                )
                status["next_scheduled_rotation"] = datetime.fromtimestamp(
                    next_rotation
                ).isoformat()
        
        return status
    
    def configure(self, 
                 enable_token_check: Optional[bool] = None,
                 enable_rate_limit_check: Optional[bool] = None,
                 enable_scheduled_rotation: Optional[bool] = None,
                 scheduled_interval_hours: Optional[float] = None):
        """
        Configure scheduler settings
        
        Args:
            enable_token_check: Enable token expiration check
            enable_rate_limit_check: Enable rate limit check
            enable_scheduled_rotation: Enable scheduled rotation
            scheduled_interval_hours: Scheduled rotation interval
        """
        if enable_token_check is not None:
            self.enable_token_check = enable_token_check
        if enable_rate_limit_check is not None:
            self.enable_rate_limit_check = enable_rate_limit_check
        if enable_scheduled_rotation is not None:
            self.enable_scheduled_rotation = enable_scheduled_rotation
        if scheduled_interval_hours is not None:
            self.scheduled_interval_hours = scheduled_interval_hours
        
        logger.info(f"Scheduler configured: token_check={self.enable_token_check}, "
                   f"rate_limit_check={self.enable_rate_limit_check}, "
                   f"scheduled={self.enable_scheduled_rotation} "
                   f"({self.scheduled_interval_hours}h)")

