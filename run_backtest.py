import backtrader as bt
import tushare as ts
import pandas as pd
from datetime import datetime
from config.settings import config
from backtest_strategy import ThreeToolsStrategy

ts.set_token(config.TUSHARE_TOKEN)
pro = ts.pro_api()

def get_data(code, start, end):
    df = pro.daily(ts_code=code, start_date=start, end_date=end)
    if df.empty:
        return None
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')
    df = df.rename(columns={'trade_date': 'datetime', 'vol': 'volume'})
    df.set_index('datetime', inplace=True)
    data = bt.feeds.PandasData(dataname=df)
    return data

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(ThreeToolsStrategy)
    
    # 添加股票数据（如宁德时代）
    stock_data = get_data('300750.SZ', '20240101', '20260430')
    if stock_data is None:
        print("股票数据获取失败")
        exit()
    cerebro.adddata(stock_data)
    
    # 添加沪深300指数数据（用于大盘择时）
    hs300_data = get_data('000300.SH', '20240101', '20260430')
    if hs300_data is not None:
        cerebro.adddata(hs300_data)  # 第二个数据源，策略中可用 self.datas[1] 访问
        print("✅ 已加载沪深300指数数据")
    else:
        print("⚠️ 沪深300数据获取失败，将忽略大盘择时")
    
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.0003)
    print('初始资金:', cerebro.broker.getvalue())
    cerebro.run()
    print('最终资金:', cerebro.broker.getvalue())
