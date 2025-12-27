#!/usr/bin/env python3
"""
Database Cleaner - Module dọn dẹp database

Xử lý chuyên biệt việc dọn dẹp các bản ghi liên quan AugmentCode trong database VSCode và JetBrains
"""

import logging
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

from config.settings import VSCODE_CONFIG, JETBRAINS_CONFIG

logger = logging.getLogger(__name__)


class DatabaseCleaner:
    """Bộ dọn dẹp database"""
    
    def __init__(self, path_manager, backup_manager):
        """
        Khởi tạo bộ dọn dẹp database
        
        Args:
            path_manager: Instance quản lý đường dẫn
            backup_manager: Instance quản lý backup
        """
        self.path_manager = path_manager
        self.backup_manager = backup_manager
    
    def clean_vscode_databases(self, create_backups: bool = True) -> Dict[str, Any]:
        """
        Dọn dẹp các bản ghi AugmentCode trong database VSCode
        
        Args:
            create_backups: Có tạo backup không
            
        Returns:
            Dictionary kết quả dọn dẹp
        """
        logger.info("Starting VSCode database cleaning")
        
        results = {
            "success": False,
            "databases_found": 0,
            "databases_cleaned": 0,
            "databases_failed": 0,
            "total_records_deleted": 0,
            "backups_created": [],
            "errors": []
        }
        
        try:
            # Find VSCode directories
            vscode_dirs = self.path_manager.get_vscode_directories()
            if not vscode_dirs:
                results["errors"].append("No VSCode installations found")
                return results
            
            # Process each VSCode directory
            for vscode_dir in vscode_dirs:
                db_file = self.path_manager.get_vscode_database_file(vscode_dir)
                if db_file:
                    results["databases_found"] += 1
                    
                    db_result = self._clean_database_file(db_file, create_backups)
                    if db_result["success"]:
                        results["databases_cleaned"] += 1
                        results["total_records_deleted"] += db_result["records_deleted"]
                        if db_result["backup_path"]:
                            results["backups_created"].append(db_result["backup_path"])
                    else:
                        results["databases_failed"] += 1
                        if db_result["error"]:
                            results["errors"].append(f"{db_file.name}: {db_result['error']}")
            
            # Đánh giá thành công tổng thể
            if results["databases_cleaned"] > 0:
                results["success"] = True
                logger.info(f"Successfully cleaned {results['databases_cleaned']} VSCode databases")
            
        except Exception as e:
            error_msg = f"VSCode database cleaning failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def clean_jetbrains_databases(self, create_backups: bool = True) -> Dict[str, Any]:
        """
        Dọn dẹp các bản ghi AugmentCode trong database JetBrains
        
        Args:
            create_backups: Có tạo backup không
            
        Returns:
            Dictionary kết quả dọn dẹp
        """
        logger.info("Starting JetBrains database cleaning")
        
        results = {
            "success": False,
            "databases_found": 0,
            "databases_cleaned": 0,
            "databases_failed": 0,
            "total_records_deleted": 0,
            "backups_created": [],
            "errors": []
        }
        
        try:
            # Find JetBrains database files
            jetbrains_dbs = self.path_manager.get_jetbrains_database_files()
            if not jetbrains_dbs:
                results["errors"].append("No JetBrains database files found")
                return results
            
            results["databases_found"] = len(jetbrains_dbs)
            
            # Process each database file
            for db_file in jetbrains_dbs:
                db_result = self._clean_database_file(db_file, create_backups, use_jetbrains_patterns=True)
                if db_result["success"]:
                    results["databases_cleaned"] += 1
                    results["total_records_deleted"] += db_result["records_deleted"]
                    if db_result["backup_path"]:
                        results["backups_created"].append(db_result["backup_path"])
                else:
                    results["databases_failed"] += 1
                    if db_result["error"]:
                        results["errors"].append(f"{db_file.name}: {db_result['error']}")
            
            # Đánh giá thành công tổng thể
            if results["databases_cleaned"] > 0:
                results["success"] = True
                logger.info(f"Successfully cleaned {results['databases_cleaned']} JetBrains databases")
            
        except Exception as e:
            error_msg = f"JetBrains database cleaning failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _clean_database_file(self, db_file: Path, create_backups: bool, 
                            use_jetbrains_patterns: bool = False) -> Dict[str, Any]:
        """
        Dọn dẹp một file database
        
        Args:
            db_file: Đường dẫn file database
            create_backups: Có tạo backup không
            use_jetbrains_patterns: Có sử dụng mẫu JetBrains không
            
        Returns:
            Dictionary kết quả dọn dẹp
        """
        result = {
            "success": False,
            "backup_path": None,
            "records_deleted": 0,
            "error": None
        }
        
        try:
            # Kiểm tra file có phải database SQLite hợp lệ không
            if not self._is_valid_sqlite_database(db_file):
                logger.warning(f"Skipping non-SQLite file: {db_file}")
                result["success"] = True  # Không phải lỗi, chỉ bỏ qua
                return result
            
            # Tạo backup
            if create_backups:
                backup_path = self.backup_manager.create_file_backup(db_file)
                if backup_path:
                    result["backup_path"] = str(backup_path)
                    logger.info(f"Created backup: {backup_path}")
            
            # Dọn dẹp database
            records_deleted = self._execute_database_cleaning(db_file, use_jetbrains_patterns)
            result["records_deleted"] = records_deleted
            
            logger.info(f"Successfully deleted {records_deleted} records from {db_file}")
            result["success"] = True
            
        except Exception as e:
            error_msg = f"Database cleaning failed: {str(e)}"
            logger.error(f"Error cleaning database {db_file}: {error_msg}")
            result["error"] = error_msg
        
        return result
    
    def _is_valid_sqlite_database(self, db_file: Path) -> bool:
        """
        Kiểm tra file có phải database SQLite hợp lệ không
        
        Args:
            db_file: Đường dẫn file database
            
        Returns:
            Có phải database SQLite hợp lệ không
        """
        try:
            # Kiểm tra header file
            with open(db_file, 'rb') as f:
                header = f.read(16)
                if not header.startswith(b'SQLite format 3\x00'):
                    return False
            
            # Thử kết nối database
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            cursor.close()
            conn.close()
            return True
            
        except Exception:
            return False

    def _execute_database_cleaning(self, db_file: Path, use_jetbrains_patterns: bool = False) -> int:
        """
        Thực hiện thao tác dọn dẹp database thực tế

        Args:
            db_file: Đường dẫn file database
            use_jetbrains_patterns: Có sử dụng mẫu JetBrains không

        Returns:
            Số lượng bản ghi đã xóa
        """
        total_deleted = 0

        try:
            # Kết nối database
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()

            try:
                # Lấy tất cả các bảng
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                # Chọn mẫu dọn dẹp
                patterns = JETBRAINS_CONFIG["augment_patterns"] if use_jetbrains_patterns else [
                    "%augment%", "%Augment%", "%AUGMENT%", "%device%", "%machine%", "%telemetry%"
                ]

                # Dọn dẹp từng bảng
                for table_name, in tables:
                    table_deleted = self._clean_table_records(cursor, table_name, patterns)
                    total_deleted += table_deleted

                # Commit tất cả thay đổi
                conn.commit()

                # Dọn dẹp database backup (nếu tồn tại)
                backup_db_file = db_file.with_suffix(db_file.suffix + ".backup")
                if backup_db_file.exists():
                    logger.info(f"Cleaning backup database: {backup_db_file}")
                    backup_deleted = self._execute_database_cleaning(backup_db_file, use_jetbrains_patterns)
                    logger.info(f"Deleted {backup_deleted} records from backup database")

            finally:
                cursor.close()
                conn.close()

        except sqlite3.Error as e:
            logger.error(f"SQLite error while cleaning {db_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while cleaning {db_file}: {e}")
            raise

        return total_deleted

    def _clean_table_records(self, cursor, table_name: str, patterns: List[str]) -> int:
        """
        Dọn dẹp các bản ghi trong bảng

        Args:
            cursor: Con trỏ database
            table_name: Tên bảng
            patterns: Danh sách mẫu khớp

        Returns:
            Số lượng bản ghi đã xóa
        """
        deleted_count = 0

        try:
            # Lấy cấu trúc bảng
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # Tìm các cột text
            text_columns = [col[1] for col in columns if col[2].upper() in ['TEXT', 'VARCHAR', 'CHAR', 'BLOB']]

            for column in text_columns:
                for pattern in patterns:
                    try:
                        # Đếm số bản ghi cần xóa
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column} LIKE ?", (pattern,))
                        count = cursor.fetchone()[0]

                        if count > 0:
                            # Xóa bản ghi
                            cursor.execute(f"DELETE FROM {table_name} WHERE {column} LIKE ?", (pattern,))
                            deleted_count += count
                            logger.info(f"Cleaned {count} records from {table_name}.{column} matching {pattern}")

                    except sqlite3.Error as e:
                        logger.warning(f"Could not clean {table_name}.{column} with pattern {pattern}: {e}")
                        continue

        except sqlite3.Error as e:
            logger.warning(f"Could not process table {table_name}: {e}")

        return deleted_count

    def get_database_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin database

        Returns:
            Dictionary thông tin database
        """
        info = {
            "vscode_databases": [],
            "jetbrains_databases": [],
            "total_databases": 0,
            "accessible_databases": 0,
            "errors": []
        }

        try:
            # Database VSCode
            vscode_dirs = self.path_manager.get_vscode_directories()
            for vscode_dir in vscode_dirs:
                db_file = self.path_manager.get_vscode_database_file(vscode_dir)
                if db_file:
                    db_info = {
                        "path": str(db_file),
                        "variant": vscode_dir.parent.name,
                        "exists": db_file.exists(),
                        "accessible": False,
                        "size": 0
                    }

                    if db_file.exists():
                        try:
                            db_info["size"] = db_file.stat().st_size
                            if self._is_valid_sqlite_database(db_file):
                                db_info["accessible"] = True
                                info["accessible_databases"] += 1
                        except Exception as e:
                            info["errors"].append(f"Error accessing {db_file}: {str(e)}")

                    info["vscode_databases"].append(db_info)
                    info["total_databases"] += 1

            # Database JetBrains
            jetbrains_dbs = self.path_manager.get_jetbrains_database_files()
            for db_file in jetbrains_dbs:
                db_info = {
                    "path": str(db_file),
                    "exists": db_file.exists(),
                    "accessible": False,
                    "size": 0
                }

                if db_file.exists():
                    try:
                        db_info["size"] = db_file.stat().st_size
                        if self._is_valid_sqlite_database(db_file):
                            db_info["accessible"] = True
                            info["accessible_databases"] += 1
                    except Exception as e:
                        info["errors"].append(f"Error accessing {db_file}: {str(e)}")

                info["jetbrains_databases"].append(db_info)
                info["total_databases"] += 1

        except Exception as e:
            info["errors"].append(f"Error getting database info: {str(e)}")

        return info
