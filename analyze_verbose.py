#!/usr/bin/env python3
"""分析单只股票 - 详细打印版"""
import sys
import re
import time
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from config.settings import config
from three_tools_system_final import ThreeToolsTradingSystem
from loguru import logger

# 移除默认的日志处理器，自定义打印
logger.remove()

def verbose_print(msg, level="INFO"):
    """自定义详细打印"""
    timestamp = time.strftime("%H:%M:%S")
    emoji = {
        "INFO": "📘",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }
    print(f"{timestamp} {emoji.get(level, '📘')} {msg}")

# 添加自定义处理器
logger.add(lambda msg: verbose_print(msg, msg.record["level"].name), format="", level="DEBUG")

from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor
from dexter_wrapper import DexterWrapper
from trading_agents_wrapper import TradingAgentsWrapper

def format_stock_code(code):
    """自动格式化股票代码"""
    code = code.upper().strip()
    
    if code.endswith('.SZ') or code.endswith('.SH'):
        return code
    
    import re
    num = re.sub(r'\D', '', code)
    
    if len(num) == 6:
        if num.startswith(('00', '30', '20')):
            return f"{num}.SZ"
        elif num.startswith(('60', '68')):
            return f"{num}.SH"
    
    return code

def get_stock_name(ts_code):
    """根据代码获取股票名称"""
    try:
        import tushare as ts
        from dotenv import load_dotenv
        import os
        load_dotenv()
        ts.set_token(os.getenv('TUSHARE_TOKEN'))
        pro = ts.pro_api()
        df = pro.stock_basic(ts_code=ts_code, fields='name')
        if not df.empty:
            return df.iloc[0]['name']
    except Exception as e:
        verbose_print(f"获取股票名称失败: {e}", "WARNING")
    return ts_code.split('.')[0]

