@echo off
setlocal

:: 获取当前批处理文件的路径
for %%I in ("%~dp0converter.mp4.h264.vbr-18000-25000.seq.bat") do set "scriptPath=%%~fI"

:: 注册表键名
set "keyName=HKCR\SystemFileAssociations\.mkv\shell\FFmpeg Convert to MP4 H.264 VBR-18000-25000\command"

:: 命令行
set "command=""%scriptPath%"" ""%%V"""

:: 将命令添加到右键菜单
reg add "%keyName%" /ve /d "%command%" /f

:: 图标文件路径，这里我们使用shell32.dll中的第5个图标
set "iconPath=%SystemRoot%\system32\shell32.dll,5"

:: 将图标添加到右键菜单项
reg add "%keyName%" /v Icon /t REG_SZ /d "%iconPath%" /f

endlocal

pause
