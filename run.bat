@echo off 
chcp 65001 
cd /d %~dp0 
title 头条助手 
echo 正在启动程序... 
call venv\Scripts\activate.bat 
python src\main.py 
if errorlevel 1 ( 
    echo 程序异常退出！ 
    pause 
) 
