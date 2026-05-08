#!/usr/bin/env python3
"""单股深度分析 - 显示详细报告（含决策理由）"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor
from dexter_wrapper import DexterWrapper
from trading_agents_wrapper import TradingAgentsWrapper

def analyze_stock(ts_code, name):
    print("=" * 70)
    print(f"🔍 深度分析: {name} ({ts_code})")
    print("=" * 70)
    
    # Kronos
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
    print(f"   当前价: {signal.get('current_price', df['close'].iloc[-1]):.2f}")
    
    # Dexter 详细报告
    print("\n📚 [2/4] Dexter 基本面研究报告")
    print("-" * 50)
    dexter = DexterWrapper()
    result = dexter.research_stock(ts_code, name)
    if result.get("success"):
        report = result.get("analysis", "")
        print(report[:2000])
        if len(report) > 2000:
            print(f"\n... (报告共 {len(report)} 字，已截断)")
    else:
        print("   ❌ 分析失败")
    print("-" * 50)
    
    # TradingAgents
    print("\n🤖 [3/4] 多智能体综合决策")
    print("-" * 50)
    agents = TradingAgentsWrapper()
    decision_obj = agents.decide(ts_code, name, signal, report if result.get("success") else None)
    # decision_obj 格式: {"success": bool, "decision": {"action": str, "reason": str, ...}}
    final_decision = decision_obj.get("decision", {})
    final_action = final_decision.get("action", "HOLD")
    final_reason = final_decision.get("reason", "无")
    print(f"   最终决策: {final_action}")
    print(f"   决策理由: {final_reason}")
    print("-" * 50)
    
    # 综合投资建议
    print("\n💡 [4/4] 综合投资建议")
    print("-" * 50)
    if final_action == "BUY":
        print("   ✅ 建议买入")
        print(f"   🔥 置信度: {signal['confidence']:.1%}")
        print(f"   📊 建议仓位: {min(30, int(signal['confidence']*100))}%")
    elif final_action == "SELL":
        print("   ❌ 建议卖出")
        print(f"   ⚠️ 理由: {final_reason[:100]}")
    else:
        print("   ⚪ 建议持有/观望")
        print("   📌 等待更明确的入场信号")
    print("-" * 50)
    
    print("=" * 70)
    print(f"报告生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: an <股票代码> [股票名称]")
        print("示例: an 600519 贵州茅台")
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
