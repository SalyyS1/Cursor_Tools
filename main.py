#!/usr/bin/env python3
"""
AugmentCode Unlimited - Điểm Vào Chính

Công cụ toàn diện để dọn dẹp dữ liệu liên quan AugmentCode
và cho phép đăng nhập không giới hạn với các tài khoản khác nhau.
Tập trung tối ưu cho Cursor IDE.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Import các module
from config.settings import VERSION, APP_NAME, DEFAULT_SETTINGS, LOGGING_CONFIG
from utils.i18n import t, init_translator
from utils.paths import PathManager
from utils.backup import BackupManager
from utils.id_generator import IDGenerator
from utils.file_locker import FileLockManager
from core.jetbrains_handler import JetBrainsHandler
from core.vscode_handler import VSCodeHandler
from core.db_cleaner import DatabaseCleaner

# Khởi tạo translator với tiếng Việt
init_translator("vi")


def setup_logging(verbose: bool = False) -> None:
    """
    Thiết lập cấu hình logging
    
    Args:
        verbose: Bật logging chi tiết
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format=LOGGING_CONFIG["format"],
        datefmt=LOGGING_CONFIG["date_format"]
    )
    
    # Reduce noise from some modules
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Tạo và cấu hình argument parser
    
    Returns:
        ArgumentParser instance đã cấu hình
    """
    parser = argparse.ArgumentParser(
        prog="augmentcode-unlimited",
        description=f"{APP_NAME} v{VERSION} - Dọn dẹp dữ liệu AugmentCode để chuyển đổi tài khoản không giới hạn",
        epilog="Để biết thêm thông tin, xem file README.md."
    )
    
    # Các chế độ hoạt động chính
    parser.add_argument(
        "--jetbrains-only",
        action="store_true",
        help="Chỉ xử lý JetBrains IDEs"
    )
    
    parser.add_argument(
        "--vscode-only", 
        action="store_true",
        help="Chỉ xử lý VSCode variants (bao gồm Cursor)"
    )
    
    # Tùy chọn backup
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Bỏ qua tạo backup (không khuyến nghị)"
    )
    
    # Tùy chọn khóa file
    parser.add_argument(
        "--no-lock",
        action="store_true", 
        help="Bỏ qua khóa file sau khi sửa"
    )
    
    # Tùy chọn dọn dẹp database
    parser.add_argument(
        "--no-database-clean",
        action="store_true",
        help="Bỏ qua dọn dẹp SQLite databases"
    )
    
    # Tùy chọn dọn dẹp workspace
    parser.add_argument(
        "--no-workspace-clean",
        action="store_true",
        help="Bỏ qua dọn dẹp workspace storage"
    )
    
    # Tùy chọn thông tin
    parser.add_argument(
        "--info",
        action="store_true",
        help="Hiển thị thông tin cài đặt và thoát"
    )

    parser.add_argument(
        "--current-ids",
        action="store_true",
        help="Hiển thị giá trị ID hiện tại và thoát"
    )

    parser.add_argument(
        "--paths",
        action="store_true",
        help="Hiển thị đường dẫn hệ thống và thoát"
    )

    parser.add_argument(
        "--legacy-output",
        action="store_true",
        help="Sử dụng định dạng output kiểu free-augmentcode cũ"
    )
    
    # Tùy chọn output
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Bật output chi tiết"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Ẩn output không phải lỗi"
    )
    
    # Phiên bản
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} v{VERSION}"
    )
    
    return parser


def print_banner() -> None:
    """In banner ứng dụng"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          {APP_NAME}                           ║
