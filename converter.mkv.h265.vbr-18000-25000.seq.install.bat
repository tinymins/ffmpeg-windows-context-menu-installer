@echo off
setlocal enabledelayedexpansion

:: 获取批处理文件的路径
for %%I in ("%~dp0converter.mkv.h265.vbr-18000-25000.seq.bat") do set "scriptPath=%%~fI"

:: 文件类型数组
set "fileTypes=.mkv .mp4 .avi .mov"

:: 遍历文件类型
for %%F in (%fileTypes%) do (
    :: 注册表键的路径
    set "keyName=HKCR\SystemFileAssociations\%%F\shell\FFmpeg convert to..."
    set "subKeyName=HKCR\SystemFileAssociations\%%F\shell\FFmpeg convert to...\shell\MKV H.265 VBR-18000-25000"

    :: 创建一级菜单注册表键
    reg add "!keyName!" /v "Icon" /t REG_SZ /d "%SystemRoot%\system32\shell32.dll,5" /f
    reg add "!keyName!" /v "MUIVerb" /t REG_SZ /d "FFmpeg convert to..." /f
    reg add "!keyName!" /v "SubCommands" /t REG_SZ /d "" /f

    :: 创建二级菜单注册表键
    reg add "!subKeyName!" /v "MUIVerb" /t REG_SZ /d "MKV H.265 VBR-18000-25000" /f
    reg add "!subKeyName!\command" /ve /d """%scriptPath%"" ""%%V""" /f
)

endlocal
