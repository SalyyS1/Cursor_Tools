#!/usr/bin/env python3
"""
Xây dựng file thực thi cho Augment Cleaner Unified

Sử dụng PyInstaller để đóng gói phiên bản GUI thành file exe
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Kiểm tra PyInstaller đã được cài đặt chưa"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller đã được cài đặt, phiên bản: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller chưa được cài đặt")
        return False

def install_pyinstaller():
    """Cài đặt PyInstaller"""
    print("Đang cài đặt PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=5.0.0"])
        print("✅ Cài đặt PyInstaller thành công")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Cài đặt PyInstaller thất bại: {e}")
        print("\n💡 Giải pháp:")
        print("1. Kiểm tra kết nối mạng")
        print("2. Thử sử dụng mirror nội địa:")
        print(f"   {sys.executable} -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        print("3. Hoặc tải xuống gói cài đặt PyInstaller thủ công")
        print("4. Nếu sử dụng Anaconda, thử: conda install pyinstaller -c conda-forge")
        return False

def create_icon():
    """Tạo file icon đơn giản (nếu chưa tồn tại)"""
    icon_path = Path("icon.ico")
    if not icon_path.exists():
        print("📝 Đang tạo icon mặc định...")
        # Có thể đặt logic tạo icon đơn giản ở đây
        # Hoặc người dùng có thể đặt file icon.ico thủ công
        print("💡 Gợi ý: Bạn có thể đặt file icon.ico trong thư mục gốc dự án để tùy chỉnh icon")

def build_executable():
    """Xây dựng file thực thi"""
    print("🚀 Bắt đầu xây dựng file thực thi...")

    # Kiểm tra và đóng file exe có thể đang chạy
    exe_path = Path("dist") / "AugmentCleanerUnified.exe"
    if exe_path.exists():
        print("⚠️ Phát hiện file exe đã tồn tại, đang thử xóa...")
        try:
            exe_path.unlink()
            print("✅ Đã xóa file exe cũ")
        except PermissionError:
            print("⚠️ Không thể xóa file exe cũ (có thể đang chạy), PyInstaller sẽ thử ghi đè")
    
    # Tham số lệnh PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",                    # Đóng gói thành một file
        "--windowed",                   # Không có cửa sổ console
        "--name=AugmentCleanerUnified", # Tên file thực thi
        "--distpath=dist",              # Thư mục đầu ra
        "--workpath=build",             # Thư mục file tạm
        "--specpath=.",                 # Vị trí file spec
        "--clean",                      # Dọn dẹp file tạm
        "--noconfirm",                  # Không hỏi ghi đè
        "gui_main.py"                   # File chính
    ]
    
    # Thêm icon (nếu có)
    icon_path = Path("icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        print(f"📎 Sử dụng icon: {icon_path}")
    
    # Thêm import ẩn (đảm bảo tất cả module được bao gồm)
    hidden_imports = [
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.scrolledtext",
        "threading",
        "pathlib",
        "sqlite3",
        "json",
        "uuid",
        "hashlib",
        "secrets",
        "shutil",
        "stat",
        "subprocess",
        "time",
        "logging",
    ]
    
    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])
    
    # Thêm file dữ liệu (nếu cần)
    # cmd.extend(["--add-data", "config;config"])
    
    print(f"Thực thi lệnh: {' '.join(cmd)}")
    
    try:
        # Thực thi PyInstaller
        print("Đang thực thi PyInstaller...")
        result = subprocess.run(cmd, check=False, capture_output=False, text=True)

        # Kiểm tra file đầu ra
        exe_path = Path("dist") / "AugmentCleanerUnified.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("✅ Xây dựng thành công!")
            print(f"📦 File thực thi: {exe_path}")
            print(f"📏 Kích thước file: {size_mb:.1f} MB")
            return True
        else:
            print("❌ Không tìm thấy file thực thi")
            print(f"Mã trả về PyInstaller: {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ Có lỗi trong quá trình xây dựng: {e}")

        # Ngay cả khi có lỗi, cũng kiểm tra xem file exe đã được tạo chưa
        exe_path = Path("dist") / "AugmentCleanerUnified.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("⚠️ Mặc dù có lỗi, nhưng file exe đã được tạo!")
            print(f"📦 File thực thi: {exe_path}")
            print(f"📏 Kích thước file: {size_mb:.1f} MB")
            return True

        return False



def create_readme():
    """Tạo hướng dẫn sử dụng"""
    readme_content = """# Augment Cleaner Unified - Phiên bản thực thi

