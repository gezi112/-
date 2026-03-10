#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的课表小工具打包脚本
使用方法: python build_exe_simple.py
"""

import os
import sys
import subprocess

def create_simple_icon():
    """创建一个简单的图标"""
    try:
        from PIL import Image, ImageDraw

        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        images = []

        for size in sizes:
            img = Image.new('RGBA', size, (44, 62, 80, 255))
            draw = ImageDraw.Draw(img)

            margin = size[0] // 8
            # 外框
            draw.rectangle([margin, margin, size[0]-margin, size[1]-margin],
                          outline=(52, 152, 219, 255), width=max(1, size[0]//20))
            # 顶部条
            draw.rectangle([margin, margin, size[0]-margin, margin + size[0]//5],
                          fill=(52, 152, 219, 255))

            images.append(img)

        images[0].save('icon.ico', format='ICO', sizes=sizes)
        print("✓ 图标创建成功: icon.ico")
        return True
    except Exception as e:
        print(f"⚠ 创建图标失败: {e}")
        return False

def main():
    # 创建图标
    if not os.path.exists('icon.ico'):
        print("正在创建图标...")
        create_simple_icon()

    print("\n开始打包exe...")
    print("这可能需要几分钟时间，请耐心等待...\n")

    # 检查并安装pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("安装 PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'pyinstaller'])

    # 打包命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=课表小工具',
        '--windowed',
        '--onefile',
        '--noconfirm',
        '--clean',
    ]

    if os.path.exists('icon.ico'):
        cmd.extend(['--icon=icon.ico'])
        cmd.extend(['--add-data', 'icon.ico;.'])

    cmd.append('schedule_widget.py')

    try:
        subprocess.check_call(cmd)
        print("\n" + "="*50)
        print("✓ 打包成功!")
        print("="*50)
        print(f"✓ exe文件: {os.path.abspath('dist/课表小工具.exe')}")
        print("\n使用说明:")
        print("1. 直接运行 dist/课表小工具.exe 即可启动")
        print("2. 可将exe发送到桌面创建快捷方式")
        print("3. 运行时会在任务栏显示图标，可点击选中")
        print("="*50)

        # 询问是否创建快捷方式
        create_shortcut = input("\n是否在桌面创建快捷方式? (y/n): ").lower().strip()
        if create_shortcut == 'y':
            try:
                import winshell
                from win32com.client import Dispatch

                desktop = winshell.desktop()
                target = os.path.abspath("dist/课表小工具.exe")
                shortcut_path = os.path.join(desktop, "课表小工具.lnk")

                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = target
                shortcut.WorkingDirectory = os.path.dirname(target)
                if os.path.exists('icon.ico'):
                    shortcut.IconLocation = os.path.abspath('icon.ico')
                shortcut.save()
                print(f"✓ 桌面快捷方式已创建")
            except Exception as e:
                print(f"⚠ 创建快捷方式失败: {e}")
                print("  你可以手动将exe文件发送到桌面快捷方式")

    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
