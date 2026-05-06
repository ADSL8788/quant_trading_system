# 量化交易系统 (Kronos + Dexter + TradingAgents)

基于三智能体的A股量化分析系统，支持技术预测、基本面研究、多智能体决策、全市场扫描、回测与自动预警。

## 功能特性

- **Kronos**：时序模型预测股价趋势，输出 BUY/SELL/HOLD 信号及置信度。
- **Dexter**：DeepSeek 驱动的基本面研究，生成财务、估值、风险报告。
- **TradingAgents**：多角色智能体辩论，输出最终交易决策。
- **全市场扫描**：多因子技术面筛选，支持候选股一键加入自选池。
- **数据缓存**：本地 Parquet 缓存，大幅提升重复分析速度。
- **实盘模拟**：模拟交易，计算总资产、收益率。
- **微信推送**：支持 Server酱/企业微信，可定时推送晨报。
- **回测框架**：基于 Backtrader，验证策略历史表现。

## 快速开始

### 1. 克隆仓库（不含第三方工具）
```bash
git clone https://github.com/ADSL8788/quant_trading_system.git
cd quant_trading_system

# 量化交易系统 (Kronos + Dexter + TradingAgents)

基于三智能体的A股量化分析系统，集成了技术预测（Kronos）、基本面研究（Dexter）和多智能体决策（TradingAgents），支持全市场扫描、数据缓存、回测、微信推送等功能。

## 📌 项目简介

- **Kronos**：时序模型预测股价趋势，输出 BUY/SELL/HOLD 信号及置信度。
- **Dexter**：DeepSeek 驱动的基本面研究，生成财务、估值、风险报告。
- **TradingAgents**：多角色智能体（技术、基本面、风控、交易员、总监）辩论，输出最终交易决策。
- **全市场扫描**：多因子技术面筛选，候选股一键加入自选池。
- **数据缓存**：本地 Parquet 缓存，二次分析秒级响应。
- **回测框架**：基于 Backtrader，验证策略历史表现。
- **实盘模拟**：模拟交易，计算总资产、收益率、持仓。
- **微信推送**：支持 Server酱 / 企业微信，可定时推送晨报。
