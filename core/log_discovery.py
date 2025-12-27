#!/usr/bin/env python3
"""
Log Discovery - Multi-path Cursor log file discovery

Discovers Cursor log file locations using multiple strategies:
1. Standard VSCode locations
2. Process-based discovery
3. Registry-based discovery
4. File system scan fallback
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Set
import time

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available, process-based discovery disabled")

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False
    if sys.platform == "win32":
        logging.warning("winreg not available on Windows")

logger = logging.getLogger(__name__)


class CursorLogDiscovery:
    """Discovers Cursor log file locations using multiple strategies"""
    
    def __init__(self):
        """Initialize log discovery"""
        self._discovered_paths: Optional[List[Path]] = None
        self._discovery_time: Optional[float] = None
        self._cache_file = Path.home() / ".cursor_rotation" / "log_paths_cache.json"
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def discover_cursor_logs(self, use_cache: bool = True, max_age_seconds: int = 3600) -> List[Path]:
        """
        Discover Cursor log locations using multiple strategies
        
        Args:
            use_cache: Use cached paths if available and fresh
            max_age_seconds: Maximum age of cache in seconds
            
        Returns:
            List of discovered log directory paths
        """
        start_time = time.time()
        
        # Check cache first
        if use_cache and self._load_cache(max_age_seconds):
            logger.info(f"Using cached log paths (discovered in {self._discovery_time:.2f}s)")
            return self._discovered_paths or []
        
        # Multi-strategy discovery
        log_paths: Set[Path] = set()
        
        # Strategy 1: Standard VSCode locations
        standard_paths = self._check_standard_paths()
        log_paths.update(standard_paths)
        logger.debug(f"Standard paths found: {len(standard_paths)}")
        
        # Strategy 2: Process-based discovery
        if PSUTIL_AVAILABLE:
            process_paths = self._check_process_paths()
            log_paths.update(process_paths)
            logger.debug(f"Process paths found: {len(process_paths)}")
        
        # Strategy 3: Registry-based discovery (Windows only)
        if sys.platform == "win32" and WINREG_AVAILABLE:
            registry_paths = self._check_registry_paths()
            log_paths.update(registry_paths)
            logger.debug(f"Registry paths found: {len(registry_paths)}")
        
        # Strategy 4: File system scan fallback
        if not log_paths:
            scan_paths = self._scan_for_log_files()
            log_paths.update(scan_paths)
            logger.debug(f"Scan paths found: {len(scan_paths)}")
        
        # Validate and filter paths
        validated_paths = self._validate_log_paths(list(log_paths))
        
        self._discovered_paths = validated_paths
        self._discovery_time = time.time() - start_time
        
        # Cache results
        if validated_paths:
            self._save_cache()
        
        logger.info(f"Discovered {len(validated_paths)} log paths in {self._discovery_time:.2f}s")
        return validated_paths
    
    def _check_standard_paths(self) -> List[Path]:
        """Check standard VSCode/Cursor log locations"""
        paths = []
        
        # Windows standard locations
        if sys.platform == "win32":
            appdata = os.getenv("APPDATA")
            localappdata = os.getenv("LOCALAPPDATA")
            home = Path.home()
            
            standard_locations = [
                Path(appdata) / "Cursor" / "logs" if appdata else None,
                Path(localappdata) / "Cursor" / "logs" if localappdata else None,
                home / "AppData" / "Roaming" / "Cursor" / "logs",
                home / "AppData" / "Local" / "Cursor" / "logs",
                Path(appdata) / "Cursor" / "User" / "logs" if appdata else None,
            ]
            
            for location in standard_locations:
                if location and location.exists() and location.is_dir():
                    paths.append(location)
        
        return paths
    
    def _check_process_paths(self) -> List[Path]:
        """Discover logs from running Cursor processes"""
        paths = []
        
        if not PSUTIL_AVAILABLE:
            return paths
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cwd']):
                try:
                    proc_info = proc.info
                    name = proc_info.get('name', '').lower()
                    
                    # Check if it's Cursor process
                    if 'cursor' in name and name.endswith('.exe'):
                        exe_path = proc_info.get('exe')
                        cwd = proc_info.get('cwd')
                        
                        # Try to find logs relative to executable
                        if exe_path:
                            exe_dir = Path(exe_path).parent
                            # Check common log locations relative to exe
                            log_candidates = [
                                exe_dir / "logs",
                                exe_dir.parent / "logs",
                                Path(os.getenv("APPDATA", "")) / "Cursor" / "logs",
                            ]
                            for candidate in log_candidates:
                                if candidate and candidate.exists() and candidate.is_dir():
                                    paths.append(candidate)
                        
                        # Try working directory
                        if cwd:
                            cwd_path = Path(cwd)
                            log_dir = cwd_path / "logs"
                            if log_dir.exists() and log_dir.is_dir():
                                paths.append(log_dir)
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        
        except Exception as e:
            logger.warning(f"Process-based discovery failed: {e}")
        
        return paths
    
    def _check_registry_paths(self) -> List[Path]:
        """Discover logs from Windows registry"""
        paths = []
        
        if not WINREG_AVAILABLE or sys.platform != "win32":
            return paths
        
        registry_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Cursor"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Cursor"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Cursor"),
        ]
        
        for hkey, subkey in registry_keys:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    # Try to read installation path
                    try:
                        install_path = winreg.QueryValueEx(key, "InstallLocation")[0]
                        if install_path:
                            log_dir = Path(install_path) / "logs"
                            if log_dir.exists() and log_dir.is_dir():
                                paths.append(log_dir)
                    except FileNotFoundError:
                        pass
                    
                    # Try InstallPath
                    try:
                        install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                        if install_path:
                            log_dir = Path(install_path) / "logs"
                            if log_dir.exists() and log_dir.is_dir():
                                paths.append(log_dir)
                    except FileNotFoundError:
                        pass
            
            except (FileNotFoundError, OSError, PermissionError):
                continue
        
        return paths
    
    def _scan_for_log_files(self) -> List[Path]:
        """Fallback: Scan common locations for log files"""
        paths = []
        
        if sys.platform != "win32":
            return paths
        
        scan_locations = [
            Path(os.getenv("APPDATA", "")) / "Cursor",
            Path(os.getenv("LOCALAPPDATA", "")) / "Cursor",
            Path.home() / "AppData" / "Roaming" / "Cursor",
            Path.home() / "AppData" / "Local" / "Cursor",
        ]
        
        for base_location in scan_locations:
            if not base_location.exists():
                continue
            
            try:
                # Look for logs directory
                for item in base_location.rglob("logs"):
                    if item.is_dir():
                        # Check if it contains log files
                        log_files = list(item.glob("*.log"))
                        if log_files:
                            paths.append(item)
                            break  # Found one, move to next location
            except (PermissionError, OSError) as e:
                logger.debug(f"Scan failed for {base_location}: {e}")
                continue
        
        return paths
    
    def _validate_log_paths(self, paths: List[Path]) -> List[Path]:
        """Validate and filter log paths"""
        validated = []
        seen = set()
        
        for path in paths:
            try:
                # Convert to absolute path
                abs_path = path.resolve()
                
                # Check if already seen (normalize paths)
                path_str = str(abs_path).lower()
                if path_str in seen:
                    continue
                seen.add(path_str)
                
                # Validate path exists and is directory
                if not abs_path.exists() or not abs_path.is_dir():
                    continue
                
                # Check if contains log files
                log_files = list(abs_path.glob("*.log"))
                if not log_files:
                    # Might be valid even without .log files (new installation)
                    logger.debug(f"Log directory has no .log files yet: {abs_path}")
                
                validated.append(abs_path)
            
            except (OSError, ValueError) as e:
                logger.debug(f"Invalid log path {path}: {e}")
                continue
        
        return validated
    
    def _load_cache(self, max_age_seconds: int) -> bool:
        """Load cached log paths if available and fresh"""
        if not self._cache_file.exists():
            return False
        
        try:
            import json
            import time
            
            cache_data = json.loads(self._cache_file.read_text(encoding='utf-8'))
            
            # Check cache age
            cache_time = cache_data.get('timestamp', 0)
            age = time.time() - cache_time
            if age > max_age_seconds:
                return False
            
            # Load paths
            paths = [Path(p) for p in cache_data.get('paths', [])]
            
            # Validate cached paths still exist
            valid_paths = [p for p in paths if p.exists() and p.is_dir()]
            
            if valid_paths:
                self._discovered_paths = valid_paths
                self._discovery_time = cache_data.get('discovery_time', 0)
                return True
        
        except Exception as e:
            logger.debug(f"Cache load failed: {e}")
        
        return False
    
    def _save_cache(self):
        """Save discovered paths to cache"""
        if not self._discovered_paths:
            return
        
        try:
            import json
            import time
            
            cache_data = {
                'timestamp': time.time(),
                'paths': [str(p) for p in self._discovered_paths],
                'discovery_time': self._discovery_time or 0,
            }
            
            self._cache_file.write_text(
                json.dumps(cache_data, indent=2),
                encoding='utf-8'
            )
        
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    def get_log_files(self, log_dir: Optional[Path] = None) -> List[Path]:
        """
        Get all log files from discovered directories or specific directory
        
        Args:
            log_dir: Specific log directory (optional)
            
        Returns:
            List of log file paths
        """
        if log_dir:
            directories = [log_dir]
        else:
            directories = self.discover_cursor_logs()
        
        log_files = []
        for directory in directories:
            try:
                files = list(directory.glob("*.log"))
                log_files.extend(files)
            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot read log directory {directory}: {e}")
        
        return log_files
    
    def clear_cache(self):
        """Clear cached log paths"""
        if self._cache_file.exists():
            try:
                self._cache_file.unlink()
            except Exception as e:
                logger.warning(f"Cache clear failed: {e}")
        
        self._discovered_paths = None
        self._discovery_time = None

