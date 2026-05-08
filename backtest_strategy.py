import backtrader as bt
import sys
import os
sys.path.append(os.path.dirname(__file__))
import pandas as pd
from analysis_layer.kronos_predictor import KronosPredictor

class ThreeToolsStrategy(bt.Strategy):
    params = (
        ('stoploss', 0.07),
        ('takeprofit', 0.15),
        ('size', 0.15),
        ('min_confidence', 0.35),
        ('trailing_profit_start', 0.08),
        ('trailing_profit_drawdown', 0.03),
        ('max_hold_days', 5),
    )

    def __init__(self):
        self.kronos = KronosPredictor()
        self.order = None
        self.last_confidence = 0.3
        self.atr = bt.indicators.ATR(self.data, period=14)
        # 沪深300指标（如果有第二个数据源）
        if len(self.datas) > 1:
            self.hs300_ma = bt.indicators.SimpleMovingAverage(self.datas[1].close, period=20)
        else:
            self.hs300_ma = None
        # 60日均线指标（用于趋势过滤）
        self.ma60 = bt.indicators.SimpleMovingAverage(self.data.close, period=60)
        # 记录持仓相关信息
        self.entry_price = 0
        self.entry_bar = 0
        self.highest_price = 0

    def log(self, txt):
        print(f'{self.data.datetime.date(0)} {txt}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.entry_bar = len(self.data)
                self.highest_price = order.executed.price
                self.log(f'买入 {order.executed.size}股 @ {order.executed.price:.2f}')
            else:
                shares = order.executed.size
                pnl = (order.executed.price - self.entry_price) / self.entry_price if self.entry_price else 0
                self.log(f'卖出 {shares}股 @ {order.executed.price:.2f} (盈亏:{pnl:.2%})')
            self.order = None

    def get_dynamic_size(self, price):
        ratio = min(0.20, self.params.size + (self.last_confidence - 0.5) * 0.2)
        size = int(self.broker.getvalue() * ratio / price)
        size = (size // 100) * 100
        return max(100, size)

    def next(self):
        if self.order:
            return
        if len(self.data) < 60:
            return

        # ========== 大盘择时（只影响开仓） ==========
        market_ok = True
        if self.hs300_ma is not None:
            # 确保沪深300数据已足够
            if len(self.datas[1]) >= 20:
                hs300_close = self.datas[1].close[0]
                hs300_ma20 = self.hs300_ma[0]
                if hs300_close <= hs300_ma20:
                    market_ok = False
        # ========== 处理持仓（止盈止损、时间止损、移动止盈） ==========
        if self.position:
            current_price = self.data.close[0]
            pnl = (current_price - self.entry_price) / self.entry_price if self.entry_price else 0
            hold_bars = len(self.data) - self.entry_bar

            # 更新最高价
            if current_price > self.highest_price:
                self.highest_price = current_price

            # 移动止盈
            if pnl >= self.params.trailing_profit_start:
                if current_price < self.highest_price * (1 - self.params.trailing_profit_drawdown):
                    self.log(f"移动止盈触发（最高{self.highest_price:.2f}，现价{current_price:.2f}）")
                    self.order = self.sell(size=self.position.size)
                    return
            # 时间止损
            if hold_bars > self.params.max_hold_days and pnl <= 0:
                self.log(f"时间止损触发（持仓{hold_bars}天，盈亏{pnl:.2%})")
                self.order = self.sell(size=self.position.size)
                return
            # 硬止损
            if pnl <= -self.params.stoploss:
                self.log(f"硬止损触发 (亏损{pnl:.2%})")
                self.order = self.sell(size=self.position.size)
                return
            # 固定止盈（若未触发移动止盈但达到目标也可卖出）
            if pnl >= self.params.takeprofit:
                self.log(f"固定止盈触发 (盈利{pnl:.2%})")
                self.order = self.sell(size=self.position.size)
                return

        # ========== 开仓信号 ==========
        if not self.position and market_ok:
            # 构建过去200天的DataFrame（用于Kronos）
            if len(self.data) < 200:
                return
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
            # 中期趋势过滤：价格必须高于60日均线
            trend_ok = current_price > self.ma60[0]
            if action == 'BUY' and self.last_confidence >= self.params.min_confidence and trend_ok:
                size = self.get_dynamic_size(current_price)
                self.order = self.buy(size=size)
