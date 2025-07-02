#!/bin/bash

# 设置UTF-8编码
export LANG=zh_CN.UTF-8

echo ""
echo "========================================"
echo "           中国象棋命令行工具"
echo "========================================"
echo ""
echo "请选择运行模式："
echo ""
echo "1. 演示模式 - 自动演示几个移动"
echo "2. 交互模式 - 进入命令行界面"
echo "3. 退出"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "启动演示模式..."
        python3 chess_cli.py
        ;;
    2)
        echo ""
        echo "启动交互模式..."
        python3 chess_cli.py --cli
        ;;
    3)
        echo "再见！"
        exit 0
        ;;
    *)
        echo "无效选择，请重新运行程序"
        exit 1
        ;;
esac 