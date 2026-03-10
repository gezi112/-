' 启动课表小工具（隐藏命令框）
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw schedule_widget.py", 0, False
Set WshShell = Nothing