║                                 v{VERSION}                                  ║
║                                                                              ║
║  {t('cli.banner.description')}   ║
║                                                                              ║
║  {t('cli.banner.supports')}        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def print_system_paths(path_manager: PathManager) -> None:
    """
    In thông tin đường dẫn hệ thống

    Args:
        path_manager: Instance quản lý đường dẫn
    """
    print("\n" + "="*80)
    print(t("cli.paths.title"))
    print("="*80)

    platform_paths = path_manager.platform_paths

    print(f"\n{t('cli.paths.system_dirs')}")
    print(t("cli.paths.home", path=str(platform_paths['home'])))
    print(t("cli.paths.config", path=str(platform_paths['config'])))
    print(t("cli.paths.data", path=str(platform_paths['data'])))

    # Đường dẫn VSCode (bao gồm Cursor)
    print(f"\n{t('cli.paths.vscode_paths')}")
    workspace_path = path_manager.get_workspace_storage_path()
    print(t("cli.paths.workspace_storage", path=str(workspace_path) if workspace_path else t("cli.paths.not_found")))

    # Hiển thị một số đường dẫn storage ví dụ
    vscode_dirs = path_manager.get_vscode_directories()
    if vscode_dirs:
        print(t("cli.paths.example_storage"))
        for i, vscode_dir in enumerate(vscode_dirs[:3]):
            storage_file = path_manager.get_vscode_storage_file(vscode_dir)
            db_file = path_manager.get_vscode_database_file(vscode_dir)
            print(t("cli.paths.storage_item", num=i+1, path=str(storage_file) if storage_file else "N/A"))
            print(t("cli.paths.database_item", path=str(db_file) if db_file else "N/A"))
        if len(vscode_dirs) > 3:
            print(t("cli.paths.more", count=len(vscode_dirs) - 3))

    # Đường dẫn JetBrains
    jetbrains_dir = path_manager.get_jetbrains_config_dir()
    print(f"\n{t('cli.paths.jetbrains_paths')}")
    print(t("cli.paths.config_dir", path=str(jetbrains_dir) if jetbrains_dir else t("cli.paths.not_found")))
    if jetbrains_dir:
        id_files = path_manager.get_jetbrains_id_files()
        print(t("cli.paths.id_files"))
        for id_file in id_files:
            print(t("cli.paths.id_file_item", path=str(id_file)))


def print_installation_info(jetbrains_handler: JetBrainsHandler, vscode_handler: VSCodeHandler, database_cleaner: DatabaseCleaner) -> None:
    """
    In thông tin cài đặt
    
    Args:
        jetbrains_handler: Instance xử lý JetBrains
        vscode_handler: Instance xử lý VSCode
        database_cleaner: Instance dọn dẹp database
    """
    print("\n" + "="*80)
    print(t("cli.info.title"))
    print("="*80)
    
    # Thông tin JetBrains
    jetbrains_info = jetbrains_handler.verify_jetbrains_installation()
    print(f"\n{t('cli.info.jetbrains')}")
    print(t("cli.info.installed", status=t("cli.info.yes") if jetbrains_info['installed'] else t("cli.info.no")))
    if jetbrains_info['installed']:
        print(t("cli.info.config_dir", path=str(jetbrains_info['config_dir'])))
        print(t("cli.info.id_files_found", found=len(jetbrains_info['existing_files']), total=len(jetbrains_info['id_files'])))
        for file_path in jetbrains_info['existing_files']:
            print(f"     {t('cli.ids.found')} {file_path}")
        for file_path in jetbrains_info['missing_files']:
            print(f"     {t('cli.ids.not_found')} {file_path}")
    
    # Thông tin VSCode (ưu tiên hiển thị Cursor)
    vscode_info = vscode_handler.verify_vscode_installation()
    print(f"\n{t('cli.info.vscode')}")
    print(t("cli.info.installed", status=t("cli.info.yes") if vscode_info['installed'] else t("cli.info.no")))
    if vscode_info['installed']:
        variants = vscode_info['variants_found']
        # Sắp xếp để Cursor lên đầu
        if 'Cursor' in variants:
            variants.remove('Cursor')
            variants.insert(0, 'Cursor')
        print(t("cli.info.variants_found", variants=', '.join(variants)))
        print(t("cli.info.storage_directories", count=vscode_info['total_directories']))
        for directory in vscode_info['storage_directories'][:5]:  # Hiển thị 5 đầu tiên
            print(f"     • {directory}")
        if vscode_info['total_directories'] > 5:
            print(t("cli.paths.more", count=vscode_info['total_directories'] - 5))
    
    # Thông tin Database
    db_info = database_cleaner.get_database_info()
    print(f"\n{t('cli.info.databases')}")
    print(t("cli.info.total_found", count=db_info['total_databases']))
    print(t("cli.info.accessible", count=db_info['accessible_databases']))
    
    total_augment_records = sum(db['augment_records'] for db in db_info['databases'] if db.get('augment_records'))
    print(t("cli.info.augment_records", count=total_augment_records))


