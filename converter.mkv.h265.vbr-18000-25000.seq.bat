@echo off
setlocal enabledelayedexpansion
%~d0
cd %~dp0

for %%I in (%*) do (
  set "inputFile=%%~I"
  set "inputName=%%~dpnI"
  set "outputFile=%%~dpnI.h265.mkv"
  set "counter=1"

  echo Input File:  "!inputFile!"

  :loop
  if exist "!outputFile!" (
    set "outputFile=!inputName! (!counter!).h265.mkv"
    set /a counter+=1
    goto :loop
  )

  echo Output File: "!outputFile!"

  ffmpeg -i "!inputFile!" ^
    -map 0 ^
    -c:v hevc_nvenc ^
    -b:v 18000k ^
    -maxrate 25000k ^
    -rc:v vbr ^
    -preset p3 ^
    -tune hq ^
    -profile:v main ^
    -rc-lookahead 32 ^
    -spatial_aq 1 ^
    -bf 4 ^
    -pass 1 ^
    -f null /dev/null
  ffmpeg -i "!inputFile!" ^
    -map 0 ^
    -c:v hevc_nvenc ^
    -b:v 18000k ^
    -maxrate 25000k ^
    -rc:v vbr ^
    -preset p3 ^
    -tune hq ^
    -profile:v main ^
    -rc-lookahead 32 ^
    -spatial_aq 1 ^
    -bf 4 ^
    -pass 2 ^
    -c:a copy ^
    "!outputFile!"

  @REM copy /B "!outputFile!" +,, & copy /B "!inputFile!" +,, "!outputFile!"
  nircmd clonefiletime "!inputFile!" "!outputFile!"
)

endlocal
pause
