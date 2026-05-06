import backtrader as bt
import sys
import os
sys.path.append(os.path.dirname(__file__))
import pandas as pd
from analysis_layer.kronos_predictor import KronosPredictor

class ThreeToolsStrategy(bt.Strategy):
    params = (
        ('stoploss', 0.10),
        ('takeprofit', 0.15),
        ('size', 0.15),
        ('min_confidence', 0.35),
        ('trend_period', 120),   # 趋势均线周期（120日≈半年）
    )

    def __init__(self):
        self.kronos = KronosPredictor()
        self.order = None
        self.last_confidence = 0.3
        self.atr = bt.indicators.ATR(self.data, period=14)
        # 趋势指标：120日均线
        self.trend_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.trend_period)

    def log(self, txt):
        print(f'{self.data.datetime.date(0)} {txt}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.log(f'交易执行: {order.executed.price} 数量 {order.executed.size}')
            self.order = None

    def get_dynamic_size(self, price):
        ratio = min(0.20, self.params.size + (self.last_confidence - 0.5) * 0.2)
        size = int(self.broker.getvalue() * ratio / price)
        size = (size // 100) * 100
        return max(100, size)

    def next(self):
        if self.order:
            return
        if len(self.data) < self.p.trend_period:
            return

        # 趋势向上条件：价格高于 120 日均线
        uptrend = self.data.close[0] > self.trend_ma[0]

        # 构建过去200天的DataFrame（用于Kronos）
        dates = [self.data.datetime.date(-i) for i in range(200)][::-1]
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(dates),
            'open': [self.data.open[-i] for i in range(200)][::-1],
            'high': [self.data.high[-i] for i in range(200)][::-1],
            'low': [self.data.low[-i] for i in range(200)][::-1],
            'close': [self.data.close[-i] for i in range(200)][::-1],
            'volume': [self.data.volume[-i] for i in range(200)][::-1],
        })
        kronos_signal = self.kronos.predict(df)
        self.last_confidence = kronos_signal.get('confidence', 0.3)
        action = kronos_signal.get('action', 'HOLD')
        current_price = self.data.close[0]
        atr_value = self.atr[0]

        # 买入：BUY信号 + 趋势向上 + 置信度足够
        if action == 'BUY' and not self.position and self.last_confidence >= self.params.min_confidence and uptrend:
            size = self.get_dynamic_size(current_price)
            self.order = self.buy(size=size)
            self.log(f'买入 {size}股 @ {current_price:.2f} (置信度:{self.last_confidence:.0%}, 趋势向上)')

        # 卖出
        elif self.position:
            pnl = (current_price - self.position.price) / self.position.price
            dynamic_stop = self.position.price - 2 * atr_value
            if action == 'SELL' or pnl <= -self.params.stoploss or current_price <= dynamic_stop:
                self.order = self.sell(size=self.position.size)
                reason = '信号' if action == 'SELL' else '止损' if pnl <= -self.params.stoploss else '动态止损'
                self.log(f'{reason}卖出 @ {current_price:.2f} (盈亏:{pnl:.2%})')
            elif pnl >= self.params.takeprofit:
                self.order = self.sell(size=self.position.size)
                self.log(f'止盈卖出 @ {current_price:.2f} (盈利:{pnl:.2%})')