def print_current_ids(jetbrains_handler: JetBrainsHandler, vscode_handler: VSCodeHandler) -> None:
    """
    In giá trị ID hiện tại
    
    Args:
        jetbrains_handler: Instance xử lý JetBrains
        vscode_handler: Instance xử lý VSCode
    """
    print("\n" + "="*80)
    print(t("cli.ids.title"))
    print("="*80)
    
    # JetBrains IDs
    jetbrains_ids = jetbrains_handler.get_current_jetbrains_ids()
    print(f"\n{t('cli.ids.jetbrains')}")
    if jetbrains_ids:
        for file_name, id_value in jetbrains_ids.items():
            status = t("cli.ids.found") if id_value else t("cli.ids.not_found")
            print(f"   {status} {file_name}: {id_value or t('cli.paths.not_found')}")
    else:
        print(t("cli.ids.no_jetbrains"))
    
    # VSCode IDs (ưu tiên hiển thị Cursor)
    vscode_ids = vscode_handler.get_current_vscode_ids()
    print(f"\n{t('cli.ids.vscode')}")
    if vscode_ids:
        # Sắp xếp để Cursor lên đầu
        sorted_dirs = sorted(vscode_ids.items(), key=lambda x: (0 if 'Cursor' in str(x[0]) else 1, str(x[0])))
        for directory, ids in sorted_dirs:
            print(t("cli.ids.directory", name=Path(directory).name))
            for key, value in ids.items():
                status = t("cli.ids.found") if value else t("cli.ids.not_found")
                print(f"     {status} {key}: {value or t('cli.paths.not_found')}")
    else:
        print(t("cli.ids.no_vscode"))


