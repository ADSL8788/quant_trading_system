#!/usr/bin/env python3
"""带 Tushare 修补的启动脚本"""
import sys
import os

# 首先应用修补
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'TradingAgents'))

# 导入并应用数据修补
from tradingagents.data.tushare_data import patch_yfinance_module
patch_yfinance_module()

# 然后运行主程序
from three_tools_system import main

if __name__ == "__main__":
    main()
