#!/usr/bin/env python3
"""单股完整分析 - 详细研究报告版"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor
from dexter_wrapper import DexterWrapper
from trading_agents_wrapper import TradingAgentsWrapper

def print_sep(char="=", length=70):
    print(char * length)

def analyze_stock(ts_code, name):
    print_sep("=")
    print(f"🔍 深度分析报告: {name} ({ts_code})")
    print_sep("=")
    
    # 1. Kronos
    print("\n📈 [1/4] Kronos 技术分析")
    print("-" * 50)
    client = TushareClient()
    df = client.get_kline(ts_code, days=200)
    if len(df) < 50:
        print("   ❌ 数据不足")
        return
    
    kronos = KronosPredictor()
    signal = kronos.predict(df)
    print(f"   信号: {signal['action']}")
    print(f"   置信度: {signal['confidence']:.1%}")
    print(f"   当前价格: {signal.get('current_price', df['close'].iloc[-1]):.2f}")
    print(f"   预期收益: {signal.get('expected_return', 0):+.2%}")
    
    # 2. Dexter 详细报告
    print("\n📚 [2/4] Dexter 基本面研究")
    print("-" * 50)
    dexter = DexterWrapper()
    result = dexter.research_stock(ts_code, name)
    full_report = ""
    if result.get("success"):
        full_report = result.get("analysis", "")
        print(full_report)
    else:
        print("   ❌ 分析失败")
    print("-" * 50)
    
    # 3. 多智能体决策
    print("\n🤖 [3/4] 多智能体综合决策")
    print("-" * 50)
    agents = TradingAgentsWrapper()
    decision = agents.decide(ts_code, name, signal, full_report)
    print(f"   最终决策: {decision.get('action', 'HOLD')}")
    print(f"   决策理由: {decision.get('reason', '无')[:200]}")
    print("-" * 50)
    
    # 4. 综合投资建议
    print("\n💡 [4/4] 综合投资建议")
    print("-" * 50)
    action = decision.get('action', 'HOLD')
    if action == 'BUY':
        conf = signal['confidence']
        print(f"   ✅ 建议买入")
        print(f"   🔥 信号置信度: {conf:.1%}")
        print(f"   📊 建议仓位: {min(30, int(conf*100))}%")
        print(f"   🛡️ 止损线: -7% | 止盈线: +15%")
    elif action == 'SELL':
        print(f"   ❌ 建议卖出")
        print(f"   ⚠️ 理由: {decision.get('reason', '技术面走弱')[:100]}")
        print(f"   💰 建议: 分批减仓")
    else:
        print(f"   ⚪ 建议持有/观望")
        print(f"   📌 等待更明确的入场信号")
        if signal['confidence'] > 0.7:
            print(f"   💡 当前置信度较高({signal['confidence']:.1%})，可小仓位试探")
    print("-" * 50)
    
    print_sep("=")
    print(f"报告生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_sep("=")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: an <股票代码> [股票名称]")
        print("示例: an 300061 旗天科技")
        sys.exit(0)
    
    code = sys.argv[1]
    if '.' not in code:
        if code.startswith(('60', '68')):
            ts_code = f"{code}.SH"
        else:
            ts_code = f"{code}.SZ"
    else:
        ts_code = code
    
    name = sys.argv[2] if len(sys.argv) > 2 else ts_code.split('.')[0]
    analyze_stock(ts_code, name)