class VerboseTradingSystem(ThreeToolsTradingSystem):
    """带详细打印的交易系统"""
    
    def __init__(self):
        verbose_print("初始化三工具集成交易系统...", "INFO")
        super().__init__()
        verbose_print("系统初始化完成", "SUCCESS")
    
    def analyze_single_stock(self, stock):
        ts_code = stock['ts_code']
        name = stock['name']
        
        print("\n" + "="*60)
        print(f"🎯 分析目标: {name} ({ts_code})")
        print("="*60)
        
        result = {
            "ts_code": ts_code,
            "name": name,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "kronos": None,
            "dexter": None,
            "final_decision": None
        }
        
        # Step 1: Kronos 技术分析
        print(f"\n📈 [1/5] Kronos 技术分析...")
        print(f"   ├─ 获取历史K线数据...")
        
        df = self.data_client.get_kline(ts_code, days=200)
        
        if len(df) < 50:
            print(f"   └─ ❌ 数据不足: 仅{len(df)}条 (需要≥50条)")
            return None
        
        print(f"   ├─ 数据获取成功: {len(df)}条K线")
        print(f"   ├─ 时间范围: {df['timestamp'].iloc[0].strftime('%Y-%m-%d')} ~ {df['timestamp'].iloc[-1].strftime('%Y-%m-%d')}")
        print(f"   ├─ 当前价格: {df['close'].iloc[-1]:.2f}")
        print(f"   ├─ 涨跌幅: {(df['close'].iloc[-1]/df['close'].iloc[-20]-1)*100:.2f}% (20日)")
        
        print(f"   ├─ 运行Kronos预测模型...")
        kronos_signal = self.kronos.predict(df)
        result["kronos"] = kronos_signal
        
        print(f"   ├─ 预测结果:")
        print(f"   │    ├─ 操作: {kronos_signal['action']}")
        print(f"   │    ├─ 置信度: {kronos_signal['confidence']:.1%}")
        print(f"   │    └─ 预期收益: {kronos_signal.get('expected_return', 0):+.2%}")
        print(f"   └─ ✅ Kronos分析完成")
        
        # Step 2: Dexter 深度研究
        print(f"\n📚 [2/5] Dexter 深度研究...")
        print(f"   ├─ 调用DeepSeek进行基本面分析...")
        
        try:
            dexter_result = self.dexter.research_stock(ts_code, name)
            result["dexter"] = {
                "success": dexter_result.get("success"),
                "analysis_preview": dexter_result.get("analysis", "")[:500] if dexter_result.get("analysis") else ""
            }
            
            if result["dexter"].get("success"):
                print(f"   ├─ 研究报告生成成功")
                # 提取研究结论
                analysis = result["dexter"].get("analysis_preview", "")
                if "买入" in analysis[:200]:
                    print(f"   ├─ 研究倾向: 积极")
                elif "卖出" in analysis[:200]:
                    print(f"   ├─ 研究倾向: 谨慎")
                else:
                    print(f"   ├─ 研究倾向: 中性")
            else:
                print(f"   ├─ ⚠️ 研究失败，使用降级方案")
        except Exception as e:
            print(f"   ├─ ❌ Dexter调用失败: {e}")
            result["dexter"] = {"success": False}
        
        print(f"   └─ ✅ Dexter研究完成")
        
        # Step 3: 多智能体决策
        print(f"\n🤖 [3/5] 多智能体综合决策...")
        print(f"   ├─ 启动5个专业智能体并行分析...")
        
        decision = self.agents.decide(
            ticker=ts_code,
            name=name,
            kronos_signal=kronos_signal,
            dexter_report=result["dexter"].get("analysis_preview") if result["dexter"] else None
        )
        
        result["final_decision"] = decision
        
        print(f"   ├─ 各智能体意见:")
        
        agents_opinions = decision.get("agents_opinions", {})
        for agent, opinion in agents_opinions.items():
            # 截取简短意见
            short_opinion = opinion[:50] + "..." if len(opinion) > 50 else opinion
            print(f"   │    ├─ {agent}: {short_opinion}")
        
        print(f"   └─ ✅ 综合决策完成")
        
        # Step 4: 最终决策
        print(f"\n🎯 [4/5] 最终决策:")
        action = decision.get("action", "HOLD")
        reason = decision.get("reason", "")
        
        action_emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
        print(f"   ├─ 决策: {action_emoji} {action}")
        print(f"   └─ 理由: {reason}")
        
        # Step 5: 交易建议
        print(f"\n💰 [5/5] 交易建议:")
        if action == "BUY":
            print(f"   ├─ 建议操作: 买入")
            print(f"   ├─ 建议仓位: 10-15%")
            print(f"   ├─ 止损线: -7%")
            print(f"   └─ 止盈线: +15%")
        elif action == "SELL":
            print(f"   ├─ 建议操作: 卖出")
            print(f"   ├─ 理由: 技术面与基本面均偏空")
            print(f"   └─ 建议: 减仓或清仓")
        else:
            print(f"   ├─ 建议操作: 持有/观望")
            print(f"   ├─ 理由: 信号不明确或风险较高")
            print(f"   └─ 建议: 等待更明确的入场信号")
        
        print("\n" + "="*60)
        
        return result

def main():
    if len(sys.argv) < 2:
        print("\n" + "="*60)
        print("📊 单股分析工具 (详细版)")
        print("="*60)
        print("\n用法:")
        print("  python analyze_verbose.py <股票代码> [股票名称]")
        print("\n示例:")
        print("  python analyze_verbose.py 000858        # 自动识别五粮液")
        print("  python analyze_verbose.py 000858 五粮液")
        print("  python analyze_verbose.py 600519        # 贵州茅台")
        print("  python analyze_verbose.py 300061        # 自定义")
        print("\n" + "="*60)
        sys.exit(0)
    
    raw_code = sys.argv[1]
    ts_code = format_stock_code(raw_code)
    
    # 获取股票名称
    if len(sys.argv) >= 3:
        name = sys.argv[2]
    else:
        name = get_stock_name(ts_code)
    
    print("\n" + "="*60)
    print(f"🚀 启动详细分析: {name} ({ts_code})")
    print("="*60)
    
    # 覆盖股票池
    config.WATCHLIST = [{'ts_code': ts_code, 'name': name, 'sector': '自选'}]
    
    # 运行分析
    system = VerboseTradingSystem()
    results = system.run()
    
    print("\n" + "="*60)
    print("✅ 分析完成")
    print("="*60)

if __name__ == "__main__":
    main()
