#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务栏图标显示
"""

import tkinter as tk
import os
import sys
import ctypes

class TestWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("任务栏图标测试")
        self.root.geometry("400x200+100+100")

        # 设置应用程序ID（Windows任务栏需要）
        try:
            myappid = 'ScheduleWidget.Test.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            print(f"✓ 应用程序ID设置成功: {myappid}")
        except Exception as e:
            print(f"✗ 设置应用程序ID失败: {e}")

        # 加载图标
        try:
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(application_path, 'icon.ico')

            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                self.root.wm_iconbitmap(icon_path)
                print(f"✓ 图标加载成功: {icon_path}")
            else:
                print(f"✗ 图标文件不存在: {icon_path}")
        except Exception as e:
            print(f"✗ 加载图标失败: {e}")

        # UI
        tk.Label(
            self.root,
            text="任务栏图标测试窗口",
            font=("微软雅黑", 16)
        ).pack(pady=20)

        tk.Label(
            self.root,
            text="检查任务栏是否正确显示图标",
            font=("微软雅黑", 12)
        ).pack(pady=10)

        tk.Button(
            self.root,
            text="关闭",
            command=self.root.quit,
            font=("微软雅黑", 12)
        ).pack(pady=20)

        self.root.mainloop()

if __name__ == "__main__":
    print("=" * 50)
    print("任务栏图标测试")
    print("=" * 50)
    TestWindow()
