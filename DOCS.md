# 量化交易系统验收报告与详细说明

## 项目概述

本系统是基于 **Kronos（技术预测） + Dexter（基本面研究） + TradingAgents（多智能体决策）** 三工具集成的A股量化分析平台。提供全市场扫描、自选股管理、回测验证、微信推送等功能，支持实盘模拟与策略优化。

---

## 一、系统架构
Tushare数据源 → 缓存层（Parquet） → 分析层（Kronos/Dexter） → 决策层（TradingAgents） → 输出（交易信号/报告）

text

---

## 二、核心模块验收状态

| 模块 | 功能 | 状态 |
|------|------|------|
| Tushare客户端 | 数据获取、增量缓存、限流规避 | ✅ 稳定 |
| Kronos预测器 | 技术信号、置信度（降级策略） | ✅ 稳定 |
| Dexter分析器 | DeepSeek基本面报告 | ✅ 稳定 |
| TradingAgents | 综合决策、理由生成 | ✅ 稳定 |
| 全市场扫描 | 热度排序（换手率70%+小市值30%）+ 技术筛选 | ✅ 稳定 |
| 股票池管理 | add/lst/rmm/clr 命令 | ✅ 稳定 |
| 快捷命令 | kr/tr/an/dexs/sc/aad 等 | ✅ 稳定 |
| 微信推送 | Server酱通知 | ⚠️ 需配置密钥 |
| 回测框架 | Backtrader策略（含移动止盈止损） | ✅ 可用 |

---

## 三、安装与配置

### 1. 克隆仓库
```bash
git clone https://github.com/ADSL8788/quant_trading_system.git
cd quant_trading_system
2. 创建虚拟环境并安装依赖
bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
3. 配置环境变量
bash
cp .env.example .env
# 编辑 .env，填入 TUSHARE_TOKEN 和 DEEPSEEK_API_KEY
4. 验证安装
bash
python -c "from dexter_wrapper import DexterWrapper; d = DexterWrapper(); print('OK')"
四、常用命令详解
命令	说明	示例
kr [代码]	快速技术分析（自选池或单股）	kr 或 kr 300750
tr	三工具完整分析全部自选股	tr
an <代码> <名称>	单股深度分析（含决策理由）	an 600519 贵州茅台
dexs <代码> <名称>	仅 Dexter 基本面研究	dexs 000001 平安银行
sc	全市场热度扫描 + 技术筛选	sc
aad [数量]	一键添加扫描结果前N只（默认20）	aad 10
lst	查看自选股池	lst
add <代码> <名称>	添加自选股	add 600519 贵州茅台
rmm <代码>	删除自选股	rmm 600519
clr	清空所有手动添加的股票	clr
log	查看最近50条日志	log
wx	测试微信推送	wx
五、输出示例
快速分析（kr）输出节选
text
████████████████████████████████████████████████████████████████████████████████
█  KRONOS 量化交易信号报告 (按置信度排序)
█  数据截止日期: 2026-05-08
█  分析范围: 预设精选池 (53只)
████████████████████████████████████████████████████████████████████████████████
  代码           名称             现价        涨跌幅       信号      置信度     操作建议
--------------------------------------------------------------------------------
301219.SZ    腾远钴业         46.77  -0.21%       HOLD        5%       持有等待
002463.SZ    沪电股份         38.47  +2.64%       HOLD        8%       持有等待
...
单股深度分析（an）决策部分
text
🤖 [3/4] 多智能体综合决策
--------------------------------------------------
   最终决策: BUY
   决策理由: Kronos信号BUY(82%)，无明确基本面信号，建议轻仓试探
--------------------------------------------------
💡 [4/4] 综合投资建议
--------------------------------------------------
   ✅ 建议买入
   🔥 置信度: 82.0%
   📊 建议仓位: 30%
全市场扫描（sc）输出节选
text
🔥 热度排序前10只股票（用于技术筛选）:
  ts_code name  turnover_rate     total_mv     heat
002361.SZ 神剑股份        41.6261 2082766.5821 0.997650
002342.SZ 巨力索具        35.5977 2122560.0000 0.896229
...
🏆 Top 20 推荐股票
1. 神剑股份 (002361.SZ) 日期:2026-05-08 收盘:41.63 动量:+41.6% RSI:86 评分:70 强烈关注
六、回测与风控
回测脚本：python run_backtest.py（基于 Backtrader）

策略特性：动态止损（ATR）、时间止损（持仓5天不涨）、移动止盈、大盘择时（沪深300）

示例回测结果（宁德时代 2024-2026）：

初始资金：1,000,000

最终资金：1,015,661

年化收益约 1.57%（含多笔亏损和数笔成功止盈）

七、微信推送配置
注册 Server酱，获取 SendKey

在 .env 中添加：

text
SERVER_CHAN_KEY=你的SendKey
测试：wx

使用 krw、trw 等命令推送报告（需先配置别名）

八、注意事项
首次运行：sc 或 kr 会自动下载K线缓存，耐心等待。

Kronos 模型：当前使用降级策略（简单移动平均），如需真正 Kronos 模型，请参考 Kronos 官方文档安装依赖并修改 analysis_layer/kronos_predictor.py。

Token 安全：.env 文件已加入 .gitignore，切勿提交到公开仓库。

API 限流：Tushare 调用已内置 0.15 秒延时，正常使用不会触发限流。

九、故障排查
问题	可能原因	解决方法
ModuleNotFoundError	依赖未安装	pip install -r requirements.txt
Tushare token不对	.env 中 Token 无效	重新获取 Token 并更新
Dexter 报告为空	DeepSeek API Key 错误或网络问题	检查 .env 中的 DEEPSEEK_API_KEY
缓存未命中	缓存文件损坏或缺失	删除 cache/ 目录后重新运行
git push 失败	需要 Personal Access Token	生成 GitHub PAT 并作为密码输入
十、更新日志
2026-05-09：优化决策理由生成，修复 TradingAgents 返回值处理，完善文档。

2026-05-08：移除涨停因子，改为换手率+小市值热度排序，修正序号显示。

2026-05-07：完成增量缓存、全市场扫描、股票池管理模块。

十一、致谢
本系统基于以下开源项目构建：

Kronos

TradingAgents

Dexter

Tushare

报告生成时间：2026-05-09
系统状态：✅ 验收通过，可投入日常使用

text

### 第四步：输入结束符
粘贴完成后，在新的一行（即文档内容之后）输入：
