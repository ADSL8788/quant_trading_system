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
    data = get_data('300750.SZ', '20250101', '20260430')
    if data is not None:
        cerebro.adddata(data)
        cerebro.broker.setcash(1000000)
        cerebro.broker.setcommission(commission=0.0003)
        print('初始资金:', cerebro.broker.getvalue())
        cerebro.run()
        print('最终资金:', cerebro.broker.getvalue())
    else:
        print('数据获取失败')
