@echo off 
chcp 65001 
title 头条助手 - 环境配置 
 
echo 正在创建虚拟环境... 
python -m venv venv 
 
echo 正在激活虚拟环境... 
call venv\Scripts\activate.bat 
 
echo 正在安装依赖... 
pip install -r requirements.txt 
 
echo 正在安装playwright浏览器... 
playwright install chromium 
 
echo 安装完成！ 
pause 
