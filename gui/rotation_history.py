#!/usr/bin/env python3
"""
Rotation History Display - Display rotation history and analytics
"""

import tkinter as tk
from tkinter import ttk, filedialog
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from utils.rotation_history import RotationHistory

logger = logging.getLogger(__name__)


class RotationHistoryWidget:
    """Rotation history display widget"""
    
    def __init__(self, parent, rotation_history: RotationHistory, update_interval_ms: int = 60000):
        """
        Initialize rotation history widget
        
        Args:
            parent: Parent widget
            rotation_history: Rotation history instance
            update_interval_ms: Update interval in milliseconds
        """
        self.rotation_history = rotation_history
        self.update_interval_ms = update_interval_ms
        self.running = False
        
        # Create main frame
        self.frame = ttk.Frame(parent, padding="10")
        self.create_widgets()
        self.start_updates()
    
    def create_widgets(self):
        """Create history widgets"""
        # Title
        title_label = ttk.Label(self.frame, text="Rotation History", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Statistics
        stats_frame = ttk.LabelFrame(self.frame, text="Statistics (30 days)", padding="10")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, width=50, wrap=tk.WORD)
        self.stats_text.grid(row=0, column=0, sticky="ew")
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", 
                                       command=self.stats_text.yview)
        stats_scrollbar.grid(row=0, column=1, sticky="ns")
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        # Recent rotations
        recent_frame = ttk.LabelFrame(self.frame, text="Recent Rotations", padding="10")
        recent_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.recent_text = tk.Text(recent_frame, height=10, width=50, wrap=tk.WORD)
        self.recent_text.grid(row=0, column=0, sticky="ew")
        recent_scrollbar = ttk.Scrollbar(recent_frame, orient="vertical", 
                                        command=self.recent_text.yview)
        recent_scrollbar.grid(row=0, column=1, sticky="ns")
        self.recent_text.configure(yscrollcommand=recent_scrollbar.set)
        
        # Export button
        export_frame = ttk.Frame(self.frame, padding="10")
        export_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        
        export_btn = ttk.Button(export_frame, text="Export History", 
                                command=self.on_export)
        export_btn.grid(row=0, column=0, padx=5)
        
        # Configure grid
        self.frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(0, weight=1)
        recent_frame.columnconfigure(0, weight=1)
    
    def start_updates(self):
        """Start auto-updating"""
        self.running = True
        self.update_display()
    
    def stop_updates(self):
        """Stop auto-updating"""
        self.running = False
    
    def update_display(self):
        """Update history display"""
        if not self.running:
            return
        
        try:
            # Update statistics
            stats = self.rotation_history.get_statistics(days=30)
            stats_text = f"""Total Rotations: {stats.get('total_rotations', 0)}
Successful: {stats.get('successful_rotations', 0)}
Failed: {stats.get('failed_rotations', 0)}
Avg Duration: {stats.get('avg_duration_seconds', 0):.1f} seconds

By Trigger:
"""
            for trigger, count in stats.get('by_trigger', {}).items():
                stats_text += f"  {trigger}: {count}\n"
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            
            # Update recent rotations
            recent = self.rotation_history.get_recent_rotations(count=20)
            recent_text = ""
            for rotation in reversed(recent[-20:]):  # Show last 20, newest first
                timestamp = rotation.get("timestamp", "")
                trigger = rotation.get("trigger", "unknown")
                success = "✅" if rotation.get("success", False) else "❌"
                account = rotation.get("account_id", "N/A")
                duration = rotation.get("duration_seconds", 0)
                
                # Format timestamp
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
                
                recent_text += f"[{timestamp}] {success} {trigger} (Account: {account}, {duration:.1f}s)\n"
            
            if not recent_text:
                recent_text = "No rotations yet"
            
            self.recent_text.delete(1.0, tk.END)
            self.recent_text.insert(1.0, recent_text)
        
        except Exception as e:
            logger.error(f"Failed to update history display: {e}")
        
        # Schedule next update
        if self.running:
            self.frame.after(self.update_interval_ms, self.update_display)
    
    def on_export(self):
        """Export history"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            format = "csv" if file_path.endswith(".csv") else "json"
            result = self.rotation_history.export_history(Path(file_path), format)
            if result:
                logger.info(f"History exported to {file_path}")
            else:
                logger.error(f"Failed to export history to {file_path}")
    
    def refresh(self):
        """Manually refresh"""
        self.update_display()

