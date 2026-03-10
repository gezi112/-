#!/usr/bin/env python3
"""
打包课表小工具为exe
使用方法: python build_exe.py
"""

import os
import sys
import subprocess

def create_icon():
    """创建一个简单的图标文件"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 创建64x64的图标
        size = 64
        img = Image.new('RGBA', (size, size), (44, 62, 80, 255))  # 背景色 #2c3e50
        draw = ImageDraw.Draw(img)

        # 绘制日历形状
        # 外框
        margin = 8
        draw.rectangle([margin, margin, size-margin, size-margin], outline=(52, 152, 219, 255), width=3)

        # 顶部横条
        draw.rectangle([margin, margin, size-margin, margin+12], fill=(52, 152, 219, 255))

        # 绘制课程格子
        cell_size = 10
        start_x = margin + 6
        start_y = margin + 18
        for row in range(3):
            for col in range(3):
                x = start_x + col * (cell_size + 4)
                y = start_y + row * (cell_size + 4)
                color = (236, 240, 241, 255) if (row + col) % 2 == 0 else (149, 165, 166, 255)
                draw.rectangle([x, y, x+cell_size, y+cell_size], fill=color)

        # 保存为ico
        img.save('icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        print("✓ 图标文件创建成功: icon.ico")
        return True
    except ImportError:
        print("✗ 需要安装Pillow来创建图标: pip install Pillow")
        return False
    except Exception as e:
        print(f"✗ 创建图标失败: {e}")
        return False

def build_exe():
    """使用pyinstaller打包exe"""
    # 检查pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    # 创建图标
    if not os.path.exists('icon.ico'):
        if not create_icon():
            print("警告: 没有找到图标文件，将使用默认图标")
            icon_param = []
        else:
            icon_param = ['--icon=icon.ico']
    else:
        icon_param = ['--icon=icon.ico']

    print("\n开始打包exe...")

    # pyinstaller参数
    params = [
        'pyinstaller',
        '--name=课表小工具',
        '--windowed',  # 不显示命令行窗口
        '--onefile',   # 打包成单个exe
        '--noconfirm', # 覆盖现有文件
        '--clean',     # 清理临时文件
    ] + icon_param + [
        '--add-data=icon.ico;.',
        'schedule_widget.py'
    ]

    try:
        subprocess.check_call(params)
        print("\n✓ 打包成功!")
        print("✓ exe文件位于: dist/课表小工具.exe")

        # 创建启动快捷方式脚本
        create_shortcut_script()

    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        sys.exit(1)

def create_shortcut_script():
    """创建快捷方式生成脚本"""
    shortcut_script = '''
import os
import winshell
from win32com.client import Dispatch

def create_shortcut():
    desktop = winshell.desktop()
    target = os.path.abspath("dist/课表小工具.exe")
    icon = os.path.abspath("icon.ico")

    shortcut_path = os.path.join(desktop, "课表小工具.lnk")

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.IconLocation = icon
    shortcut.save()

    print(f"✓ 桌面快捷方式已创建: {shortcut_path}")

if __name__ == "__main__":
    create_shortcut()
'''
    with open('create_shortcut.py', 'w', encoding='utf-8') as f:
        f.write(shortcut_script)

    print("✓ 快捷方式生成脚本已创建: create_shortcut.py")
    print("  运行 'python create_shortcut.py' 可创建桌面快捷方式")

if __name__ == "__main__":
    build_exe()
