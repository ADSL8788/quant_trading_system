#!/usr/bin/env python3
"""Dexter 增强版 - 多数据源容灾（国内：Tushare → AkShare → BaoStock；海外：yfinance → Alpha Vantage）"""
import os
import requests
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class DexterWrapper:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url='https://api.deepseek.com/v1'
        )
        self.av_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')  # 可选

    # ---------- 国内数据源（A股）----------
    def _get_tech_data_from_tushare(self, ts_code, days=100):
        try:
            from data_layer.tushare_client import TushareClient
            client = TushareClient()
            df = client.get_kline(ts_code, days=days)
            if df is not None and len(df) >= 50:
                latest = df['close'].iloc[-1]
                ma20 = df['close'].rolling(20).mean().iloc[-1]
                ma60 = df['close'].rolling(60).mean().iloc[-1]
                trend = '上升' if latest > ma60 else '下降'
                return {
                    'source': 'Tushare',
                    'current': latest,
                    'ma20': ma20,
                    'ma60': ma60,
                    'trend': trend,
                }
            return None
        except Exception as e:
            print(f"   ⚠️ Tushare 获取失败: {e}")
            return None

    def _get_tech_data_from_akshare(self, ts_code, days=100):
        try:
            import akshare as ak
            code = ts_code.split('.')[0]
            df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date='19000101', adjust='qfq')
            if df is None or len(df) < 50:
                return None
            df.rename(columns={'日期':'trade_date','收盘':'close'}, inplace=True)
            df['close'] = pd.to_numeric(df['close'])
            df.sort_values('trade_date', ascending=True, inplace=True)
            latest = df['close'].iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            trend = '上升' if latest > ma60 else '下降'
            return {
                'source': 'AkShare',
                'current': latest,
                'ma20': ma20,
                'ma60': ma60,
                'trend': trend,
            }
        except Exception as e:
            print(f"   ⚠️ AkShare 获取失败: {e}")
            return None

    def _get_tech_data_from_baostock(self, ts_code, days=100):
        try:
            import baostock as bs
            code = ts_code.split('.')[0]
            market = 'sh' if ts_code.endswith('.SH') else 'sz'
            bs_code = f"{market}.{code}"
            bs.login()
            end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
            start_date = (pd.Timestamp.now() - pd.Timedelta(days=days*2)).strftime('%Y-%m-%d')
            rs = bs.query_history_k_data_plus(bs_code,
                fields="date,close",
                start_date=start_date, end_date=end_date, frequency="d", adjustflag="2")
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            bs.logout()
            if not data_list:
                return None
            df = pd.DataFrame(data_list, columns=['trade_date','close'])
            df['close'] = df['close'].astype(float)
            df.sort_values('trade_date', inplace=True)
            if len(df) < 50:
                return None
            latest = df['close'].iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            trend = '上升' if latest > ma60 else '下降'
            return {
                'source': 'BaoStock',
                'current': latest,
                'ma20': ma20,
                'ma60': ma60,
                'trend': trend,
            }
        except Exception as e:
            print(f"   ⚠️ BaoStock 获取失败: {e}")
            return None

    # ---------- 海外数据源 ----------
    def _get_overseas_data_from_yfinance(self, symbol):
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info or len(info) == 0:
                return None
            hist = ticker.history(period="6mo")
            if hist.empty or len(hist) < 50:
                current = info.get('regularMarketPrice', info.get('currentPrice', None))
                ma20 = ma60 = None
                trend = '未知'
            else:
                current = hist['Close'].iloc[-1]
                ma20 = hist['Close'].rolling(20).mean().iloc[-1]
                ma60 = hist['Close'].rolling(60).mean().iloc[-1]
                trend = '上升' if current > ma60 else '下降'
            pe = info.get('trailingPE', info.get('forwardPE', 'N/A'))
            pb = info.get('priceToBook', 'N/A')
            market_cap = info.get('marketCap', 'N/A')
            eps = info.get('trailingEps', info.get('forwardEps', 'N/A'))
            dividend_yield = info.get('dividendYield', 'N/A')
            sector = info.get('sector', 'N/A')
            industry = info.get('industry', 'N/A')
            return {
                'source': 'Yahoo Finance',
                'current': current,
                'ma20': ma20,
                'ma60': ma60,
                'trend': trend,
                'pe': pe,
                'pb': pb,
                'market_cap': market_cap,
                'eps': eps,
                'dividend_yield': dividend_yield,
                'sector': sector,
                'industry': industry,
                'name': info.get('longName', info.get('shortName', ''))
            }
        except Exception as e:
            print(f"   ⚠️ Yahoo Finance 获取失败: {e}")
            return None

    def _get_overseas_data_from_alpha_vantage(self, symbol):
        if not self.av_api_key:
            return None
        try:
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.av_api_key}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data and 'Symbol' in data:
                return {
                    'source': 'Alpha Vantage',
                    'name': data.get('Name', ''),
                    'pe': data.get('PERatio', 'N/A'),
                    'pb': data.get('PriceToBookRatio', 'N/A'),
                    'eps': data.get('EPS', 'N/A'),
                    'dividend_yield': data.get('DividendYield', 'N/A'),
                    'market_cap': data.get('MarketCapitalization', 'N/A'),
                    'sector': data.get('Sector', 'N/A'),
                    'industry': data.get('Industry', 'N/A'),
                    'week52_high': data.get('WeekHigh52', 'N/A'),
                    'week52_low': data.get('WeekLow52', 'N/A')
                }
            return None
        except Exception as e:
            print(f"   ⚠️ Alpha Vantage 获取失败: {e}")
            return None

    # ---------- 财务数据（A股）----------
    def _get_financial_data(self, ts_code):
        try:
            from data_layer.tushare_client import TushareClient
            client = TushareClient()
            df = client.pro.daily_basic(ts_code=ts_code, fields='pe,pe_ttm,pb,ps,ps_ttm,total_mv')
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                return f"市盈率TTM: {latest.get('pe_ttm', 'N/A')}, 市净率: {latest.get('pb', 'N/A')}, 总市值: {latest.get('total_mv', 'N/A')}"
        except Exception:
            pass
        return "财务数据暂无法获取"

    # ---------- 主入口 ----------
    def research_stock(self, ts_code, stock_name):
        is_a_share = ts_code.endswith('.SH') or ts_code.endswith('.SZ')
        price_info = ""
        finance_info = ""

        if is_a_share:
            # 国内：三级容灾
            tech_data = self._get_tech_data_from_tushare(ts_code)
            if not tech_data:
                tech_data = self._get_tech_data_from_akshare(ts_code)
            if not tech_data:
                tech_data = self._get_tech_data_from_baostock(ts_code)

            if tech_data:
                price_info = f"""
【技术面 - 数据源: {tech_data['source']}】
当前价格: {tech_data['current']:.2f}
20日均线: {tech_data['ma20']:.2f}
60日均线: {tech_data['ma60']:.2f}
趋势: {tech_data['trend']}
"""
            else:
                price_info = "\n【技术面】无法获取有效K线数据，跳过技术分析。\n"

            finance_str = self._get_financial_data(ts_code)
            finance_info = f"\n【基本面概览】{finance_str}\n"
        else:
            # 海外：优先 Yahoo Finance
            yf_data = self._get_overseas_data_from_yfinance(ts_code)
            if yf_data:
                price_info = f"""
【技术面 - 数据源: {yf_data['source']}】
名称: {yf_data.get('name', stock_name)}
当前价格: {yf_data['current']:.2f}
"""
                if yf_data.get('ma20') is not None and yf_data.get('ma60') is not None:
                    price_info += f"20日均线: {yf_data['ma20']:.2f}\n60日均线: {yf_data['ma60']:.2f}\n趋势: {yf_data['trend']}\n"
                finance_info = f"""
【基本面摘要 - {yf_data['source']}】
市盈率: {yf_data['pe']}
市净率: {yf_data['pb']}
每股收益(EPS): {yf_data['eps']}
股息率: {yf_data['dividend_yield']}
市值: {yf_data['market_cap']}
行业: {yf_data['sector']} - {yf_data['industry']}
"""
            else:
                price_info = "\n【技术面】海外数据获取失败，尝试 Alpha Vantage 备选...\n"
                finance_info = ""

            # 补充 Alpha Vantage 数据（如果 yfinance 缺失关键指标）
            if not yf_data or (yf_data and yf_data.get('pe') == 'N/A' and self.av_api_key):
                av_data = self._get_overseas_data_from_alpha_vantage(ts_code)
                if av_data:
                    finance_info += f"""
【补充基本面 - {av_data['source']}】
市盈率: {av_data['pe']}
市净率: {av_data['pb']}
每股收益: {av_data['eps']}
股息率: {av_data['dividend_yield']}
市值: {av_data['market_cap']}
52周区间: {av_data['week52_low']} - {av_data['week52_high']}
行业: {av_data['sector']} - {av_data['industry']}
"""
            if not yf_data and not av_data:
                price_info = "\n【海外数据】所有数据源均失败，请检查网络或API配置。\n"

        prompt = f"""你是一位专业的金融研究员。请对{stock_name}({ts_code})进行全面分析：

{price_info}
{finance_info}

请按以下框架输出：
1. 财务健康度
2. 估值分析
3. 技术面分析
4. 风险因素
5. 投资结论（买入/持有/卖出）及目标价

输出简明扼要，不要多余解释。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            return {"success": True, "analysis": response.choices[0].message.content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def research(self, query):
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": query}],
                temperature=0.3,
                max_tokens=1500
            )
            return {"success": True, "stdout": response.choices[0].message.content}
        except Exception as e:
            return {"success": False, "error": str(e)}
