#!/usr/bin/env python3
"""
Trial Status Dashboard - Real-time trial status display
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
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
        self.token_status_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.token_count_label = ttk.Label(token_frame, text="Token Count: Checking...", 
                                          font=("Arial", 9))
        self.token_count_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        self.expiration_label = ttk.Label(token_frame, text="Expiration: Checking...", 
                                         font=("Arial", 9))
        self.expiration_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        self.days_remaining_label = ttk.Label(token_frame, text="Days Remaining: Checking...", 
                                              font=("Arial", 9))
        self.days_remaining_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        
        # Account info
        account_frame = ttk.LabelFrame(self.frame, text="Account Information", padding="10")
        account_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.account_email_label = ttk.Label(account_frame, text="Email: Checking...", 
                                            font=("Arial", 9))
        self.account_email_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.account_plan_label = ttk.Label(account_frame, text="Plan: Checking...", 
                                           font=("Arial", 9))
        self.account_plan_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        self.account_subscription_label = ttk.Label(account_frame, text="Subscription: Checking...", 
                                                    font=("Arial", 9))
        self.account_subscription_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        # Debug button (optional - can be removed in production)
        debug_btn = ttk.Button(account_frame, text="Show Debug Info", 
                              command=self.show_debug_info)
        debug_btn.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        
        account_frame.columnconfigure(0, weight=1)
        
        # API status
        api_frame = ttk.LabelFrame(self.frame, text="API Status", padding="10")
        api_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.api_status_label = ttk.Label(api_frame, text="Status: Checking...", 
                                          font=("Arial", 10))
        self.api_status_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.rate_limit_label = ttk.Label(api_frame, text="Rate Limit: Unknown", 
                                         font=("Arial", 10))
        self.rate_limit_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
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
            # Get token status
            token_status = self.token_monitor.check_token_status()
            token_expired = token_status.get("expired", False)
            
            # Update token status
            if token_expired:
                self.token_status_label.config(text="Status: ⚠️ Token Expired", foreground="orange")
            else:
                self.token_status_label.config(text="Status: ✅ Token Valid", foreground="green")
            
            # Get detailed token info
            token_info = self.token_monitor.get_token_info()
            
            # Update remaining tokens (this is what user wants to see)
            remaining_tokens = token_info.get("remaining_tokens")
            token_quota = token_info.get("token_quota")
            token_usage = token_info.get("token_usage")
            
            if remaining_tokens is not None:
                # Show remaining tokens with color coding
                if remaining_tokens > 1000:
                    color = "green"
                elif remaining_tokens > 100:
                    color = "orange"
                else:
                    color = "red"
                
                if token_quota is not None:
                    # Show remaining / total
                    self.token_count_label.config(
                        text=f"Remaining Tokens: {remaining_tokens:,} / {token_quota:,}", 
                        foreground=color
                    )
                else:
                    # Show only remaining
                    self.token_count_label.config(
                        text=f"Remaining Tokens: {remaining_tokens:,}", 
                        foreground=color
                    )
            elif token_quota is not None and token_usage is not None:
                # Calculate from quota - usage
                calculated = max(0, token_quota - token_usage)
                self.token_count_label.config(
                    text=f"Remaining Tokens: {calculated:,} / {token_quota:,} (calculated)", 
                    foreground="orange"
                )
            else:
                # Fallback: show token keys count (for debugging)
                token_count = token_info.get("token_count", 0)
                if token_count > 0:
                    self.token_count_label.config(
                        text=f"Token Keys Found: {token_count} (remaining tokens not detected)", 
                        foreground="orange"
                    )
                else:
                    self.token_count_label.config(
                        text="Remaining Tokens: Not detected (checking storage.json...)",
                        foreground="gray"
                    )
            
            # Update expiration info
            expiration_date = token_info.get("expiration_date")
            days_remaining = token_info.get("days_remaining")
            trial_active = token_info.get("trial_active", False)
            
            if expiration_date:
                exp_str = expiration_date.strftime("%Y-%m-%d %H:%M:%S")
                self.expiration_label.config(text=f"Expiration: {exp_str}")
                
                if days_remaining is not None:
                    if days_remaining > 0:
                        self.days_remaining_label.config(
                            text=f"Days Remaining: {days_remaining} days", 
                            foreground="green"
                        )
                    elif days_remaining == 0:
                        self.days_remaining_label.config(
                            text="Days Remaining: Expired today", 
                            foreground="orange"
                        )
                    else:
                        self.days_remaining_label.config(
                            text=f"Days Remaining: Expired ({abs(days_remaining)} days ago)", 
                            foreground="red"
                        )
                else:
                    self.days_remaining_label.config(text="Days Remaining: Unknown")
            else:
                if trial_active:
                    self.expiration_label.config(text="Expiration: Trial Active (no expiration date)")
                    if days_remaining is not None:
                        self.days_remaining_label.config(
                            text=f"Days Remaining: {days_remaining} days", 
                            foreground="green"
                        )
                else:
                    self.expiration_label.config(text="Expiration: Not found")
                    self.days_remaining_label.config(text="Days Remaining: N/A")
            
            # Update account information
            account_email = token_info.get("account_email")
            account_user = token_info.get("account_user")
            plan_type = token_info.get("plan_type")
            subscription_type = token_info.get("subscription_type")
            
            if account_email:
                self.account_email_label.config(text=f"Email: {account_email}", foreground="blue")
            elif account_user:
                self.account_email_label.config(text=f"User: {account_user}", foreground="blue")
            else:
                self.account_email_label.config(text="Email: Not found", foreground="gray")
            
            if plan_type:
                self.account_plan_label.config(text=f"Plan: {plan_type}", foreground="blue")
            else:
                # Try to infer from other info
                account_info = token_info.get("account_info", {})
                inferred_plan = account_info.get("plan")
                if inferred_plan:
                    self.account_plan_label.config(text=f"Plan: {inferred_plan}", foreground="blue")
                else:
                    self.account_plan_label.config(text="Plan: Unknown (checking...)", foreground="gray")
            
            if subscription_type:
                self.account_subscription_label.config(text=f"Subscription: {subscription_type}", foreground="blue")
            elif trial_active:
                self.account_subscription_label.config(text="Subscription: Trial", foreground="orange")
            else:
                # Try to infer from other info
                account_info = token_info.get("account_info", {})
                inferred_sub = account_info.get("subscription")
                if inferred_sub:
                    self.account_subscription_label.config(text=f"Subscription: {inferred_sub}", foreground="blue")
                else:
                    self.account_subscription_label.config(text="Subscription: Unknown (checking...)", foreground="gray")
            
            # Update API status
            api_status = self.api_monitor.check_api_status()
            api_healthy = api_status.get("api_healthy", True)
            rate_limited = api_status.get("rate_limited", False)
            
            if api_healthy:
                self.api_status_label.config(text="Status: ✅ Healthy", foreground="green")
            else:
                self.api_status_label.config(text="Status: ❌ Unhealthy", foreground="red")
            
            if rate_limited:
                self.rate_limit_label.config(text="Rate Limit: ⚠️ Limited", foreground="orange")
            else:
                self.rate_limit_label.config(text="Rate Limit: ✅ OK", foreground="green")
        
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}", exc_info=True)
            # Show error in UI
            self.token_status_label.config(text=f"Status: ❌ Error - {str(e)[:50]}", foreground="red")
        
        # Schedule next update
        if self.running:
            self.frame.after(self.update_interval_ms, self.update_dashboard)
    
    def refresh(self):
        """Manually refresh"""
        self.update_dashboard()
    
    def show_debug_info(self):
        """Show debug information about detected tokens and account"""
        try:
            token_info = self.token_monitor.get_token_info()
            
            debug_text = "=== Debug Information ===\n\n"
            debug_text += f"Token Keys Found: {token_info.get('token_count', 0)}\n"
            debug_text += f"Token Keys: {list(token_info.get('tokens', {}).keys())}\n\n"
            
            remaining_tokens = token_info.get('remaining_tokens')
            token_quota = token_info.get('token_quota')
            token_usage = token_info.get('token_usage')
            
            debug_text += f"=== Token Quota Information ===\n"
            debug_text += f"Remaining Tokens: {remaining_tokens if remaining_tokens is not None else 'Not found'}\n"
            debug_text += f"Token Quota: {token_quota if token_quota is not None else 'Not found'}\n"
            debug_text += f"Token Usage: {token_usage if token_usage is not None else 'Not found'}\n\n"
            
            debug_text += f"=== Account Information ===\n"
            debug_text += f"Account Email: {token_info.get('account_email') or 'Not found'}\n"
            debug_text += f"Account User: {token_info.get('account_user') or 'Not found'}\n"
            debug_text += f"Plan Type: {token_info.get('plan_type') or 'Not found'}\n"
            debug_text += f"Subscription Type: {token_info.get('subscription_type') or 'Not found'}\n\n"
            
            debug_text += f"=== Trial Information ===\n"
            debug_text += f"Expiration Date: {token_info.get('expiration_date') or 'Not found'}\n"
            debug_text += f"Days Remaining: {token_info.get('days_remaining') or 'N/A'}\n"
            debug_text += f"Trial Active: {token_info.get('trial_active', False)}\n\n"
            
            debug_text += f"=== Full Account Info ===\n"
            debug_text += f"{token_info.get('account_info', {})}\n"
            
            # Show in a new window
            debug_window = tk.Toplevel(self.frame.winfo_toplevel())
            debug_window.title("Debug Information")
            debug_window.geometry("600x400")
            
            debug_text_widget = scrolledtext.ScrolledText(debug_window, wrap=tk.WORD, width=70, height=20)
            debug_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            debug_text_widget.insert(tk.END, debug_text)
            debug_text_widget.config(state=tk.DISABLED)
            
            ttk.Button(debug_window, text="Close", command=debug_window.destroy).pack(pady=5)
        
        except Exception as e:
            messagebox.showerror("Debug Error", f"Failed to show debug info: {e}")

