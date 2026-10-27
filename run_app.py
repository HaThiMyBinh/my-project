# -*- coding: utf-8 -*-
import os, sys, webbrowser, time
import uvicorn

if __name__ == "__main__":
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    sys.path.insert(0, app_dir)
    
    print("=========================================================")
    print(" KHỞI CHẠY HỆ THỐNG PETCARE SPA MANAGEMENT (NHÓM 6)")
    print(" Sinh viên: Hà Thị Mỹ Bình & Nguyễn Thị Giang")
    print(" API Backend: http://127.0.0.1:8000/docs")
    print(" Giao diện Web: http://127.0.0.1:8000/app/index.html")
    print("=========================================================")
    
    # Auto open browser
    time.sleep(1)
    try:
        webbrowser.open("http://127.0.0.1:8000/app/index.html")
    except Exception:
        pass
        
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=app_dir)
