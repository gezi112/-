#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面课表小工具
功能：
1. 显示当天课程表
2. 显示距离下一节课的倒计时
3. 显示上课时间
4. 支持自定义课表（JSON格式）
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox, Menu
from datetime import datetime, timedelta
import os
import sys


class ScheduleWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("今日课表")
        self.root.geometry("320x400+100+100")

        # 设置应用程序ID，确保任务栏显示正确（Windows）
        try:
            import ctypes
            myappid = 'ScheduleWidget.App.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

        # 窗口设置
        # 置顶设置将在load_settings中应用，这里先不设置
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes('-alpha', 0.95)  # 透明度

        # 加载图标（用于任务栏显示）
        self.load_window_icon()

        # 拖动相关
        self.drag_data = {"x": 0, "y": 0}

        # 调整大小相关
        self.resize_data = {"x": 0, "y": 0, "width": 0, "height": 0, "resizing": False}
        self.resize_border = 8  # 边缘检测宽度

        # 颜色配置
        self.colors = {
            "bg": "#2c3e50",
            "header_bg": "#34495e",
            "current": "#27ae60",  # 正在上课
            "next": "#f39c12",     # 下一节课
            "normal": "#ecf0f1",   # 普通课程
            "passed": "#7f8c8d",   # 已结束
            "accent": "#3498db"
        }

        self.root.configure(bg=self.colors["bg"])

        # 课表数据
        self.schedule_data = {}
        self.schedule_file = "schedule.json"
        self.settings_file = "settings.json"

        # 设置数据
        self.settings = {
            "topmost": True,
            "background_image": "",
            "course_font_color": "#ecf0f1",
            "countdown_font_color": "#f39c12",
            "font_outline": False,
            "outline_color": "#000000"
        }
        self.load_settings()

        # 背景图片
        self.bg_image = None
        self.bg_label = None

        self.create_ui()
        self.load_schedule()
        self.update_display()

        # 每分钟更新一次
        self.update_interval = 60000
        self.schedule_next_update()

    def load_window_icon(self):
        """加载窗口图标（用于任务栏显示）"""
        try:
            # 获取程序运行路径
            if getattr(sys, 'frozen', False):
                # PyInstaller打包后的exe模式
                application_path = sys._MEIPASS
            else:
                # 脚本模式
                application_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(application_path, 'icon.ico')

            # 尝试多种方式加载图标
            if os.path.exists(icon_path):
                # 方法1: 直接使用iconbitmap
                self.root.iconbitmap(icon_path)

                # 方法2: 使用wm_iconbitmap确保任务栏显示
                self.root.wm_iconbitmap(icon_path)

                print(f"✓ 图标加载成功: {icon_path}")
            else:
                print(f"⚠ 图标文件不存在: {icon_path}")
        except Exception as e:
            print(f"⚠ 加载图标失败: {e}")

    def create_ui(self):
        """创建UI界面"""
        # 创建背景标签（在最底层）
        self.bg_label = tk.Label(self.root)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # 应用背景图片
        self.apply_background()

        # 创建主内容框架
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_frame.place(x=0, y=0, relwidth=1, relheight=1)

        # 标题栏（可拖动）
        self.header = tk.Frame(self.main_frame, bg=self.colors["header_bg"], height=35)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        # 标题文字
        self.title_label = tk.Label(
            self.header,
            text="📚 今日课表",
            bg=self.colors["header_bg"],
            fg="white",
            font=("微软雅黑", 12, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 日期显示
        self.date_label = tk.Label(
            self.header,
            text="",
            bg=self.colors["header_bg"],
            fg="#bdc3c7",
            font=("微软雅黑", 9)
        )
        self.date_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # 控制按钮区域
        self.control_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)

        # 导入按钮
        self.import_btn = tk.Button(
            self.control_frame,
            text="📁 导入课表",
            command=self.import_schedule,
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9),
            cursor="hand2"
        )
        self.import_btn.pack(side=tk.LEFT, padx=2)

        # 查看完整课表按钮
        self.full_schedule_btn = tk.Button(
            self.control_frame,
            text="📋 完整课表",
            command=self.show_full_schedule,
            bg=self.colors["header_bg"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9),
            cursor="hand2"
        )
        self.full_schedule_btn.pack(side=tk.LEFT, padx=2)

        # 设置按钮
        self.settings_btn = tk.Button(
            self.control_frame,
            text="⚙ 设置",
            command=self.show_settings,
            bg=self.colors["header_bg"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9),
            cursor="hand2"
        )
        self.settings_btn.pack(side=tk.LEFT, padx=2)

        # 最小化按钮
        self.minimize_btn = tk.Button(
            self.control_frame,
            text="—",
            command=self.minimize_window,
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9, "bold"),
            width=3,
            cursor="hand2"
        )
        self.minimize_btn.pack(side=tk.RIGHT, padx=2)

        # 关闭按钮
        self.close_btn = tk.Button(
            self.control_frame,
            text="✕",
            command=self.root.quit,
            bg="#e74c3c",
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9, "bold"),
            width=3,
            cursor="hand2"
        )
        self.close_btn.pack(side=tk.RIGHT, padx=2)

        # 倒计时区域
        self.countdown_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        self.countdown_frame.pack(fill=tk.X, padx=10, pady=10)

        self.countdown_label = tk.Label(
            self.countdown_frame,
            text="加载中...",
            bg=self.colors["bg"],
            fg=self.colors["next"],
            font=("微软雅黑", 14, "bold")
        )
        self.countdown_label.pack()

        # 课程列表区域
        self.canvas = tk.Canvas(self.main_frame, bg=self.colors["bg"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors["bg"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # 在scrollable_frame上也绑定调整大小事件
        self.scrollable_frame.bind("<Button-1>", self.on_border_click)
        self.scrollable_frame.bind("<B1-Motion>", self.on_border_drag)
        self.scrollable_frame.bind("<ButtonRelease-1>", self.on_border_release)
        self.scrollable_frame.bind("<Motion>", self.on_mouse_move)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW, width=300)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 绑定canvas尺寸变化事件
        self.canvas.bind('<Configure>', self.on_canvas_resize)

        # 在canvas上也绑定调整大小事件，避免底部边缘被canvas阻挡
        self.canvas.bind("<Button-1>", self.on_border_click)
        self.canvas.bind("<B1-Motion>", self.on_border_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_border_release)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 在滚动条上也绑定调整大小事件，避免右侧边缘被滚动条阻挡
        self.scrollbar.bind("<Button-1>", self.on_border_click)
        self.scrollbar.bind("<B1-Motion>", self.on_border_drag)
        self.scrollbar.bind("<ButtonRelease-1>", self.on_border_release)
        self.scrollbar.bind("<Motion>", self.on_mouse_move)

        # 绑定拖动事件
        self.header.bind("<Button-1>", self.on_drag_start)
        self.header.bind("<B1-Motion>", self.on_drag_motion)
        self.title_label.bind("<Button-1>", self.on_drag_start)
        self.title_label.bind("<B1-Motion>", self.on_drag_motion)

        # 右键菜单
        self.root.bind("<Button-3>", self.show_context_menu)

        # 绑定调整大小事件
        self.root.bind("<Button-1>", self.on_border_click)
        self.root.bind("<B1-Motion>", self.on_border_drag)
        self.root.bind("<ButtonRelease-1>", self.on_border_release)
        self.root.bind("<Motion>", self.on_mouse_move)

        # 绑定窗口大小改变事件（用于更新背景图片）
        self.root.bind("<Configure>", self.on_window_resize)

    def on_drag_start(self, event):
        """开始拖动"""
        # 如果正在调整大小，不执行拖动
        if self.resize_data.get("resizing"):
            return
        self.drag_data["x"] = event.x_root - self.root.winfo_x()
        self.drag_data["y"] = event.y_root - self.root.winfo_y()

    def on_drag_motion(self, event):
        """拖动中"""
        # 如果正在调整大小，不执行拖动
        if self.resize_data.get("resizing"):
            return
        x = event.x_root - self.drag_data["x"]
        y = event.y_root - self.drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def get_resize_direction(self, event):
        """判断鼠标位置是否在调整大小的边缘区域"""
        # 将鼠标坐标转换为相对于root窗口的坐标
        x = event.x_root - self.root.winfo_x()
        y = event.y_root - self.root.winfo_y()

        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # 四个角的调整区域（20x20）
        # 左上角
        if x <= 20 and y <= 20:
            return "nw"
        # 右上角
        elif x >= width - 20 and y <= 20:
            return "ne"
        # 左下角
        elif x <= 20 and y >= height - 20:
            return "sw"
        # 右下角
        elif x >= width - 20 and y >= height - 20:
            return "se"
        # 左侧边缘
        elif x <= self.resize_border:
            return "w"
        # 右侧边缘
        elif x >= width - self.resize_border:
            return "e"
        # 顶部边缘（排除标题栏区域）
        elif y <= self.resize_border and y > 35:  # 35是标题栏高度
            return "n"
        # 底部边缘
        elif y >= height - self.resize_border:
            return "s"
        return None

    def on_mouse_move(self, event):
        """鼠标移动时改变光标样式"""
        # 如果在头部区域拖动窗口，不改变光标
        if event.widget in [self.header, self.title_label]:
            self.root.config(cursor="")
            return

        direction = self.get_resize_direction(event)

        if direction in ["nw", "se"]:
            self.root.config(cursor="size_nw_se")
        elif direction in ["ne", "sw"]:
            self.root.config(cursor="size_ne_sw")
        elif direction in ["e", "w"]:
            self.root.config(cursor="size_we")
        elif direction in ["n", "s"]:
            self.root.config(cursor="size_ns")
        else:
            self.root.config(cursor="")

    def on_border_click(self, event):
        """在边缘点击时开始调整大小"""
        direction = self.get_resize_direction(event)

        if direction:
            self.resize_data["resizing"] = True
            self.resize_data["direction"] = direction
            self.resize_data["x"] = event.x_root
            self.resize_data["y"] = event.y_root
            # 保存当前窗口位置（用于左上调整时计算新位置）
            self.resize_data["win_x"] = self.root.winfo_x()
            self.resize_data["win_y"] = self.root.winfo_y()
            self.resize_data["width"] = self.root.winfo_width()
            self.resize_data["height"] = self.root.winfo_height()

    def on_border_drag(self, event):
        """拖动调整窗口大小"""
        if not self.resize_data.get("resizing"):
            return

        dx = event.x_root - self.resize_data["x"]
        dy = event.y_root - self.resize_data["y"]

        new_width = self.resize_data["width"]
        new_height = self.resize_data["height"]
        new_x = self.root.winfo_x()
        new_y = self.root.winfo_y()

        direction = self.resize_data.get("direction", "")

        # 右侧调整宽度
        if "e" in direction:
            new_width = max(200, self.resize_data["width"] + dx)
        # 左侧调整宽度和位置
        if "w" in direction:
            new_width = max(200, self.resize_data["width"] - dx)
            if new_width > 200:
                new_x = self.resize_data["win_x"] + (self.resize_data["width"] - new_width)

        # 底部调整高度
        if "s" in direction:
            new_height = max(150, self.resize_data["height"] + dy)
        # 顶部调整高度和位置
        if "n" in direction:
            new_height = max(150, self.resize_data["height"] - dy)
            if new_height > 150:
                new_y = self.resize_data["win_y"] + (self.resize_data["height"] - new_height)

        # 更新窗口大小和位置
        self.root.geometry(f"{int(new_width)}x{int(new_height)}+{int(new_x)}+{int(new_y)}")

    def on_border_release(self, event):
        """鼠标释放时结束调整大小"""
        self.resize_data["resizing"] = False
        self.resize_data["direction"] = None

    def on_canvas_resize(self, event):
        """Canvas尺寸变化时调整内部frame的宽度"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def create_outlined_label(self, parent, text, font_size, font_weight="normal", is_countdown=False):
        """创建带描边的文字标签

        Args:
            parent: 父容器
            text: 文字内容
            font_size: 字体大小
            font_weight: 字体粗细 (normal/bold)
            is_countdown: 是否是倒计时标签
        """
        from PIL import Image, ImageDraw, ImageFont, ImageTk

        # 获取颜色设置
        if is_countdown:
            fg_color = self.settings.get("countdown_font_color", "#f39c12")
        else:
            fg_color = self.settings.get("course_font_color", "#ecf0f1")

        outline_enabled = self.settings.get("font_outline", False)
        outline_color = self.settings.get("outline_color", "#000000")

        # 如果不启用描边，使用普通标签
        if not outline_enabled:
            return tk.Label(
                parent,
                text=text,
                bg=self.colors["bg"],
                fg=fg_color,
                font=("微软雅黑", font_size, font_weight)
            )

        # 使用PIL创建带描边的文字图片
        try:
            # 尝试使用微软雅黑字体
            font = ImageFont.truetype("msyh.ttc", font_size * 2)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size * 2)
            except:
                font = ImageFont.load_default()

        # 计算文字尺寸
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 添加描边边距
        outline_width = 2
        padding = outline_width + 2
        img_width = text_width + padding * 2
        img_height = text_height + padding * 2

        # 创建图片
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 绘制描边
        fg_rgb = tuple(int(fg_color[i:i+2], 16) for i in (1, 3, 5))
        outline_rgb = tuple(int(outline_color[i:i+2], 16) for i in (1, 3, 5))

        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((padding + dx, padding + dy), text, font=font, fill=outline_rgb + (255,))

        # 绘制主文字
        draw.text((padding, padding), text, font=font, fill=fg_rgb + (255,))

        # 转换为PhotoImage
        photo = ImageTk.PhotoImage(img)

        # 创建标签
        label = tk.Label(parent, image=photo, bg=self.colors["bg"])
        label.image = photo  # 保持引用
        label.text_content = text  # 保存文字内容便于更新
        label.is_countdown = is_countdown
        label.font_size = font_size
        label.font_weight = font_weight

        return label

    def update_label_text(self, label, text):
        """更新带描边标签的文字"""
        if hasattr(label, 'text_content'):
            # 这是带描边的标签，需要重新创建
            is_countdown = getattr(label, 'is_countdown', False)
            font_size = getattr(label, 'font_size', 10)
            font_weight = getattr(label, 'font_weight', 'normal')
            parent = label.master
            label.destroy()
            return self.create_outlined_label(parent, text, font_size, font_weight, is_countdown)
        else:
            # 普通标签
            label.config(text=text)
            return label

    def show_context_menu(self, event):
        """显示右键菜单"""
        menu = Menu(self.root, tearoff=0, bg=self.colors["bg"], fg="white")
        menu.add_command(label="完整课表", command=self.show_full_schedule)
        menu.add_command(label="设置", command=self.show_settings)
        menu.add_separator()
        menu.add_command(label="置顶/取消置顶", command=self.toggle_topmost)
        menu.add_command(label="导入课表", command=self.import_schedule)
        menu.add_separator()
        menu.add_command(label="退出", command=self.root.quit)
        menu.post(event.x_root, event.y_root)

    def toggle_topmost(self):
        """切换置顶状态"""
        current = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current)

    def minimize_window(self):
        """最小化窗口"""
        self.root.iconify()

    def show_full_schedule(self):
        """显示完整课表窗口"""
        # 创建新窗口
        full_window = tk.Toplevel(self.root)
        full_window.title("完整课表")
        full_window.geometry("800x600+200+100")
        full_window.configure(bg=self.colors["bg"])
        full_window.attributes('-topmost', True)

        # 标题
        title_label = tk.Label(
            full_window,
            text="📚 本周完整课表",
            bg=self.colors["bg"],
            fg="white",
            font=("微软雅黑", 16, "bold")
        )
        title_label.pack(pady=10)

        # 创建带滚动条的框架
        main_frame = tk.Frame(full_window, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(main_frame, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors["bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW, width=780)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定canvas尺寸变化
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))

        # 绑定滚轮事件到canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # 在canvas和scrollable_frame上绑定滚轮事件
        canvas.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 星期名称
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        def refresh_schedule():
            """刷新课表显示"""
            # 清空所有子组件
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            # 重新创建课表显示
            create_schedule_widgets()
            # 保存课表
            self.save_schedule()
            # 更新主窗口显示
            self.update_display()

        def create_schedule_widgets():
            """创建课表组件"""
            # 为每一天创建课程列表
            for day_num, day_name in enumerate(weekdays, 1):
                day_frame = tk.Frame(scrollable_frame, bg=self.colors["header_bg"], padx=10, pady=8)
                day_frame.pack(fill=tk.X, pady=5)

                # 在day_frame上绑定滚轮事件
                day_frame.bind("<MouseWheel>", on_mousewheel)

                # 星期标题和添加按钮
                header_frame = tk.Frame(day_frame, bg=self.colors["header_bg"])
                header_frame.pack(fill=tk.X)
                header_frame.bind("<MouseWheel>", on_mousewheel)

                day_title = tk.Label(
                    header_frame,
                    text=f"{day_name}",
                    bg=self.colors["header_bg"],
                    fg=self.colors["accent"],
                    font=("微软雅黑", 12, "bold"),
                    anchor=tk.W
                )
                day_title.pack(side=tk.LEFT)
                day_title.bind("<MouseWheel>", on_mousewheel)

                # 添加课程按钮
                add_btn = tk.Button(
                    header_frame,
                    text="➕ 添加",
                    command=lambda d=day_num: self.edit_course_window(full_window, d, None, refresh_schedule),
                    bg=self.colors["current"],
                    fg="white",
                    relief=tk.FLAT,
                    font=("微软雅黑", 8),
                    cursor="hand2"
                )
                add_btn.pack(side=tk.RIGHT)

                # 获取该天的课程
                courses = self.schedule_data.get(str(day_num), [])

                if courses:
                    # 按开始时间排序
                    courses_sorted = sorted(courses, key=lambda x: x.get('start', '00:00'))

                    for idx, course in enumerate(courses_sorted):
                        course_frame = tk.Frame(day_frame, bg=self.colors["bg"], padx=5, pady=5)
                        course_frame.pack(fill=tk.X, pady=2)
                        course_frame.bind("<MouseWheel>", on_mousewheel)

                        # 课程信息
                        info_frame = tk.Frame(course_frame, bg=self.colors["bg"])
                        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                        info_frame.bind("<MouseWheel>", on_mousewheel)

                        info_text = f"  {course['name']}  |  🕐 {course['start']} - {course['end']}  |  📍 {course['room']}"
                        course_label = tk.Label(
                            info_frame,
                            text=info_text,
                            bg=self.colors["bg"],
                            fg=self.colors["normal"],
                            font=("微软雅黑", 10),
                            anchor=tk.W
                        )
                        course_label.pack(fill=tk.X)
                        course_label.bind("<MouseWheel>", on_mousewheel)

                        # 操作按钮
                        btn_frame = tk.Frame(course_frame, bg=self.colors["bg"])
                        btn_frame.pack(side=tk.RIGHT)

                        edit_btn = tk.Button(
                            btn_frame,
                            text="编辑",
                            command=lambda d=day_num, c=course, i=idx: self.edit_course_window(full_window, d, c, refresh_schedule, i),
                            bg=self.colors["accent"],
                            fg="white",
                            relief=tk.FLAT,
                            font=("微软雅黑", 8),
                            cursor="hand2",
                            width=4,
                            height=1
                        )
                        edit_btn.pack(side=tk.LEFT, padx=2)

                        del_btn = tk.Button(
                            btn_frame,
                            text="删除",
                            command=lambda d=day_num, i=idx: self.delete_course(d, i, refresh_schedule),
                            bg="#e74c3c",
                            fg="white",
                            relief=tk.FLAT,
                            font=("微软雅黑", 8),
                            cursor="hand2",
                            width=4,
                            height=1
                        )
                        del_btn.pack(side=tk.LEFT, padx=2)
                else:
                    # 无课程提示
                    no_course_label = tk.Label(
                        day_frame,
                        text="  无课程",
                        bg=self.colors["bg"],
                        fg=self.colors["passed"],
                        font=("微软雅黑", 10, "italic"),
                        anchor=tk.W
                    )
                    no_course_label.pack(fill=tk.X, pady=2)
                    no_course_label.bind("<MouseWheel>", on_mousewheel)

        create_schedule_widgets()

        # 在标题和主框架上也绑定滚轮事件
        title_label.bind("<MouseWheel>", on_mousewheel)
        main_frame.bind("<MouseWheel>", on_mousewheel)

        # 关闭按钮
        close_btn = tk.Button(
            full_window,
            text="关闭",
            command=full_window.destroy,
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 10),
            cursor="hand2"
        )
        close_btn.pack(pady=10)

    def delete_course(self, day_num, course_index, refresh_callback):
        """删除课程"""
        if messagebox.askyesno("确认删除", "确定要删除这门课程吗？"):
            day_key = str(day_num)
            if day_key in self.schedule_data and 0 <= course_index < len(self.schedule_data[day_key]):
                del self.schedule_data[day_key][course_index]
                self.save_schedule()
                refresh_callback()
                self.update_display()

    def edit_course_window(self, parent, day_num, course, refresh_callback, course_index=None):
        """编辑/添加课程窗口"""
        is_edit = course is not None
        title = "编辑课程" if is_edit else "添加课程"

        edit_win = tk.Toplevel(parent)
        edit_win.title(title)
        edit_win.geometry("350x280+400+300")
        edit_win.configure(bg=self.colors["bg"])
        edit_win.transient(parent)
        edit_win.grab_set()

        # 标题
        tk.Label(
            edit_win,
            text=title,
            bg=self.colors["bg"],
            fg="white",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=15)

        # 课程名称
        name_frame = tk.Frame(edit_win, bg=self.colors["bg"])
        name_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(name_frame, text="课程名称:", bg=self.colors["bg"], fg="white", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        name_var = tk.StringVar(value=course["name"] if is_edit else "")
        name_entry = tk.Entry(name_frame, textvariable=name_var, font=("微软雅黑", 10))
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 教室
        room_frame = tk.Frame(edit_win, bg=self.colors["bg"])
        room_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(room_frame, text="教室:", bg=self.colors["bg"], fg="white", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        room_var = tk.StringVar(value=course["room"] if is_edit else "")
        room_entry = tk.Entry(room_frame, textvariable=room_var, font=("微软雅黑", 10))
        room_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 开始时间
        start_frame = tk.Frame(edit_win, bg=self.colors["bg"])
        start_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(start_frame, text="开始时间:", bg=self.colors["bg"], fg="white", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        start_var = tk.StringVar(value=course["start"] if is_edit else "08:00")
        start_entry = tk.Entry(start_frame, textvariable=start_var, font=("微软雅黑", 10))
        start_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 结束时间
        end_frame = tk.Frame(edit_win, bg=self.colors["bg"])
        end_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(end_frame, text="结束时间:", bg=self.colors["bg"], fg="white", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        end_var = tk.StringVar(value=course["end"] if is_edit else "09:35")
        end_entry = tk.Entry(end_frame, textvariable=end_var, font=("微软雅黑", 10))
        end_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        def save():
            name = name_var.get().strip()
            room = room_var.get().strip()
            start = start_var.get().strip()
            end = end_var.get().strip()

            if not name:
                messagebox.showwarning("警告", "请输入课程名称")
                return

            # 验证时间格式
            try:
                datetime.strptime(start, "%H:%M")
                datetime.strptime(end, "%H:%M")
            except ValueError:
                messagebox.showwarning("警告", "时间格式错误，请使用 HH:MM 格式（如 08:00）")
                return

            day_key = str(day_num)
            if day_key not in self.schedule_data:
                self.schedule_data[day_key] = []

            new_course = {"name": name, "room": room, "start": start, "end": end}

            if is_edit and course_index is not None:
                self.schedule_data[day_key][course_index] = new_course
            else:
                self.schedule_data[day_key].append(new_course)

            self.save_schedule()
            edit_win.destroy()
            refresh_callback()
            self.update_display()

        # 按钮
        btn_frame = tk.Frame(edit_win, bg=self.colors["bg"])
        btn_frame.pack(pady=20)

        save_btn = tk.Button(
            btn_frame,
            text="保存",
            command=save,
            bg=self.colors["current"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 10),
            width=10,
            cursor="hand2"
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(
            btn_frame,
            text="取消",
            command=edit_win.destroy,
            bg=self.colors["header_bg"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 10),
            width=10,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def choose_color(self, color_var):
        """打开颜色选择器"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=color_var.get(), title="选择颜色")
        if color[1]:
            color_var.set(color[1])

    def apply_font_colors(self):
        """应用字体颜色设置"""
        self.settings["course_font_color"] = self.course_color_var.get()
        self.settings["countdown_font_color"] = self.countdown_color_var.get()
        self.save_settings()
        self.update_display()

    def apply_outline_setting(self):
        """应用描边设置"""
        self.settings["font_outline"] = self.outline_var.get()
        self.settings["outline_color"] = self.outline_color_var.get()
        self.save_settings()
        self.update_display()

    def show_settings(self):
        """显示设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("350x550+300+100")
        settings_window.configure(bg=self.colors["bg"])
        settings_window.attributes('-topmost', True)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # 标题
        title_label = tk.Label(
            settings_window,
            text="⚙ 设置",
            bg=self.colors["bg"],
            fg="white",
            font=("微软雅黑", 14, "bold")
        )
        title_label.pack(pady=15)

        # 置顶设置
        topmost_frame = tk.Frame(settings_window, bg=self.colors["bg"])
        topmost_frame.pack(fill=tk.X, padx=20, pady=5)

        self.topmost_var = tk.BooleanVar(value=self.root.attributes('-topmost'))

        topmost_check = tk.Checkbutton(
            topmost_frame,
            text="窗口永远置顶",
            variable=self.topmost_var,
            command=self.apply_topmost_setting,
            bg=self.colors["bg"],
            fg="white",
            selectcolor=self.colors["header_bg"],
            activebackground=self.colors["bg"],
            activeforeground="white",
            font=("微软雅黑", 11)
        )
        topmost_check.pack(anchor=tk.W)

        # 说明文字
        desc_label = tk.Label(
            settings_window,
            text="勾选后窗口将始终显示在其他窗口上方",
            bg=self.colors["bg"],
            fg=self.colors["passed"],
            font=("微软雅黑", 9),
            wraplength=300
        )
        desc_label.pack(padx=20, pady=2)

        # 分隔线
        separator = tk.Frame(settings_window, bg=self.colors["header_bg"], height=1)
        separator.pack(fill=tk.X, padx=20, pady=10)

        # 字体颜色设置
        font_frame = tk.Frame(settings_window, bg=self.colors["bg"])
        font_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(
            font_frame,
            text="字体颜色:",
            bg=self.colors["bg"],
            fg="white",
            font=("微软雅黑", 11)
        ).pack(anchor=tk.W)

        # 课表字体颜色
        course_color_frame = tk.Frame(font_frame, bg=self.colors["bg"])
        course_color_frame.pack(fill=tk.X, pady=3)

        tk.Label(
            course_color_frame,
            text="课表颜色:",
            bg=self.colors["bg"],
            fg=self.colors["normal"],
            font=("微软雅黑", 9)
        ).pack(side=tk.LEFT)

        self.course_color_var = tk.StringVar(value=self.settings.get("course_font_color", "#ecf0f1"))
        course_color_entry = tk.Entry(
            course_color_frame,
            textvariable=self.course_color_var,
            font=("微软雅黑", 9),
            width=10
        )
        course_color_entry.pack(side=tk.LEFT, padx=5)

        course_color_btn = tk.Button(
            course_color_frame,
            text="选择",
            command=lambda: self.choose_color(self.course_color_var),
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 8),
            cursor="hand2"
        )
        course_color_btn.pack(side=tk.LEFT, padx=2)

        # 倒计时字体颜色
        countdown_color_frame = tk.Frame(font_frame, bg=self.colors["bg"])
        countdown_color_frame.pack(fill=tk.X, pady=3)

        tk.Label(
            countdown_color_frame,
            text="倒计时颜色:",
            bg=self.colors["bg"],
            fg=self.colors["normal"],
            font=("微软雅黑", 9)
        ).pack(side=tk.LEFT)

        self.countdown_color_var = tk.StringVar(value=self.settings.get("countdown_font_color", "#f39c12"))
        countdown_color_entry = tk.Entry(
            countdown_color_frame,
            textvariable=self.countdown_color_var,
            font=("微软雅黑", 9),
            width=10
        )
        countdown_color_entry.pack(side=tk.LEFT, padx=5)

        countdown_color_btn = tk.Button(
            countdown_color_frame,
            text="选择",
            command=lambda: self.choose_color(self.countdown_color_var),
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 8),
            cursor="hand2"
        )
        countdown_color_btn.pack(side=tk.LEFT, padx=2)

        # 应用颜色按钮
        apply_color_btn = tk.Button(
            font_frame,
            text="应用颜色",
            command=self.apply_font_colors,
            bg=self.colors["current"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9),
            cursor="hand2"
        )
        apply_color_btn.pack(anchor=tk.W, pady=5)

        # 字体描边设置
        outline_frame = tk.Frame(settings_window, bg=self.colors["bg"])
        outline_frame.pack(fill=tk.X, padx=20, pady=5)

        self.outline_var = tk.BooleanVar(value=self.settings.get("font_outline", False))
        outline_check = tk.Checkbutton(
            outline_frame,
            text="启用字体描边",
            variable=self.outline_var,
            bg=self.colors["bg"],
            fg="white",
            selectcolor=self.colors["header_bg"],
            activebackground=self.colors["bg"],
            activeforeground="white",
            font=("微软雅黑", 11)
        )
        outline_check.pack(anchor=tk.W)

        # 描边颜色
        outline_color_frame = tk.Frame(outline_frame, bg=self.colors["bg"])
        outline_color_frame.pack(fill=tk.X, pady=3)

        tk.Label(
            outline_color_frame,
            text="描边颜色:",
            bg=self.colors["bg"],
            fg=self.colors["normal"],
            font=("微软雅黑", 9)
        ).pack(side=tk.LEFT)

        self.outline_color_var = tk.StringVar(value=self.settings.get("outline_color", "#000000"))
        outline_color_entry = tk.Entry(
            outline_color_frame,
            textvariable=self.outline_color_var,
            font=("微软雅黑", 9),
            width=10
        )
        outline_color_entry.pack(side=tk.LEFT, padx=5)

        outline_color_btn = tk.Button(
            outline_color_frame,
            text="选择",
            command=lambda: self.choose_color(self.outline_color_var),
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 8),
            cursor="hand2"
        )
        outline_color_btn.pack(side=tk.LEFT, padx=2)

        # 应用描边按钮
        apply_outline_btn = tk.Button(
            outline_frame,
            text="应用描边设置",
            command=self.apply_outline_setting,
            bg=self.colors["current"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9),
            cursor="hand2"
        )
        apply_outline_btn.pack(anchor=tk.W, pady=5)

        # 分隔线
        separator = tk.Frame(settings_window, bg=self.colors["header_bg"], height=1)
        separator.pack(fill=tk.X, padx=20, pady=10)

        # 背景图片设置
        bg_frame = tk.Frame(settings_window, bg=self.colors["bg"])
        bg_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(
            bg_frame,
            text="背景图片:",
            bg=self.colors["bg"],
            fg="white",
            font=("微软雅黑", 11)
        ).pack(anchor=tk.W)

        # 当前背景路径
        bg_path_frame = tk.Frame(bg_frame, bg=self.colors["bg"])
        bg_path_frame.pack(fill=tk.X, pady=5)

        current_bg = self.settings.get("background_image", "")
        bg_display = os.path.basename(current_bg) if current_bg else "无"
        self.bg_path_label = tk.Label(
            bg_path_frame,
            text=bg_display,
            bg=self.colors["header_bg"],
            fg=self.colors["normal"],
            font=("微软雅黑", 9),
            anchor=tk.W,
            padx=5
        )
        self.bg_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 按钮
        bg_btn_frame = tk.Frame(bg_frame, bg=self.colors["bg"])
        bg_btn_frame.pack(fill=tk.X, pady=5)

        select_btn = tk.Button(
            bg_btn_frame,
            text="选择图片",
            command=self.select_background,
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9),
            cursor="hand2"
        )
        select_btn.pack(side=tk.LEFT, padx=2)

        clear_btn = tk.Button(
            bg_btn_frame,
            text="清除",
            command=self.clear_background,
            bg=self.colors["header_bg"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 9),
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=2)

        # 说明文字
        bg_desc_label = tk.Label(
            settings_window,
            text="支持 PNG、JPG、JPEG、GIF、BMP 格式",
            bg=self.colors["bg"],
            fg=self.colors["passed"],
            font=("微软雅黑", 9)
        )
        bg_desc_label.pack(padx=20, pady=2)

        # 分隔线
        separator2 = tk.Frame(settings_window, bg=self.colors["header_bg"], height=1)
        separator2.pack(fill=tk.X, padx=20, pady=10)

        # 关于信息
        about_label = tk.Label(
            settings_window,
            text="课表小工具 v1.2",
            bg=self.colors["bg"],
            fg=self.colors["normal"],
            font=("微软雅黑", 10)
        )
        about_label.pack(pady=5)

        # 关闭按钮
        close_btn = tk.Button(
            settings_window,
            text="关闭",
            command=settings_window.destroy,
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            font=("微软雅黑", 10),
            width=10,
            cursor="hand2"
        )
        close_btn.pack(pady=10)

    def apply_topmost_setting(self):
        """应用置顶设置"""
        is_topmost = self.topmost_var.get()
        self.root.attributes('-topmost', is_topmost)
        self.settings["topmost"] = is_topmost
        self.save_settings()

    def apply_background(self):
        """应用背景图片"""
        bg_path = self.settings.get("background_image", "")
        if bg_path and os.path.exists(bg_path):
            try:
                from PIL import Image, ImageTk
                # 获取窗口当前大小
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                if width < 100:  # 如果窗口还未显示，使用默认大小
                    width, height = 320, 400

                # 打开并调整图片大小
                image = Image.open(bg_path)
                image = image.resize((width, height), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(image)

                # 设置背景
                if self.bg_label:
                    self.bg_label.config(image=self.bg_image)
                    self.bg_label.image = self.bg_image  # 保持引用
            except ImportError:
                print("需要安装PIL库来支持背景图片: pip install Pillow")
            except Exception as e:
                print(f"加载背景图片失败: {e}")
        else:
            # 没有背景图片，使用纯色
            if self.bg_label:
                self.bg_label.config(image="", bg=self.colors["bg"])
                self.bg_image = None

    def select_background(self):
        """选择背景图片"""
        file_path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.settings["background_image"] = file_path
            self.apply_background()
            self.save_settings()
            # 更新路径显示
            if hasattr(self, 'bg_path_label'):
                self.bg_path_label.config(text=os.path.basename(file_path))

    def clear_background(self):
        """清除背景图片"""
        self.settings["background_image"] = ""
        self.apply_background()
        self.save_settings()
        if hasattr(self, 'bg_path_label'):
            self.bg_path_label.config(text="无")

    def load_settings(self):
        """加载设置"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
            except Exception:
                pass
        # 应用置顶设置
        self.root.attributes('-topmost', self.settings.get("topmost", True))

    def on_window_resize(self, event):
        """窗口大小改变时更新背景图片"""
        if self.bg_image and event.widget == self.root:
            # 使用after延迟执行，避免频繁更新
            if hasattr(self, '_resize_after_id'):
                self.root.after_cancel(self._resize_after_id)
            self._resize_after_id = self.root.after(200, self.apply_background)

    def save_settings(self):
        """保存设置"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_schedule(self):
        """加载课表数据"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    self.schedule_data = json.load(f)
            except Exception as e:
                messagebox.showerror("错误", f"加载课表失败: {e}")
                self.create_default_schedule()
        else:
            self.create_default_schedule()

    def create_default_schedule(self):
        """创建默认课表（示例）"""
        self.schedule_data = {
            "1": [  # 周一
                {"name": "高等数学", "room": "A101", "start": "08:00", "end": "09:35"},
                {"name": "大学英语", "room": "B205", "start": "10:00", "end": "11:35"},
                {"name": "程序设计", "room": "C301", "start": "14:00", "end": "15:35"}
            ],
            "2": [  # 周二
                {"name": "线性代数", "room": "A102", "start": "08:00", "end": "09:35"},
                {"name": "数据结构", "room": "C302", "start": "14:00", "end": "16:35"}
            ],
            "3": [  # 周三
                {"name": "高等数学", "room": "A101", "start": "08:00", "end": "09:35"},
                {"name": "体育", "room": "体育馆", "start": "10:00", "end": "11:35"},
                {"name": "操作系统", "room": "C303", "start": "14:00", "end": "15:35"}
            ],
            "4": [  # 周四
                {"name": "概率论", "room": "A103", "start": "08:00", "end": "09:35"},
                {"name": "计算机网络", "room": "C304", "start": "14:00", "end": "16:35"}
            ],
            "5": [  # 周五
                {"name": "大学英语", "room": "B205", "start": "08:00", "end": "09:35"},
                {"name": "数据库原理", "room": "C305", "start": "10:00", "end": "11:35"}
            ]
        }
        self.save_schedule()

    def save_schedule(self):
        """保存课表"""
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(self.schedule_data, f, ensure_ascii=False, indent=2)

    def import_schedule(self):
        """导入课表文件"""
        file_path = filedialog.askopenfilename(
            title="选择课表文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.schedule_data = data
                self.save_schedule()
                self.update_display()
                messagebox.showinfo("成功", "课表导入成功！")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    def get_today_schedule(self):
        """获取今天的课程"""
        weekday = str(datetime.now().weekday() + 1)  # 1-7 表示周一到周日
        courses = self.schedule_data.get(weekday, [])

        # 按开始时间排序
        courses_sorted = sorted(courses, key=lambda x: x.get('start', '00:00'))
        return courses_sorted

    def parse_time(self, time_str):
        """解析时间字符串"""
        return datetime.strptime(time_str, "%H:%M")

    def get_course_status(self, course):
        """获取课程状态"""
        now = datetime.now()
        start = self.parse_time(course['start'])
        end = self.parse_time(course['end'])

        start_dt = now.replace(hour=start.hour, minute=start.minute, second=0)
        end_dt = now.replace(hour=end.hour, minute=end.minute, second=0)

        if now < start_dt:
            return "upcoming", (start_dt - now).total_seconds()
        elif start_dt <= now <= end_dt:
            return "current", (end_dt - now).total_seconds()
        else:
            return "passed", 0

    def format_countdown(self, seconds):
        """格式化倒计时"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            return f"{int(seconds // 60)}分钟"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分钟"

    def update_display(self):
        """更新显示"""
        # 获取颜色设置
        course_font_color = self.settings.get("course_font_color", "#ecf0f1")
        countdown_font_color = self.settings.get("countdown_font_color", "#f39c12")

        # 更新日期
        now = datetime.now()
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        date_text = f"{now.month}月{now.day}日 {weekdays[now.weekday()]}"
        self.date_label.config(text=date_text)

        # 清空课程列表
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        courses = self.get_today_schedule()

        if not courses:
            # 使用带描边的标签或普通标签
            if self.settings.get("font_outline", False):
                no_class_label = self.create_outlined_label(
                    self.scrollable_frame, "今天没有课程 🎉", 12, "normal", False
                )
                no_class_label.pack(pady=50)
            else:
                no_class_label = tk.Label(
                    self.scrollable_frame,
                    text="今天没有课程 🎉",
                    bg=self.colors["bg"],
                    fg=course_font_color,
                    font=("微软雅黑", 12)
                )
                no_class_label.pack(pady=50)

            self.countdown_label.config(
                text="好好享受休息时光！",
                fg=countdown_font_color
            )
            return

        # 找到当前和下一节课
        current_course = None
        next_course = None
        min_time_to_next = float('inf')

        for course in courses:
            status, time_left = self.get_course_status(course)
            if status == "current":
                current_course = course
            elif status == "upcoming" and time_left < min_time_to_next:
                next_course = course
                min_time_to_next = time_left

        # 更新倒计时
        self.countdown_label.config(fg=countdown_font_color)
        if current_course:
            _, time_left = self.get_course_status(current_course)
            self.countdown_label.config(
                text=f"⏰ 正在上课: {current_course['name']}\n还剩 {self.format_countdown(time_left)}"
            )
        elif next_course:
            self.countdown_label.config(
                text=f"📖 下一节: {next_course['name']}\n还有 {self.format_countdown(min_time_to_next)}"
            )
        else:
            self.countdown_label.config(text="✅ 今天的课程全部结束！")

        # 显示课程列表
        outline_enabled = self.settings.get("font_outline", False)

        for i, course in enumerate(courses):
            status, _ = self.get_course_status(course)

            # 根据状态选择颜色
            if status == "current":
                bg_color = self.colors["current"]
                fg_color = "white"
                border_color = self.colors["current"]
                indicator = "▶ "
            elif status == "upcoming" and course == next_course:
                bg_color = self.colors["next"]
                fg_color = "white"
                border_color = self.colors["next"]
                indicator = "⏳ "
            elif status == "passed":
                bg_color = self.colors["bg"]
                fg_color = self.colors["passed"]
                border_color = self.colors["passed"]
                indicator = "✓ "
            else:
                bg_color = self.colors["bg"]
                fg_color = course_font_color
                border_color = "#7f8c8d"
                indicator = "○ "

            # 课程卡片
            card = tk.Frame(
                self.scrollable_frame,
                bg=bg_color if status == "current" else self.colors["bg"],
                highlightbackground=border_color,
                highlightthickness=2 if status in ["current", "upcoming"] else 1,
                padx=10,
                pady=8
            )
            card.pack(fill=tk.X, pady=5, padx=5)

            # 课程名称
            if outline_enabled and status not in ["current", "upcoming", "passed"]:
                name_label = self.create_outlined_label(
                    card, f"{indicator}{course['name']}", 11,
                    "bold" if status in ["current", "upcoming"] else "normal", False
                )
                name_label.pack(fill=tk.X)
            else:
                name_label = tk.Label(
                    card,
                    text=f"{indicator}{course['name']}",
                    bg=card.cget("bg"),
                    fg=fg_color,
                    font=("微软雅黑", 11, "bold" if status in ["current", "upcoming"] else "normal"),
                    anchor=tk.W
                )
                name_label.pack(fill=tk.X)

            # 时间和地点
            info_text = f"🕐 {course['start']} - {course['end']}  |  📍 {course['room']}"
            if outline_enabled and status not in ["current", "upcoming", "passed"]:
                info_label = self.create_outlined_label(card, info_text, 9, "normal", False)
                info_label.pack(fill=tk.X, pady=(3, 0))
            else:
                info_label = tk.Label(
                    card,
                    text=info_text,
                    bg=card.cget("bg"),
                    fg=fg_color,
                    font=("微软雅黑", 9),
                    anchor=tk.W
                )
                info_label.pack(fill=tk.X, pady=(3, 0))

    def schedule_next_update(self):
        """安排下一次更新"""
        self.update_display()
        self.root.after(self.update_interval, self.schedule_next_update)

    def run(self):
        """运行程序"""
        self.root.mainloop()


def create_sample_schedule():
    """创建示例课表文件"""
    sample = {
        "1": [
            {"name": "高等数学", "room": "A101", "start": "08:00", "end": "09:35"},
            {"name": "大学英语", "room": "B205", "start": "10:00", "end": "11:35"},
            {"name": "程序设计", "room": "C301", "start": "14:00", "end": "15:35"},
            {"name": "自习", "room": "图书馆", "start": "19:00", "end": "21:00"}
        ],
        "2": [
            {"name": "线性代数", "room": "A102", "start": "08:00", "end": "09:35"},
            {"name": "数据结构", "room": "C302", "start": "14:00", "end": "16:35"}
        ],
        "3": [
            {"name": "高等数学", "room": "A101", "start": "08:00", "end": "09:35"},
            {"name": "体育", "room": "体育馆", "start": "10:00", "end": "11:35"},
            {"name": "操作系统", "room": "C303", "start": "14:00", "end": "15:35"}
        ],
        "4": [
            {"name": "概率论", "room": "A103", "start": "08:00", "end": "09:35"},
            {"name": "计算机网络", "room": "C304", "start": "14:00", "end": "16:35"}
        ],
        "5": [
            {"name": "大学英语", "room": "B205", "start": "08:00", "end": "09:35"},
            {"name": "数据库原理", "room": "C305", "start": "10:00", "end": "11:35"}
        ]
    }

    with open("schedule.json", 'w', encoding='utf-8') as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print("已创建示例课表 schedule.json")
    print("你可以修改这个文件或点击\"导入课表\"按钮加载自己的课表")


if __name__ == "__main__":
    # 如果没有课表文件，创建示例
    if not os.path.exists("schedule.json"):
        create_sample_schedule()

    app = ScheduleWidget()
    app.run()
