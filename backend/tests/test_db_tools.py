# -*- coding: utf-8 -*-
"""Test sao lưu/khôi phục CSDL (thuần sqlite3, không cần FastAPI)."""
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_tools  # noqa: E402


def make_db(path, rows=("a", "b")):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE owners (id INTEGER PRIMARY KEY, name TEXT)")
    conn.executemany("INSERT INTO owners(name) VALUES (?)", [(r,) for r in rows])
    conn.commit()
    conn.close()


def names(path):
    conn = sqlite3.connect(path)
    try:
        return [r[0] for r in conn.execute("SELECT name FROM owners ORDER BY id")]
    finally:
        conn.close()


def test_backup_creates_valid_copy():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "petcare.db")
        make_db(db)
        out = db_tools.backup(db, os.path.join(d, "bk"))
        assert os.path.isfile(out) and names(out) == ["a", "b"]
        db_tools.verify(out)
        assert db_tools.list_backups(os.path.join(d, "bk")) == [out]


def test_restore_roundtrip_and_safety_backup():
    with tempfile.TemporaryDirectory() as d:
        db, bk = os.path.join(d, "petcare.db"), os.path.join(d, "bk")
        make_db(db, ("a", "b"))
        good = db_tools.backup(db, bk)
        conn = sqlite3.connect(db)                       # "sự cố": xóa dữ liệu
        conn.execute("DELETE FROM owners")
        conn.commit()
        conn.close()
        assert names(db) == []
        safety = db_tools.restore(good, db, bk)
        assert names(db) == ["a", "b"]                   # dữ liệu đã quay lại
        assert safety and names(safety) == []            # bản trước khi khôi phục vẫn được giữ lại


def test_restore_refuses_corrupt_or_missing_backup_and_keeps_current_db():
    with tempfile.TemporaryDirectory() as d:
        db, bk = os.path.join(d, "petcare.db"), os.path.join(d, "bk")
        make_db(db)
        bad = os.path.join(d, "bad.db")
        with open(bad, "wb") as f:
            f.write(b"this is not a sqlite database" * 50)
        for target in (bad, os.path.join(d, "missing.db")):
            try:
                db_tools.restore(target, db, bk)
            except db_tools.BackupError:
                pass
            else:
                raise AssertionError("phải từ chối bản sao lưu hỏng/thiếu")
        assert names(db) == ["a", "b"]                   # CSDL hiện tại không bị đụng tới


def test_verify_detects_foreign_key_violation():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.db")
        conn = sqlite3.connect(p)
        conn.executescript("CREATE TABLE p(id INTEGER PRIMARY KEY); CREATE TABLE c(id INTEGER PRIMARY KEY, pid INTEGER REFERENCES p(id));"
                           "INSERT INTO c(pid) VALUES (999);")
        conn.commit()
        conn.close()
        try:
            db_tools.verify(p)
        except db_tools.BackupError:
            return
        raise AssertionError("phải phát hiện vi phạm khóa ngoại")


def test_prune_keeps_newest():
    with tempfile.TemporaryDirectory() as d:
        db, bk = os.path.join(d, "petcare.db"), os.path.join(d, "bk")
        make_db(db)
        made = [db_tools.backup(db, bk) for _ in range(4)]
        removed = db_tools.prune(2, bk)
        assert len(removed) == 2 and db_tools.list_backups(bk) == sorted(made)[-2:]


def test_cli_backup_restore_requires_confirmation():
    with tempfile.TemporaryDirectory() as d:
        db, bk = os.path.join(d, "petcare.db"), os.path.join(d, "bk")
        make_db(db)
        assert db_tools.main(["backup", "--db", db, "--out", bk]) == 0
        f = db_tools.list_backups(bk)[0]
        assert db_tools.main(["restore", f, "--db", db, "--out", bk]) == 2            # thiếu --yes
        assert db_tools.main(["restore", f, "--db", db, "--out", bk, "--yes"]) == 0
        assert db_tools.main(["verify", os.path.join(d, "nope.db")]) == 1
