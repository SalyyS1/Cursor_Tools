#!/usr/bin/env python3
"""
VSCode Handler - Module Xử Lý VSCode/Cursor

Xử lý device ID, workspace storage và dọn dẹp database cho các trình chỉnh sửa VSCode
Tập trung tối ưu cho Cursor IDE
"""

import json
import logging
import sqlite3
import shutil
import stat
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid
import hashlib
import secrets

from config.settings import VSCODE_CONFIG
from utils.id_generator import IDGenerator
from utils.file_locker import FileLockManager

logger = logging.getLogger(__name__)


class VSCodeHandler:
    """Bộ xử lý các trình chỉnh sửa VSCode"""
    
    def __init__(self, path_manager, backup_manager):
        """
        Khởi tạo bộ xử lý VSCode
        
        Args:
            path_manager: Instance quản lý đường dẫn
            backup_manager: Instance quản lý backup
        """
        self.path_manager = path_manager
        self.backup_manager = backup_manager
        self.id_generator = IDGenerator()
        self.file_locker = FileLockManager()
        
    def process_vscode_installations(self, create_backups: bool = True, 
                                   lock_files: bool = True,
                                   clean_workspace: bool = False,
                                   clean_cache: bool = False) -> Dict[str, Any]:
        """
        Xử lý tất cả cài đặt VSCode
        
        Args:
            create_backups: Có tạo backup không
            lock_files: Có khóa file không
            clean_workspace: Có dọn dẹp workspace không
            clean_cache: Có dọn dẹp cache không
            
        Returns:
            Dictionary kết quả xử lý
        """
        logger.info("Starting VSCode processing")
        
        results = {
            "success": False,
            "vscode_found": False,
            "variants_found": [],
            "total_directories": 0,
            "directories_processed": 0,
            "directories_failed": 0,
            "files_processed": [],
            "files_failed": [],
            "backups_created": [],
            "old_ids": {},
            "new_ids": {},
            "workspace_cleaned": 0,
            "cache_cleaned": 0,
            "errors": []
        }
        
        try:
            # Lấy các thư mục VSCode
            vscode_dirs = self.path_manager.get_vscode_directories()
            if not vscode_dirs:
                results["errors"].append("No VSCode installations found")
                return results
            
            results["vscode_found"] = True
            results["total_directories"] = len(vscode_dirs)
            
            # Xử lý từng thư mục VSCode
            for vscode_dir in vscode_dirs:
                try:
                    # Lấy tên biến thể
                    variant_name = self.path_manager.get_vscode_variant_name(vscode_dir)
                    if variant_name not in results["variants_found"]:
                        results["variants_found"].append(variant_name)
                    
                    # Xử lý file device ID
                    storage_result = self._process_storage_files(
                        vscode_dir, create_backups, lock_files
                    )
                    
                    if storage_result["success"]:
                        results["directories_processed"] += 1
                        results["files_processed"].extend(storage_result["files_processed"])
                        results["backups_created"].extend(storage_result["backups_created"])
                        results["old_ids"].update(storage_result["old_ids"])
                        results["new_ids"].update(storage_result["new_ids"])
                    else:
                        results["directories_failed"] += 1
                        results["files_failed"].extend(storage_result["files_failed"])
                        results["errors"].extend(storage_result["errors"])
                    
                    # Dọn dẹp workspace (nếu cần)
                    if clean_workspace:
                        workspace_result = self._clean_workspace_storage(vscode_dir, create_backups)
                        results["workspace_cleaned"] += workspace_result["cleaned_count"]
                    
                    # Dọn dẹp cache (nếu cần)
                    if clean_cache:
                        cache_result = self._clean_cache_directories(vscode_dir.parent, create_backups)
                        results["cache_cleaned"] += cache_result["cleaned_count"]
                        
                except Exception as e:
                    error_msg = f"Error processing {vscode_dir}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    results["directories_failed"] += 1
            
            # Đánh giá thành công tổng thể
            if results["directories_processed"] > 0:
                results["success"] = True
                logger.info(f"Successfully processed {results['directories_processed']} VSCode directories")
            
        except Exception as e:
            error_msg = f"VSCode processing failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _process_storage_files(self, vscode_dir: Path, create_backups: bool, 
                              lock_files: bool) -> Dict[str, Any]:
        """
        Xử lý các file lưu trữ (storage.json và state.vscdb)
        
        Args:
            vscode_dir: Đường dẫn thư mục VSCode
            create_backups: Có tạo backup không
            lock_files: Có khóa file không
            
        Returns:
            Dictionary kết quả xử lý
        """
        result = {
            "success": False,
            "files_processed": [],
            "files_failed": [],
            "backups_created": [],
            "old_ids": {},
            "new_ids": {},
            "errors": []
        }
        
        try:
            # Xử lý storage.json
            storage_file = vscode_dir / "storage.json"
            if storage_file.exists():
                storage_result = self._process_storage_json(storage_file, create_backups, lock_files)
                if storage_result["success"]:
                    result["files_processed"].append(str(storage_file))
                    result["old_ids"].update(storage_result["old_ids"])
                    result["new_ids"].update(storage_result["new_ids"])
                    if storage_result["backup_path"]:
                        result["backups_created"].append(storage_result["backup_path"])
                else:
                    result["files_failed"].append(str(storage_file))
                    result["errors"].extend(storage_result["errors"])
            
            # Xử lý state.vscdb
            db_file = vscode_dir / "state.vscdb"
            if db_file.exists():
                db_result = self._process_state_database(db_file, create_backups, lock_files)
                if db_result["success"]:
                    result["files_processed"].append(str(db_file))
                    result["old_ids"].update(db_result["old_ids"])
                    result["new_ids"].update(db_result["new_ids"])
                    if db_result["backup_path"]:
                        result["backups_created"].append(db_result["backup_path"])
                else:
                    result["files_failed"].append(str(db_file))
                    result["errors"].extend(db_result["errors"])
            
            # Đánh giá thành công
            if result["files_processed"]:
                result["success"] = True
                
        except Exception as e:
            error_msg = f"Storage processing failed: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    def _process_storage_json(self, storage_file: Path, create_backups: bool, 
                             lock_files: bool) -> Dict[str, Any]:
        """
        Xử lý file storage.json
        
        Args:
            storage_file: Đường dẫn file storage.json
            create_backups: Có tạo backup không
            lock_files: Có khóa file không
            
        Returns:
            Dictionary kết quả xử lý
        """
        result = {
            "success": False,
            "backup_path": None,
            "old_ids": {},
            "new_ids": {},
            "errors": []
        }
        
        try:
            # Tạo backup
            if create_backups:
                backup_path = self.backup_manager.create_file_backup(storage_file)
                if backup_path:
                    result["backup_path"] = str(backup_path)
                    logger.info(f"Created backup: {backup_path}")
            
            # Đọc dữ liệu hiện có
            with open(storage_file, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            
            # Xử lý device ID
            modified = False
            for key in VSCODE_CONFIG["telemetry_keys"]:
                if key in data:
                    old_value = data[key]
                    new_value = self.id_generator.generate_device_id()
                    data[key] = new_value
                    result["old_ids"][key] = old_value
                    result["new_ids"][key] = new_value
                    modified = True
                    logger.info(f"Updated {key}: {old_value} -> {new_value}")
            
            # Ghi dữ liệu đã sửa đổi
            if modified:
                # Xóa thuộc tính chỉ đọc
                if storage_file.exists():
                    storage_file.chmod(stat.S_IWRITE | stat.S_IREAD)
                
                with open(storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Khóa file (nếu cần)
                if lock_files:
                    storage_file.chmod(stat.S_IREAD)
                    logger.info(f"Locked file: {storage_file}")
                
                result["success"] = True
                logger.info(f"Successfully processed storage.json: {storage_file}")
            else:
                logger.info(f"No telemetry keys found in {storage_file}")
                result["success"] = True
                
        except Exception as e:
            error_msg = f"Failed to process storage.json: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result

    def _process_state_database(self, db_file: Path, create_backups: bool,
                               lock_files: bool) -> Dict[str, Any]:
        """
        Xử lý file database state.vscdb

        Args:
            db_file: Đường dẫn file database
            create_backups: Có tạo backup không
            lock_files: Có khóa file không

        Returns:
            Dictionary kết quả xử lý
        """
        result = {
            "success": False,
            "backup_path": None,
            "old_ids": {},
            "new_ids": {},
            "errors": []
        }

        try:
            # Tạo backup
            if create_backups:
                backup_path = self.backup_manager.create_file_backup(db_file)
                if backup_path:
                    result["backup_path"] = str(backup_path)
                    logger.info(f"Created backup: {backup_path}")

            # Xóa thuộc tính chỉ đọc
            if db_file.exists():
                db_file.chmod(stat.S_IWRITE | stat.S_IREAD)

            # Kết nối database
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()

            try:
                # Tìm các bản ghi chứa device ID
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                modified = False
                for table_name, in tables:
                    try:
                        # Lấy cấu trúc bảng
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = cursor.fetchall()

                        # Tìm các cột text
                        text_columns = [col[1] for col in columns if col[2].upper() in ['TEXT', 'VARCHAR', 'CHAR']]

                        for column in text_columns:
                            for key in VSCODE_CONFIG["telemetry_keys"]:
                                # Tìm các bản ghi chứa device ID
                                cursor.execute(f"SELECT rowid, {column} FROM {table_name} WHERE {column} LIKE ?", (f'%{key}%',))
                                rows = cursor.fetchall()

                                for rowid, value in rows:
                                    if key in str(value):
                                        # Tạo device ID mới
                                        new_id = self.id_generator.generate_device_id()
                                        new_value = str(value).replace(str(value), new_id)

                                        # Cập nhật bản ghi
                                        cursor.execute(f"UPDATE {table_name} SET {column} = ? WHERE rowid = ?", (new_value, rowid))

                                        result["old_ids"][f"{table_name}.{column}"] = value
                                        result["new_ids"][f"{table_name}.{column}"] = new_value
                                        modified = True

                                        logger.info(f"Updated {table_name}.{column}: {value} -> {new_value}")

                    except sqlite3.Error as e:
                        logger.warning(f"Could not process table {table_name}: {e}")
                        continue

                # Commit thay đổi
                if modified:
                    conn.commit()
                    logger.info(f"Successfully updated database: {db_file}")

                result["success"] = True

            finally:
                cursor.close()
                conn.close()

            # Khóa file (nếu cần)
            if lock_files:
                db_file.chmod(stat.S_IREAD)
                logger.info(f"Locked file: {db_file}")

        except Exception as e:
            error_msg = f"Failed to process state database: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    def _clean_workspace_storage(self, vscode_dir: Path, create_backups: bool) -> Dict[str, Any]:
        """
        Dọn dẹp chính xác workspace storage - Chỉ dọn dẹp các bản ghi liên quan AugmentCode, bảo vệ cấu hình plugin khác

        Args:
            vscode_dir: Đường dẫn thư mục VSCode
            create_backups: Có tạo backup không

        Returns:
            Dictionary kết quả dọn dẹp
        """
        result = {
            "success": False,
            "cleaned_count": 0,
            "projects_processed": 0,
            "records_deleted": 0,
            "errors": []
        }

        try:
            workspace_dir = vscode_dir.parent / "workspaceStorage"
            if not workspace_dir.exists():
                logger.info(f"Workspace storage directory does not exist: {workspace_dir}")
                result["success"] = True
                return result

            logger.info(f"Starting precise workspace cleaning: {workspace_dir}")

            # Duyệt từng thư mục project
            for project_dir in workspace_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                try:
                    result["projects_processed"] += 1
                    project_cleaned = False

                    # 1. Dọn dẹp các bản ghi AugmentCode trong database project
                    project_db = project_dir / "state.vscdb"
                    if project_db.exists():
                        if create_backups:
                            backup_path = self.backup_manager.create_file_backup(project_db, f"workspace_{project_dir.name}")
                            if backup_path:
                                logger.debug(f"Created project DB backup: {backup_path}")

                        records_deleted = self._clean_project_database(project_db)
                        if records_deleted > 0:
                            result["records_deleted"] += records_deleted
                            project_cleaned = True
                            logger.info(f"Cleaned {records_deleted} AugmentCode records from project {project_dir.name}")

                    # 2. Dọn dẹp thư mục chuyên dụng plugin AugmentCode (nếu tồn tại)
                    augment_dirs = [
                        project_dir / "augmentcode.augment",
                        project_dir / "augmentcode",
                        project_dir / "augment"
                    ]

                    for augment_dir in augment_dirs:
                        if augment_dir.exists() and augment_dir.is_dir():
                            try:
                                if create_backups:
                                    backup_path = self.backup_manager.create_directory_backup(augment_dir)
                                    if backup_path:
                                        logger.debug(f"Created AugmentCode dir backup: {backup_path}")

                                shutil.rmtree(augment_dir)
                                project_cleaned = True
                                logger.info(f"Removed AugmentCode directory: {augment_dir}")
                            except Exception as e:
                                logger.warning(f"Could not remove AugmentCode directory {augment_dir}: {e}")

                    # 3. Dọn dẹp các file cấu hình liên quan AugmentCode
                    augment_files = [
                        project_dir / "augment.json",
                        project_dir / "augmentcode.json",
                        project_dir / ".augment"
                    ]

                    for augment_file in augment_files:
                        if augment_file.exists():
                            try:
                                if create_backups:
                                    backup_path = self.backup_manager.create_file_backup(augment_file)
                                    if backup_path:
                                        logger.debug(f"Created AugmentCode file backup: {backup_path}")

                                augment_file.unlink()
                                project_cleaned = True
                                logger.info(f"Removed AugmentCode file: {augment_file}")
                            except Exception as e:
                                logger.warning(f"Could not remove AugmentCode file {augment_file}: {e}")

                    if project_cleaned:
                        result["cleaned_count"] += 1

                except Exception as e:
                    logger.warning(f"Error processing project directory {project_dir}: {e}")
                    result["errors"].append(f"Project {project_dir.name}: {str(e)}")

            logger.info(f"Workspace cleaning completed: {result['cleaned_count']} projects cleaned, "
                       f"{result['records_deleted']} records deleted from {result['projects_processed']} projects")
            result["success"] = True

        except Exception as e:
            error_msg = f"Workspace cleaning failed: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    def _clean_project_database(self, project_db: Path) -> int:
        """
        Dọn dẹp chính xác các bản ghi AugmentCode trong database project

        Args:
            project_db: Đường dẫn file database project

        Returns:
            Số lượng bản ghi đã xóa
        """
        records_deleted = 0

        try:
            # Kiểm tra xem có phải database SQLite hợp lệ không
            if not self._is_valid_sqlite_database(project_db):
                logger.debug(f"Skipping non-SQLite file: {project_db}")
                return 0

            conn = sqlite3.connect(str(project_db))
            cursor = conn.cursor()

            try:
                # Kiểm tra ItemTable có tồn tại không
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ItemTable'")
                if not cursor.fetchone():
                    logger.debug(f"No ItemTable found in {project_db}")
                    return 0

                # Các mẫu dọn dẹp liên quan AugmentCode
                augment_patterns = [
                    '%augment%',           # Liên quan AugmentCode
                    '%Augment%',           # Biến thể chữ hoa
                    '%AUGMENT%',           # Tất cả chữ hoa
                    '%cursor.com%',        # Liên quan domain Cursor
                    '%workos%',            # Dịch vụ xác thực WorkOS
                    '%oauth%',             # Trạng thái OAuth
                    '%auth%',              # Trạng thái xác thực
                    '%session%',           # Trạng thái phiên
                    '%token%',             # Token
                    '%login%'              # Trạng thái đăng nhập
                ]

                # Xóa chính xác các bản ghi khớp
                for pattern in augment_patterns:
                    cursor.execute("SELECT COUNT(*) FROM ItemTable WHERE key LIKE ?", (pattern,))
                    count = cursor.fetchone()[0]

                    if count > 0:
                        cursor.execute("DELETE FROM ItemTable WHERE key LIKE ?", (pattern,))
                        records_deleted += count
                        logger.debug(f"Deleted {count} records matching pattern {pattern}")

                # Commit thay đổi
                if records_deleted > 0:
                    conn.commit()
                    logger.debug(f"Successfully deleted {records_deleted} AugmentCode records from {project_db}")

            finally:
                cursor.close()
                conn.close()

        except sqlite3.Error as e:
            logger.warning(f"SQLite error cleaning project database {project_db}: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning project database {project_db}: {e}")

        return records_deleted

    def _is_valid_sqlite_database(self, db_file: Path) -> bool:
        """
        Kiểm tra file có phải database SQLite hợp lệ không

        Args:
            db_file: Đường dẫn file database

        Returns:
            True nếu là database SQLite hợp lệ, False nếu không
        """
        try:
            # File SQLite bắt đầu bằng "SQLite format 3\000"
            with open(db_file, 'rb') as f:
                header = f.read(16)
                return header.startswith(b'SQLite format 3\x00')
        except (OSError, IOError):
            return False

    def _clean_cache_directories(self, vscode_root: Path, create_backups: bool) -> Dict[str, Any]:
        """
        Dọn dẹp các thư mục cache

        Args:
            vscode_root: Đường dẫn thư mục gốc VSCode
            create_backups: Có tạo backup không

        Returns:
            Dictionary kết quả dọn dẹp
        """
        result = {
            "success": False,
            "cleaned_count": 0,
            "errors": []
        }

        try:
            cache_dirs = ["CachedExtensions", "CachedData", "logs", "GPUCache", "Service Worker"]

            for cache_dir_name in cache_dirs:
                cache_dir = vscode_root / cache_dir_name
                if cache_dir.exists():
                    try:
                        if create_backups:
                            backup_path = self.backup_manager.create_directory_backup(cache_dir)
                            if backup_path:
                                logger.info(f"Created cache backup: {backup_path}")

                        # Dọn dẹp thư mục cache
                        if cache_dir.is_dir():
                            shutil.rmtree(cache_dir)
                            result["cleaned_count"] += 1
                            logger.info(f"Cleaned cache directory: {cache_dir}")

                    except Exception as e:
                        logger.warning(f"Could not clean cache {cache_dir}: {e}")
                        result["errors"].append(f"Cache {cache_dir_name}: {str(e)}")

            result["success"] = True

        except Exception as e:
            error_msg = f"Cache cleaning failed: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    def verify_vscode_installation(self) -> Dict[str, Any]:
        """
        Xác minh cài đặt VSCode và trả về thông tin

        Returns:
            Dictionary thông tin cài đặt
        """
        info = {
            "installed": False,
            "variants_found": [],
            "total_directories": 0,
            "storage_files": [],
            "database_files": [],
            "missing_files": [],
            "storage_directories": []
        }

        try:
            # Lấy các thư mục VSCode
            vscode_dirs = self.path_manager.get_vscode_directories()
            if vscode_dirs:
                info["installed"] = True
                info["total_directories"] = len(vscode_dirs)
                info["storage_directories"] = [str(vscode_dir) for vscode_dir in vscode_dirs]

                # Kiểm tra từng thư mục (Cursor đã được ưu tiên từ paths.py)
                for vscode_dir in vscode_dirs:
                    variant_name = self.path_manager.get_vscode_variant_name(vscode_dir)
                    if variant_name not in info["variants_found"]:
                        # Ưu tiên Cursor lên đầu danh sách
                        if variant_name == "Cursor":
                            info["variants_found"].insert(0, variant_name)
                        else:
                            info["variants_found"].append(variant_name)

                    # Kiểm tra file lưu trữ
                    storage_file = vscode_dir / "storage.json"
                    if storage_file.exists():
                        info["storage_files"].append(str(storage_file))
                    else:
                        info["missing_files"].append(str(storage_file))

                    # Kiểm tra file database
                    db_file = vscode_dir / "state.vscdb"
                    if db_file.exists():
                        info["database_files"].append(str(db_file))
                    else:
                        info["missing_files"].append(str(db_file))

        except Exception as e:
            logger.error(f"Error verifying VSCode installation: {e}")
            info["error"] = str(e)

        return info

    def get_current_device_ids(self) -> Dict[str, Any]:
        """
        Lấy device ID hiện tại

        Returns:
            Dictionary thông tin device ID
        """
        ids = {
            "storage_ids": {},
            "database_ids": {},
            "errors": []
        }

        try:
            vscode_dirs = self.path_manager.get_vscode_directories()

            for vscode_dir in vscode_dirs:
                variant_name = vscode_dir.parent.name

                # Đọc ID từ storage.json
                storage_file = vscode_dir / "storage.json"
                if storage_file.exists():
                    try:
                        with open(storage_file, 'r', encoding='utf-8-sig') as f:
                            data = json.load(f)

                        storage_ids = {}
                        for key in VSCODE_CONFIG["telemetry_keys"]:
                            if key in data:
                                storage_ids[key] = data[key]

                        if storage_ids:
                            ids["storage_ids"][variant_name] = storage_ids

                    except Exception as e:
                        ids["errors"].append(f"Error reading {storage_file}: {str(e)}")

                # Đọc ID từ database (phiên bản đơn giản)
                db_file = vscode_dir / "state.vscdb"
                if db_file.exists():
                    try:
                        conn = sqlite3.connect(str(db_file))
                        cursor = conn.cursor()

                        # Tìm các bản ghi chứa device ID (truy vấn đơn giản)
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()

                        db_ids = {}
                        for table_name, in tables[:3]:  # Giới hạn số lượng bảng truy vấn
                            try:
                                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                                rows = cursor.fetchall()
                                for row in rows:
                                    for value in row:
                                        if isinstance(value, str):
                                            for key in VSCODE_CONFIG["telemetry_keys"]:
                                                if key in value:
                                                    db_ids[f"{table_name}"] = value[:100]  # Cắt giá trị dài
                                                    break
                            except:
                                continue

                        if db_ids:
                            ids["database_ids"][variant_name] = db_ids

                        cursor.close()
                        conn.close()

                    except Exception as e:
                        ids["errors"].append(f"Error reading {db_file}: {str(e)}")

        except Exception as e:
            ids["errors"].append(f"Error getting device IDs: {str(e)}")

        return ids

    def get_current_vscode_ids(self):
        """
        Lấy thông tin device ID hiện tại của VSCode/Cursor

        Returns:
            Dict[str, Dict]: Chứa thông tin ID của các biến thể VSCode
        """
        result = {}

        try:
            # Lấy tất cả thư mục VSCode
            vscode_dirs = self.path_manager.get_vscode_directories()

            for vscode_dir in vscode_dirs:
                variant_name = self._get_variant_name_from_path(str(vscode_dir))

                # Chỉ xử lý thư mục globalStorage
                if 'globalStorage' in str(vscode_dir):
                    variant_ids = {}

                    # Kiểm tra file storage.json
                    storage_file = vscode_dir / "storage.json"
                    if storage_file.exists():
                        try:
                            with open(storage_file, 'r', encoding='utf-8-sig') as f:
                                data = json.load(f)

                            # Trích xuất telemetry ID
                            telemetry_keys = [
                                'telemetry.machineId',
                                'telemetry.devDeviceId',
                                'telemetry.macMachineId',
                                'telemetry.sqmId'
                            ]

                            for key in telemetry_keys:
                                if key in data:
                                    variant_ids[key] = data[key]

                        except Exception as e:
                            logger.warning(f"Could not read storage.json for {variant_name}: {e}")

                    # Kiểm tra file machineId
                    machine_id_file = vscode_dir.parent / "machineId"
                    if machine_id_file.exists():
                        try:
                            with open(machine_id_file, 'r', encoding='utf-8') as f:
                                machine_id = f.read().strip()
                            variant_ids['machineId'] = machine_id
                        except Exception as e:
                            logger.warning(f"Could not read machineId for {variant_name}: {e}")

                    if variant_ids:
                        result[variant_name] = variant_ids

        except Exception as e:
            logger.error(f"Failed to get VSCode IDs: {e}")

        return result

    def perform_automated_rotation(self, 
                                   create_backups: bool = True,
                                   lock_files: bool = True) -> Dict[str, Any]:
        """
        Perform automated rotation (wrapper for rotation engine)
        
        Args:
            create_backups: Create backups before rotation
            lock_files: Lock files after rotation
            
        Returns:
            Rotation result dictionary
        """
        return self.process_vscode_installations(
            create_backups=create_backups,
            lock_files=lock_files,
            clean_workspace=False,
            clean_cache=False
        )
    
    def _get_variant_name_from_path(self, path_str):
        """Lấy tên biến thể VSCode từ đường dẫn"""
        if 'Cursor' in path_str:
            return 'Cursor'
        elif 'Code - Insiders' in path_str:
            return 'VSCode Insiders'
        elif 'Code' in path_str:
            return 'VSCode'
        elif 'VSCodium' in path_str:
            return 'VSCodium'
        else:
            return 'Unknown VSCode Variant'