## 🎯 Giới thiệu
Đây là phiên bản giao diện đồ họa của Augment Cleaner Unified, đã được đóng gói thành file thực thi, không cần cài đặt Python để sử dụng.

## 🚀 Bắt đầu nhanh

1. Nhấp đúp `AugmentCleanerUnified.exe`
2. Làm theo hướng dẫn trên giao diện

## 📋 Các bước sử dụng

1. **Chuẩn bị**
   - Đóng tất cả IDE (VSCode, JetBrains IDEs, Cursor, v.v.)
   - Thoát plugin AugmentCode

2. **Chạy chương trình**
   - Nhấp đúp file thực thi để khởi động
   - Xem trạng thái hệ thống, xác nhận đã phát hiện phần mềm liên quan

3. **Cấu hình tùy chọn**
   - Chọn loại IDE cần xử lý
   - Khuyến nghị giữ cài đặt mặc định (tạo backup, khóa file, v.v.)

4. **Bắt đầu dọn dẹp**
   - Nhấp nút "🚀 Bắt đầu dọn dẹp"
   - Chờ quá trình xử lý hoàn tất

5. **Hoàn tất**
   - Khởi động lại IDE
   - Đăng nhập với tài khoản AugmentCode mới

## 🛡️ Tính năng bảo mật

- ✅ **Tự động backup**: Tự động backup tất cả file trước khi sửa đổi
- ✅ **Khóa file**: Ngăn chặn sửa đổi bị ghi đè
- ✅ **Log chi tiết**: Ghi lại toàn bộ quá trình thao tác
- ✅ **Khôi phục lỗi**: Có thể khôi phục từ backup khi gặp lỗi

## 📁 Vị trí backup

File backup được lưu tại: `C:\\Users\\TênNgườiDùng\\.augment_cleaner_backups\\`

## ❓ Câu hỏi thường gặp

**Q: Chương trình không khởi động được?**
A: Thử chạy với quyền quản trị viên, hoặc kiểm tra phần mềm diệt virus có báo sai không

**Q: Thông báo không đủ quyền?**
A: Chạy chương trình với quyền quản trị viên

**Q: Sau khi dọn dẹp vẫn không thể chuyển tài khoản?**
A: Đảm bảo đã đóng hoàn toàn IDE, và khởi động lại trước khi đăng nhập

**Q: Làm thế nào để khôi phục cài đặt gốc?**
A: Khôi phục file tương ứng từ thư mục backup

## 📞 Hỗ trợ kỹ thuật

Nếu có vấn đề, vui lòng xem log thao tác trong chương trình, hoặc kiểm tra file trong thư mục backup.

---

**Lưu ý**: Công cụ này chỉ dùng cho mục đích học tập và nghiên cứu, vui lòng tuân thủ các điều khoản sử dụng của phần mềm liên quan.
"""
    
    with open("README_EXE.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ Đã tạo hướng dẫn sử dụng: README_EXE.md")

def main():
    """Hàm chính"""
    print("🔨 Công cụ xây dựng Augment Cleaner Unified")
    print("=" * 50)
    
    # Kiểm tra PyInstaller
    if not check_pyinstaller():
        if not install_pyinstaller():
            print("❌ Không thể cài đặt PyInstaller, xây dựng thất bại")
            return False
    
    # Tạo icon
    create_icon()
    
    # Xây dựng file thực thi
    if not build_executable():
        print("❌ Xây dựng thất bại")
        return False
    
    # Tạo file hướng dẫn
    create_readme()
    
    print("\n" + "=" * 50)
    print("🎉 Xây dựng hoàn tất!")
    print("\n📦 File đầu ra:")
    print("   - dist/AugmentCleanerUnified.exe  (Chương trình chính)")
    print("   - README_EXE.md                   (Hướng dẫn sử dụng)")
    print("\n🚀 Cách sử dụng:")
    print("   Chạy trực tiếp: Nhấp đúp AugmentCleanerUnified.exe")
    
    return True

if __name__ == "__main__":
    main()
