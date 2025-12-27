#!/usr/bin/env python3
"""
Trial Status Dashboard - Real-time trial status display
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.token_monitor import TokenExpirationMonitor
from core.api_monitor import OpusAPIMonitor

logger = logging.getLogger(__name__)


class TrialDashboardWidget:
    """Trial status dashboard widget"""
    
    def __init__(self, parent, token_monitor: TokenExpirationMonitor, 
                 api_monitor: OpusAPIMonitor, update_interval_ms: int = 30000):
        """
        Initialize trial dashboard widget
        
        Args:
            parent: Parent widget
            token_monitor: Token monitor instance
            api_monitor: API monitor instance
            update_interval_ms: Update interval in milliseconds
        """
        self.token_monitor = token_monitor
        self.api_monitor = api_monitor
        self.update_interval_ms = update_interval_ms
        self.running = False
        
        # Create main frame
        self.frame = ttk.Frame(parent, padding="10")
        self.create_widgets()
        self.start_updates()
    
    def create_widgets(self):
        """Create dashboard widgets"""
        # Title
        title_label = ttk.Label(self.frame, text="Trial Status Dashboard", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Token status
        token_frame = ttk.LabelFrame(self.frame, text="Token Status", padding="10")
        token_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.token_status_label = ttk.Label(token_frame, text="Status: Checking...", 
                                           font=("Arial", 10))
        self.token_status_label.grid(row=0, column=0, sticky="w", padx=5)
        
        # API status
        api_frame = ttk.LabelFrame(self.frame, text="API Status", padding="10")
        api_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.api_status_label = ttk.Label(api_frame, text="Status: Checking...", 
                                          font=("Arial", 10))
        self.api_status_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.rate_limit_label = ttk.Label(api_frame, text="Rate Limit: Unknown", 
                                         font=("Arial", 10))
        self.rate_limit_label.grid(row=1, column=0, sticky="w", padx=5)
        
        # Configure grid
        self.frame.columnconfigure(0, weight=1)
        token_frame.columnconfigure(0, weight=1)
        api_frame.columnconfigure(0, weight=1)
    
    def start_updates(self):
        """Start auto-updating"""
        self.running = True
        self.update_dashboard()
    
    def stop_updates(self):
        """Stop auto-updating"""
        self.running = False
    
    def update_dashboard(self):
        """Update dashboard"""
        if not self.running:
            return
        
        try:
            # Update token status
            token_expired = self.token_monitor.is_token_expired()
            if token_expired:
                self.token_status_label.config(text="Status: ⚠️ Token Expired", foreground="orange")
            else:
                self.token_status_label.config(text="Status: ✅ Token Valid", foreground="green")
            
            # Update API status
            api_health = self.api_monitor.get_api_health()
            if api_health.get("healthy", True):
                self.api_status_label.config(text="Status: ✅ Healthy", foreground="green")
            else:
                self.api_status_label.config(text="Status: ❌ Unhealthy", foreground="red")
            
            if api_health.get("rate_limited", False):
                self.rate_limit_label.config(text="Rate Limit: ⚠️ Limited", foreground="orange")
            else:
                self.rate_limit_label.config(text="Rate Limit: ✅ OK", foreground="green")
        
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
        
        # Schedule next update
        if self.running:
            self.frame.after(self.update_interval_ms, self.update_dashboard)
    
    def refresh(self):
        """Manually refresh"""
        self.update_dashboard()