def main() -> int:
    """
    Main entry point
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    verbose = args.verbose and not args.quiet
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    # Print banner unless quiet
    if not args.quiet:
        print_banner()
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        path_manager = PathManager()
        backup_manager = BackupManager()
        jetbrains_handler = JetBrainsHandler(path_manager, backup_manager)
        vscode_handler = VSCodeHandler(path_manager, backup_manager)
        database_cleaner = DatabaseCleaner(path_manager, backup_manager)
        
        # Handle information requests
        if args.info:
            print_installation_info(jetbrains_handler, vscode_handler, database_cleaner)
            return 0

        if args.current_ids:
            print_current_ids(jetbrains_handler, vscode_handler)
            return 0

        if args.paths:
            print_system_paths(path_manager)
            return 0
        
        # Kiểm tra arguments
        if args.jetbrains_only and args.vscode_only:
            logger.error(t("cli.errors.both_flags"))
            return 1
        
        # Determine what to process
        process_jetbrains = not args.vscode_only
        process_vscode = not args.jetbrains_only
        create_backups = not args.no_backup
        lock_files = not args.no_lock
        clean_database = not args.no_database_clean
        clean_workspace = not args.no_workspace_clean
        
        logger.info(f"Starting {APP_NAME} v{VERSION}")
        logger.info(f"Process JetBrains: {process_jetbrains}")
        logger.info(f"Process VSCode: {process_vscode}")
        logger.info(f"Create backups: {create_backups}")
        logger.info(f"Lock files: {lock_files}")
        logger.info(f"Clean database: {clean_database}")
        logger.info(f"Clean workspace: {clean_workspace}")
        
        # Track overall results
        overall_success = False
        results = {}
        
        # Xử lý JetBrains IDEs
        if process_jetbrains:
            if not args.quiet:
                print(t("cli.processing.jetbrains"))
            
            jetbrains_result = jetbrains_handler.process_jetbrains_ides(
                create_backups=create_backups,
                lock_files=lock_files
            )
            results["jetbrains"] = jetbrains_result
            
            if jetbrains_result["success"]:
                overall_success = True
                if not args.quiet:
                    print(t("cli.processing.jetbrains_processed", count=len(jetbrains_result['files_processed'])))

                    # Hiển thị kết quả chi tiết
                    if jetbrains_result["old_ids"] and jetbrains_result["new_ids"]:
                        print("   📋 Thay đổi ID:")
                        for file_name in jetbrains_result["old_ids"]:
                            old_id = jetbrains_result["old_ids"].get(file_name, "N/A")
                            new_id = jetbrains_result["new_ids"].get(file_name, "N/A")
                            print(f"     {file_name}:")
                            print(f"       Cũ: {old_id}")
                            print(f"       Mới: {new_id}")

                    if jetbrains_result["backups_created"]:
                        print(t("cli.processing.backups_created", count=len(jetbrains_result['backups_created'])))
                        for backup in jetbrains_result["backups_created"]:
                            print(f"     • {backup}")
            else:
                if not args.quiet:
                    print(t("cli.processing.jetbrains_failed"))
                    for error in jetbrains_result["errors"]:
                        print(f"     Lỗi: {error}")
        
        # Xử lý VSCode variants (ưu tiên Cursor)
        if process_vscode:
            if not args.quiet:
                print(t("cli.processing.vscode"))
            
            vscode_result = vscode_handler.process_vscode_installations(
                create_backups=create_backups,
                lock_files=lock_files,
                clean_workspace=clean_workspace
            )
            results["vscode"] = vscode_result
            
            if vscode_result["success"]:
                overall_success = True
                if not args.quiet:
                    print(t("cli.processing.vscode_processed", count=len(vscode_result['directories_processed'])))

                    # Hiển thị kết quả chi tiết
                    if vscode_result["old_ids"] and vscode_result["new_ids"]:
                        print("   📋 Thay đổi ID:")
                        for key in vscode_result["old_ids"]:
                            old_id = vscode_result["old_ids"].get(key, "N/A")
                            new_id = vscode_result["new_ids"].get(key, "N/A")
                            print(f"     {key}:")
                            print(f"       Cũ: {old_id}")
                            print(f"       Mới: {new_id}")

                    if vscode_result["backups_created"]:
                        print(t("cli.processing.backups_created", count=len(vscode_result['backups_created'])))

                    if vscode_result["workspace_cleaned"]:
                        print(t("cli.processing.workspace_cleaned"))
                        if vscode_result["workspace_backup"]:
                            print(t("cli.processing.workspace_backup", path=vscode_result['workspace_backup']))
            else:
                if not args.quiet:
                    print(t("cli.processing.vscode_failed"))
                    for error in vscode_result["errors"]:
                        print(f"     Lỗi: {error}")
        
        # Dọn dẹp databases
        if clean_database and (process_vscode or not process_jetbrains):
            if not args.quiet:
                print(t("cli.processing.databases"))
            
            db_result = database_cleaner.clean_all_databases(create_backups=create_backups)
            results["database"] = db_result
            
            if db_result["success"]:
                if not args.quiet:
                    print(t("cli.processing.databases_cleaned", count=db_result['databases_cleaned']))
                    print(t("cli.processing.records_deleted", count=db_result['total_records_deleted']))

                    # Hiển thị kết quả chi tiết
                    if db_result["backups_created"]:
                        print(t("cli.processing.backups_created", count=len(db_result['backups_created'])))

                    print("   📊 Tóm tắt Database:")
                    print(f"     Tổng tìm thấy: {db_result['databases_found']}")
                    print(f"     Dọn dẹp thành công: {db_result['databases_cleaned']}")
                    print(f"     Thất bại: {db_result['databases_failed']}")
            else:
                if not args.quiet:
                    print(t("cli.processing.database_failed"))
                    for error in db_result["errors"]:
                        print(f"     Lỗi: {error}")
        
        # In tóm tắt
        if not args.quiet:
            print("\n" + "="*80)
            if overall_success:
                print(t("cli.summary.success"))
                print(f"\n{t('cli.summary.next_steps')}")
                print(t("cli.summary.step_1"))
                print(t("cli.summary.step_2"))
                print(t("cli.summary.step_3"))
                
                if create_backups:
                    print(t("cli.summary.backups_location", path=str(backup_manager.backup_dir)))
            else:
                print(t("cli.summary.failed"))
                print(f"\n{t('cli.summary.some_failed')}")
                print(t("cli.summary.need_permissions"))
            print("="*80)
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        logger.info("Thao tác đã bị hủy bởi người dùng")
        if not args.quiet:
            print(t("cli.errors.cancelled"))
        return 1
    except Exception as e:
        logger.error(f"Lỗi không mong đợi: {e}", exc_info=True)
        if not args.quiet:
            print(t("cli.errors.unexpected", error=str(e)))
        return 1


if __name__ == "__main__":
    sys.exit(main())
