@echo off
chcp 65001 >nul
title 中国象棋命令行工具

echo.
echo ========================================
echo           中国象棋命令行工具
echo ========================================
echo.
echo 请选择运行模式：
echo.
echo 1. 演示模式 - 自动演示几个移动
echo 2. 交互模式 - 进入命令行界面
echo 3. 退出
echo.
set /p choice="请输入选择 (1-3): "

if "%choice%"=="1" (
    echo.
    echo 启动演示模式...
    python chess_cli.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo 启动交互模式...
    python chess_cli.py --cli
) else if "%choice%"=="3" (
    echo 再见！
    exit /b 0
) else (
    echo 无效选择，请重新运行程序
    pause
    exit /b 1
) 