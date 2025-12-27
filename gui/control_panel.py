#!/usr/bin/env python3
"""
Automation Control Panel - Control rotation automation
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, Callable

from core.rotation_scheduler import HybridRotationScheduler

logger = logging.getLogger(__name__)


class ControlPanelWidget:
    """Automation control panel widget"""
    
    def __init__(self, parent, scheduler: HybridRotationScheduler,
                 on_settings_change: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize control panel widget
        
        Args:
            parent: Parent widget
            scheduler: Rotation scheduler instance
            on_settings_change: Callback for settings changes
        """
        self.scheduler = scheduler
        self.on_settings_change = on_settings_change
        
        # Create main frame
        self.frame = ttk.Frame(parent, padding="10")
        self.create_widgets()
        self.load_settings()
    
    def create_widgets(self):
        """Create control panel widgets"""
        # Title
        title_label = ttk.Label(self.frame, text="Automation Control", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Automation toggles
        toggles_frame = ttk.LabelFrame(self.frame, text="Automation Settings", padding="10")
        toggles_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.token_check_var = tk.BooleanVar(value=True)
        token_check = ttk.Checkbutton(toggles_frame, text="Enable Token Check", 
                                      variable=self.token_check_var,
                                      command=self.on_toggle_change)
        token_check.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.rate_limit_check_var = tk.BooleanVar(value=True)
        rate_limit_check = ttk.Checkbutton(toggles_frame, text="Enable Rate Limit Check", 
                                          variable=self.rate_limit_check_var,
                                          command=self.on_toggle_change)
        rate_limit_check.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        self.scheduled_rotation_var = tk.BooleanVar(value=True)
        scheduled_rotation = ttk.Checkbutton(toggles_frame, text="Enable Scheduled Rotation", 
                                             variable=self.scheduled_rotation_var,
                                             command=self.on_toggle_change)
        scheduled_rotation.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        # Schedule configuration
        schedule_frame = ttk.LabelFrame(self.frame, text="Schedule", padding="10")
        schedule_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Label(schedule_frame, text="Interval (hours):").grid(row=0, column=0, sticky="w", padx=5)
        self.interval_var = tk.DoubleVar(value=12.0)
        interval_spin = ttk.Spinbox(schedule_frame, from_=1.0, to=168.0, increment=1.0,
                                   textvariable=self.interval_var, width=10,
                                   command=self.on_interval_change)
        interval_spin.grid(row=0, column=1, sticky="w", padx=5)
        
        # Manual rotation button
        manual_frame = ttk.Frame(self.frame, padding="10")
        manual_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.manual_rotate_btn = ttk.Button(manual_frame, text="Manual Rotation", 
                                            command=self.on_manual_rotation)
        self.manual_rotate_btn.grid(row=0, column=0, padx=5)
        
        # Configure grid
        self.frame.columnconfigure(0, weight=1)
        toggles_frame.columnconfigure(0, weight=1)
        schedule_frame.columnconfigure(0, weight=1)
    
    def load_settings(self):
        """Load current settings"""
        status = self.scheduler.get_status()
        enabled = status.get("enabled_checks", {})
        
        self.token_check_var.set(enabled.get("token_check", True))
        self.rate_limit_check_var.set(enabled.get("rate_limit_check", True))
        self.scheduled_rotation_var.set(enabled.get("scheduled_rotation", True))
        
        # Get interval from scheduler
        self.interval_var.set(self.scheduler.scheduled_interval_hours)
    
    def on_toggle_change(self):
        """Handle toggle change"""
        self.scheduler.enable_token_check = self.token_check_var.get()
        self.scheduler.enable_rate_limit_check = self.rate_limit_check_var.get()
        self.scheduler.enable_scheduled_rotation = self.scheduled_rotation_var.get()
        
        if self.on_settings_change:
            self.on_settings_change(self.get_settings())
    
    def on_interval_change(self):
        """Handle interval change"""
        self.scheduler.scheduled_interval_hours = self.interval_var.get()
        
        if self.on_settings_change:
            self.on_settings_change(self.get_settings())
    
    def on_manual_rotation(self):
        """Handle manual rotation"""
        self.scheduler.trigger_manual_rotation()
        logger.info("Manual rotation triggered from control panel")
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings"""
        return {
            "token_check": self.token_check_var.get(),
            "rate_limit_check": self.rate_limit_check_var.get(),
            "scheduled_rotation": self.scheduled_rotation_var.get(),
            "interval_hours": self.interval_var.get(),
        }

