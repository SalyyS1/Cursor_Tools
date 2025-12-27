#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm tra và tự động cài đặt dependencies
"""

import sys
import subprocess
import importlib
import os
from pathlib import Path

def check_python_version():
    """Kiểm tra phiên bản Python"""
    if sys.version_info < (3, 8):
        print("❌ Phiên bản Python quá thấp, cần Python 3.8 hoặc cao hơn")
        print(f"   Phiên bản hiện tại: {sys.version}")
        return False
    print(f"✅ Kiểm tra phiên bản Python thành công: {sys.version.split()[0]}")
    return True

def install_package(package_name, use_mirror=False):
    """Cài đặt package Python"""
    try:
        if use_mirror:
            cmd = [sys.executable, "-m", "pip", "install", package_name, 
                   "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/"]
        else:
            cmd = [sys.executable, "-m", "pip", "install", package_name]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"   Cài đặt thất bại: {e}")
        return False

def check_and_install_package(package_name, import_name=None):
    """Kiểm tra và cài đặt package"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} đã được cài đặt")
        return True
    except ImportError:
        print(f"⚠️ {package_name} chưa được cài đặt, đang cài đặt...")
        
        # Thử cài đặt bình thường trước
        if install_package(package_name):
            print(f"✅ {package_name} cài đặt thành công")
            return True
        
        # Nếu thất bại, thử dùng mirror nội địa
        print(f"   Đang thử dùng mirror nội địa...")
        if install_package(package_name, use_mirror=True):
            print(f"✅ {package_name} cài đặt thành công (dùng mirror)")
            return True
        
        print(f"❌ {package_name} cài đặt thất bại")
        return False

def install_from_requirements():
    """Cài đặt dependencies từ requirements.txt"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        return False
    
    print("📦 Đang cài đặt dependencies từ requirements.txt...")
    try:
        # Thử cài đặt bình thường trước
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Cài đặt dependencies từ requirements.txt thành công")
            return True
        
        # Nếu thất bại, thử dùng mirror nội địa
        print("   Đang thử dùng mirror nội địa...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
               "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Cài đặt dependencies từ requirements.txt thành công (dùng mirror)")
            return True
        
        print("❌ Cài đặt dependencies từ requirements.txt thất bại")
        print(f"   Thông tin lỗi: {result.stderr}")
        return False
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình cài đặt: {e}")
        return False

def main():
    """Hàm chính"""
    print("🔍 Đang kiểm tra môi trường Python và dependencies...")
    print()
    
    # Kiểm tra phiên bản Python
    if not check_python_version():
        return False
    
    print()
    
    # Danh sách dependencies cốt lõi
    core_dependencies = [
        ("psutil", "psutil"),  # (tên package, tên import)
    ]
    
    # Kiểm tra xem có requirements.txt không
    if Path("requirements.txt").exists():
        print("📋 Đã phát hiện file requirements.txt")
        if install_from_requirements():
            print()
            print("✅ Tất cả dependencies đã được cài đặt")
            return True
    
    # Kiểm tra từng dependency cốt lõi
    print("📦 Đang kiểm tra dependencies cốt lõi...")
    all_success = True
    
    for package_name, import_name in core_dependencies:
        if not check_and_install_package(package_name, import_name):
            all_success = False
    
    print()
    
    if all_success:
        print("✅ Tất cả dependencies đã được kiểm tra")
        return True
    else:
        print("❌ Một số dependencies cài đặt thất bại")
        print()
        print("Lệnh cài đặt thủ công:")
        for package_name, _ in core_dependencies:
            print(f"   pip install {package_name}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nNhấn Enter để thoát...")
        sys.exit(1)
