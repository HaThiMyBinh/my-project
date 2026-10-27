# -*- coding: utf-8 -*-
"""Nạp biến môi trường từ file .env (nếu có).

Import module này TRƯỚC khi đọc os.getenv ở các module khác.
Thứ tự ưu tiên: biến môi trường hệ thống > .env ở thư mục gốc > backend/.env
"""
import os

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv chưa cài: bỏ qua, vẫn đọc được biến hệ thống
    load_dotenv = None

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)

if load_dotenv:
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
    load_dotenv(os.path.join(BACKEND_DIR, ".env"))
