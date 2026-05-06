#!/bin/bash
# 一键运行完整系统

cd ~/auto_trading_system

echo "=========================================="
echo "🚀 量化交易系统 - 完整运行"
echo "=========================================="
echo ""

# 激活虚拟环境
source venv/bin/activate

# 选项菜单
echo "请选择运行模式:"
echo "1. 完整分析 (Kronos + Dexter + 多智能体)"
echo "2. 全市场扫描选股"
echo "3. 实盘模拟"
echo "4. 查看持仓"
echo "5. 退出"
read -p "请输入选项 [1-5]: " option

case $option in
    1)
        echo "运行完整分析..."
        python three_tools_system_final.py
        ;;
    2)
        echo "运行全市场扫描..."
        python auto_screener.py
        ;;
    3)
        echo "运行实盘模拟..."
        python live_simulator_full.py
        ;;
    4)
        echo "查看持仓..."
        python -c "
from live_simulator_full import PortfolioManager
p = PortfolioManager()
print('当前模拟持仓:', p.positions)
"
        ;;
    5)
        echo "退出"
        exit 0
        ;;
esac

echo ""
echo "✅ 运行完成"
