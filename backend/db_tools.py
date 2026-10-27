# -*- coding: utf-8 -*-
"""Sao lưu / khôi phục CSDL SQLite của PetCare Spa (chỉ dùng thư viện chuẩn).

Dùng:
    python backend/db_tools.py backup                 # tạo bản sao lưu có dấu thời gian trong thư mục backups/
    python backend/db_tools.py list                   # liệt kê các bản sao lưu
    python backend/db_tools.py verify <file>          # kiểm tra tính toàn vẹn một bản sao lưu
    python backend/db_tools.py restore <file> --yes   # khôi phục (tự sao lưu bản hiện tại trước)
    python backend/db_tools.py backup --keep 10       # giữ 10 bản mới nhất

Đường dẫn CSDL: biến môi trường DATABASE_PATH (mặc định <thư mục gốc>/petcare.db).
Thư mục sao lưu: BACKUP_DIR (mặc định <thư mục gốc>/backups).
Nên DỪNG ứng dụng trước khi khôi phục.
"""
import argparse
import glob
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from typing import List, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.getenv("DATABASE_PATH", os.path.join(ROOT_DIR, "petcare.db"))
DEFAULT_BACKUP_DIR = os.getenv("BACKUP_DIR", os.path.join(ROOT_DIR, "backups"))


class BackupError(Exception):
    pass


def verify(path: str) -> None:
    """Raise BackupError nếu file không phải SQLite hợp lệ hoặc hỏng/mất nhất quán khóa ngoại."""
    if not os.path.isfile(path):
        raise BackupError(f"Không tìm thấy file: {path}")
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise BackupError(f"integrity_check thất bại: {result}")
            bad = conn.execute("PRAGMA foreign_key_check").fetchall()
            if bad:
                raise BackupError(f"Có {len(bad)} bản ghi vi phạm khóa ngoại")
            tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            if tables == 0:
                raise BackupError("CSDL rỗng (không có bảng nào)")
        finally:
            conn.close()
    except sqlite3.DatabaseError as e:
        raise BackupError(f"Không phải CSDL SQLite hợp lệ: {e}") from None


def _copy(src_path: str, dst_path: str) -> None:
    """Sao chép an toàn bằng SQLite backup API (nhất quán ngay cả khi ứng dụng đang ghi)."""
    src = sqlite3.connect(src_path)
    dst = sqlite3.connect(dst_path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def backup(db_path: str = DEFAULT_DB, backup_dir: str = DEFAULT_BACKUP_DIR, tag: str = "petcare") -> str:
    if not os.path.isfile(db_path):
        raise BackupError(f"Không tìm thấy CSDL: {db_path}")
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out = os.path.join(backup_dir, f"{tag}_{stamp}.db")
    _copy(db_path, out)
    verify(out)
    return out


def list_backups(backup_dir: str = DEFAULT_BACKUP_DIR) -> List[str]:
    return sorted(glob.glob(os.path.join(backup_dir, "*.db")))


def prune(keep: int, backup_dir: str = DEFAULT_BACKUP_DIR) -> List[str]:
    files = list_backups(backup_dir)
    removed = files[:-keep] if keep > 0 else []
    for f in removed:
        os.remove(f)
    return removed


def restore(backup_path: str, db_path: str = DEFAULT_DB, backup_dir: str = DEFAULT_BACKUP_DIR) -> Optional[str]:
    """Khôi phục. Trả về đường dẫn bản sao lưu an toàn của CSDL hiện tại (nếu có)."""
    verify(backup_path)                                    # không bao giờ ghi đè bằng file hỏng
    safety = None
    if os.path.isfile(db_path):
        safety = backup(db_path, backup_dir, tag="before_restore")
    tmp = db_path + ".restoring"
    _copy(backup_path, tmp)
    verify(tmp)
    for suffix in ("-wal", "-shm"):                        # xóa file phụ của CSDL cũ
        if os.path.exists(db_path + suffix):
            os.remove(db_path + suffix)
    os.replace(tmp, db_path)
    return safety


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Sao lưu/khôi phục CSDL PetCare Spa")
    p.add_argument("command", choices=["backup", "list", "verify", "restore"])
    p.add_argument("file", nargs="?")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--out", default=DEFAULT_BACKUP_DIR)
    p.add_argument("--keep", type=int, default=0, help="chỉ giữ N bản sao lưu mới nhất")
    p.add_argument("--yes", action="store_true", help="xác nhận khôi phục")
    a = p.parse_args(argv)
    try:
        if a.command == "backup":
            print("Đã sao lưu:", backup(a.db, a.out))
            if a.keep:
                for f in prune(a.keep, a.out):
                    print("Đã xóa bản cũ:", f)
        elif a.command == "list":
            files = list_backups(a.out)
            print("\n".join(files) if files else "(chưa có bản sao lưu)")
        elif a.command == "verify":
            if not a.file:
                p.error("cần chỉ định file")
            verify(a.file)
            print("Bản sao lưu hợp lệ:", a.file)
        elif a.command == "restore":
            if not a.file:
                p.error("cần chỉ định file")
            if not a.yes:
                print("Khôi phục sẽ GHI ĐÈ CSDL hiện tại. Chạy lại với --yes để xác nhận.")
                return 2
            safety = restore(a.file, a.db, a.out)
            print("Đã khôi phục từ:", a.file)
            if safety:
                print("Bản sao lưu CSDL trước khi khôi phục:", safety)
    except BackupError as e:
        print("LỖI:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
