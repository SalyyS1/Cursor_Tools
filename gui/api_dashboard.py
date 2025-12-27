#!/usr/bin/env python3
"""
API Dashboard Widget - Real-time API health and usage display
"""

import tkinter as tk
from tkinter import ttk
import threading
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.api_monitor import OpusAPIMonitor
from utils.api_history import APIHistory

logger = logging.getLogger(__name__)


class APIDashboardWidget:
    """API health dashboard widget for GUI"""
    
    def __init__(self, parent, api_monitor: OpusAPIMonitor, api_history: APIHistory,
                 update_interval_ms: int = 30000):
        """
        Initialize API dashboard widget
        
        Args:
            parent: Parent widget
            api_monitor: API monitor instance
            api_history: API history instance
            update_interval_ms: Update interval in milliseconds (default: 30 seconds)
        """
        self.api_monitor = api_monitor
        self.api_history = api_history
        self.update_interval_ms = update_interval_ms
        self.running = False
        
        # Create main frame
        self.frame = ttk.Frame(parent, padding="10")
        
        # Create widgets
        self.create_widgets()
        
        # Start auto-update
        self.start_updates()
    
    def create_widgets(self):
        """Create dashboard widgets"""
        # Title
        title_label = ttk.Label(self.frame, text="API Health Dashboard", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Status section
        status_frame = ttk.LabelFrame(self.frame, text="Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.health_label = ttk.Label(status_frame, text="Health: Checking...", 
                                     font=("Arial", 10))
        self.health_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.rate_limit_label = ttk.Label(status_frame, text="Rate Limit: Unknown", 
                                         font=("Arial", 10))
        self.rate_limit_label.grid(row=1, column=0, sticky="w", padx=5)
        
        self.last_check_label = ttk.Label(status_frame, text="Last Check: Never", 
                                         font=("Arial", 9))
        self.last_check_label.grid(row=2, column=0, sticky="w", padx=5)
        
        # Statistics section
        stats_frame = ttk.LabelFrame(self.frame, text="Statistics (24h)", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, width=50, wrap=tk.WORD)
        self.stats_text.grid(row=0, column=0, sticky="ew")
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", 
                                       command=self.stats_text.yview)
        stats_scrollbar.grid(row=0, column=1, sticky="ns")
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        # Recent events section
        events_frame = ttk.LabelFrame(self.frame, text="Recent Events", padding="10")
        events_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.events_text = tk.Text(events_frame, height=6, width=50, wrap=tk.WORD)
        self.events_text.grid(row=0, column=0, sticky="ew")
        events_scrollbar = ttk.Scrollbar(events_frame, orient="vertical", 
                                      command=self.events_text.yview)
        events_scrollbar.grid(row=0, column=1, sticky="ns")
        self.events_text.configure(yscrollcommand=events_scrollbar.set)
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(0, weight=1)
        events_frame.columnconfigure(0, weight=1)
    
    def start_updates(self):
        """Start auto-updating dashboard"""
        self.running = True
        self.update_dashboard()
    
    def stop_updates(self):
        """Stop auto-updating dashboard"""
        self.running = False
    
    def update_dashboard(self):
        """Update dashboard with latest data"""
        if not self.running:
            return
        
        try:
            # Update status
            health = self.api_monitor.get_api_health()
            
            # Health status
            if health.get("healthy", True):
                self.health_label.config(text="Health: ✅ Healthy", foreground="green")
            else:
                self.health_label.config(text="Health: ❌ Unhealthy", foreground="red")
            
            # Rate limit status
            if health.get("rate_limited", False):
                self.rate_limit_label.config(text="Rate Limit: ⚠️ Limited", foreground="orange")
            else:
                self.rate_limit_label.config(text="Rate Limit: ✅ OK", foreground="green")
            
            # Last check
            last_check = health.get("last_check", "Never")
            if last_check != "Never":
                try:
                    dt = datetime.fromisoformat(last_check)
                    last_check = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            self.last_check_label.config(text=f"Last Check: {last_check}")
            
            # Update statistics
            stats = self.api_history.get_statistics(hours=24)
            stats_text = f"""Total Calls: {stats.get('total_calls', 0)}
Successful: {stats.get('successful_calls', 0)}
Failed: {stats.get('failed_calls', 0)}
Rate Limits: {stats.get('rate_limits', 0)}
Errors: {stats.get('errors', 0)}
Avg Response Time: {stats.get('avg_response_time_ms', 0):.1f} ms
"""
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            
            # Update recent events
            recent_limits = self.api_history.get_recent_rate_limits(hours=1)
            recent_errors = self.api_history.get_recent_errors(hours=1)
            
            events_text = ""
            if recent_limits:
                events_text += "Recent Rate Limits:\n"
                for limit in recent_limits[-5:]:  # Last 5
                    timestamp = limit.get("timestamp", "")
                    reason = limit.get("reason", "")
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        timestamp = dt.strftime("%H:%M:%S")
                    except:
                        pass
                    events_text += f"  [{timestamp}] {reason}\n"
            
            if recent_errors:
                events_text += "\nRecent Errors:\n"
                for error in recent_errors[-5:]:  # Last 5
                    timestamp = error.get("timestamp", "")
                    error_type = error.get("error_type", "")
                    message = error.get("message", "")
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        timestamp = dt.strftime("%H:%M:%S")
                    except:
                        pass
                    events_text += f"  [{timestamp}] {error_type}: {message[:50]}\n"
            
            if not events_text:
                events_text = "No recent events"
            
            self.events_text.delete(1.0, tk.END)
            self.events_text.insert(1.0, events_text)
        
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
        
        # Schedule next update
        if self.running:
            self.frame.after(self.update_interval_ms, self.update_dashboard)
    
    def refresh(self):
        """Manually refresh dashboard"""
        self.update_dashboard()

