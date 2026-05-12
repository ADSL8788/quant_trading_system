#!/usr/bin/env python3
"""
股票池管理工具 - 联动版
功能：列出当前激活的股票池（优先显示动态扫描结果）
"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from config.settings import config
from data_layer.pool_manager import sync_to_config

class Color:
    RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
    WHITE = '\033[97m'; BOLD = '\033[1m'; END = '\033[0m'

def colorize(text, color):
    return f"{color}{text}{Color.END}"

def main():
    print("\n" + "█" * 60)
    print(f"█  当前激活股票池状态查询")
    print("█" * 60)

    # ============================================================
    # 关键联动：调用 pool_manager 同步最新的股票池
    # 这样无论是在 config 中预设的，还是 sc 扫描出来的，都能显示
    # ============================================================
    active_pool = sync_to_config()
    
    if not active_pool:
        print(f"\n{colorize('⚠️ 股票池为空!', Color.YELLOW)}")
        print("请尝试运行 'sc' 命令进行全市场扫描，或使用 'add' 命令手动添加股票。")
        print("█" * 60)
        return

    print(f"\n{Color.BOLD}共计加载 {len(active_pool)} 只股票:{Color.END}")
    print("-" * 60)
    print(f"{'序号':<6} {'代码':<12} {'名称':<12} {'来源/板块':<15}")
    print("-" * 60)

    for i, stock in enumerate(active_pool, 1):
        ts_code = stock.get('ts_code', 'N/A')
        name = stock.get('name', '未知')
        sector = stock.get('sector', '未知')
        
        # 如果来源是动态扫描，用黄色高亮显示
        if sector == '动态扫描':
            sector_str = colorize(sector, Color.YELLOW)
        else:
            sector_str = colorize(sector, Color.WHITE)
            
        print(f"{i:<6} {ts_code:<12} {name:<12} {sector_str:<15}")

    print("-" * 60)
    print("\n" + "█" * 60)
    print(f"💡 提示: 当前池子已与 data/auto_screener_results.csv 实时同步")
    print("█" * 60 + "\n")

if __name__ == "__main__":
    main()
