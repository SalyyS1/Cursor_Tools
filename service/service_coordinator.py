#!/usr/bin/env python3
"""
Service Coordinator - Shared state management between service and scheduled task
"""

import json
import time
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Platform-specific imports
if sys.platform == "win32":
    try:
        import msvcrt
        MSVCRT_AVAILABLE = True
    except ImportError:
        MSVCRT_AVAILABLE = False
else:
    try:
        import fcntl
        FCNTL_AVAILABLE = True
    except ImportError:
        FCNTL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ServiceCoordinator:
    """Coordinates between Windows service and scheduled task"""
    
    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize coordinator
        
        Args:
            state_file: Path to shared state file (default: ~/.cursor_rotation/service_state.json)
        """
        if state_file is None:
            state_file = Path.home() / ".cursor_rotation" / "service_state.json"
        
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = self.state_file.with_suffix('.lock')
    
    def _acquire_lock(self, timeout: float = 5.0) -> bool:
        """Acquire file lock"""
        try:
            if sys.platform == "win32":
                # Windows: use msvcrt
                if not MSVCRT_AVAILABLE:
                    logger.warning("msvcrt not available, using simple file lock")
                    # Fallback: simple file existence check
                    if self._lock_file.exists():
                        return False
                    self._lock_handle = open(self._lock_file, 'w')
                    return True
                self._lock_handle = open(self._lock_file, 'w')
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        msvcrt.locking(self._lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
                        return True
                    except IOError:
                        time.sleep(0.1)
                return False
            else:
                # Unix: use fcntl
                if not FCNTL_AVAILABLE:
                    logger.warning("fcntl not available, using simple file lock")
                    if self._lock_file.exists():
                        return False
                    self._lock_handle = open(self._lock_file, 'w')
                    return True
                self._lock_handle = open(self._lock_file, 'w')
                fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False
    
    def _release_lock(self):
        """Release file lock"""
        try:
            if sys.platform == "win32":
                if hasattr(self, '_lock_handle') and MSVCRT_AVAILABLE:
                    try:
                        msvcrt.locking(self._lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                if hasattr(self, '_lock_handle'):
                    self._lock_handle.close()
                # Remove lock file
                if self._lock_file.exists():
                    try:
                        self._lock_file.unlink()
                    except Exception:
                        pass
            else:
                if hasattr(self, '_lock_handle') and FCNTL_AVAILABLE:
                    try:
                        fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_UN)
                    except Exception:
                        pass
                if hasattr(self, '_lock_handle'):
                    self._lock_handle.close()
                # Remove lock file
                if self._lock_file.exists():
                    try:
                        self._lock_file.unlink()
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
    
    def _read_state(self) -> Dict[str, Any]:
        """Read state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            else:
                return self._default_state()
        except Exception as e:
            logger.error(f"Failed to read state: {e}")
            return self._default_state()
    
    def _write_state(self, state: Dict[str, Any]):
        """Write state to file"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write state: {e}")
    
    def _default_state(self) -> Dict[str, Any]:
        """Get default state"""
        return {
            "service_running": False,
            "last_rotation": None,
            "rotation_in_progress": False,
            "last_check": None,
            "last_rotation_success": None,
            "rotation_count": 0,
        }
    
    def mark_service_running(self):
        """Mark service as running"""
        if not self._acquire_lock():
            logger.warning("Failed to acquire lock for mark_service_running")
            return
        
        try:
            state = self._read_state()
            state["service_running"] = True
            state["last_check"] = time.time()
            self._write_state(state)
        finally:
            self._release_lock()
    
    def mark_service_stopped(self):
        """Mark service as stopped"""
        if not self._acquire_lock():
            logger.warning("Failed to acquire lock for mark_service_stopped")
            return
        
        try:
            state = self._read_state()
            state["service_running"] = False
            self._write_state(state)
        finally:
            self._release_lock()
    
    def mark_rotation_in_progress(self):
        """Mark rotation as in progress"""
        if not self._acquire_lock():
            logger.warning("Failed to acquire lock for mark_rotation_in_progress")
            return
        
        try:
            state = self._read_state()
            state["rotation_in_progress"] = True
            self._write_state(state)
        finally:
            self._release_lock()
    
    def mark_rotation_idle(self):
        """Mark rotation as idle"""
        if not self._acquire_lock():
            logger.warning("Failed to acquire lock for mark_rotation_idle")
            return
        
        try:
            state = self._read_state()
            state["rotation_in_progress"] = False
            self._write_state(state)
        finally:
            self._release_lock()
    
    def mark_rotation_complete(self, success: bool):
        """Mark rotation as complete"""
        if not self._acquire_lock():
            logger.warning("Failed to acquire lock for mark_rotation_complete")
            return
        
        try:
            state = self._read_state()
            state["rotation_in_progress"] = False
            state["last_rotation"] = time.time()
            state["last_rotation_success"] = success
            state["rotation_count"] = state.get("rotation_count", 0) + 1
            self._write_state(state)
        finally:
            self._release_lock()
    
    def update_status(self, last_check: Optional[float] = None, rotation_in_progress: Optional[bool] = None):
        """Update service status"""
        if not self._acquire_lock():
            logger.warning("Failed to acquire lock for update_status")
            return
        
        try:
            state = self._read_state()
            if last_check is not None:
                state["last_check"] = last_check
            if rotation_in_progress is not None:
                state["rotation_in_progress"] = rotation_in_progress
            self._write_state(state)
        finally:
            self._release_lock()
    
    def is_service_running(self) -> bool:
        """Check if service is running"""
        state = self._read_state()
        return state.get("service_running", False)
    
    def is_rotation_in_progress(self) -> bool:
        """Check if rotation is in progress"""
        state = self._read_state()
        return state.get("rotation_in_progress", False)
    
    def get_last_rotation(self) -> Optional[float]:
        """Get last rotation timestamp"""
        state = self._read_state()
        return state.get("last_rotation")
    
    def get_last_check(self) -> Optional[float]:
        """Get last check timestamp"""
        state = self._read_state()
        return state.get("last_check")
    
    def get_state(self) -> Dict[str, Any]:
        """Get full state"""
        return self._read_state()
    
    def clear_state(self):
        """Clear state file (for testing)"""
        if self.state_file.exists():
            self.state_file.unlink()
        if self._lock_file.exists():
            self._lock_file.unlink()

