# src/backtest_engine.py
# moomoo-grid-optimizer/src/backtest_engine.py

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from .config import Config
from tqdm import tqdm

class GridBacktester:
    """网格策略回测引擎"""
    
    def __init__(self, orders_df: pd.DataFrame, params: Dict):
        """
        初始化回测引擎
        
        Args:
            orders_df: 历史订单数据
            params: 策略参数
        """
        self.orders_df = orders_df
        self.params = params
        self.positions = {}
        self.trades = []
        self.cash = Config.INITIAL_CAPITAL
        self.grid_prices = []
        
    def run_backtest(self) -> Dict:
        """执行回测"""
        self._initialize_grids(verbose=False)  # 关闭初始化时的详细输出
        
        valid_orders = self.orders_df[
            (self.orders_df['成交时间'].notna()) & 
            (self.orders_df['成交价格'] > 0)
        ].sort_values('成交时间')
        
        trade_count = 0
        for _, row in tqdm(valid_orders.iterrows(), desc="回测进行中", 
                          disable=True):  # 关闭单个回测的进度条
            price = row['成交价格']
            time = row['成交时间']
            
            buys = self._check_buy_signals(price, time)
            sells = self._check_sell_signals(price, time)
            trade_count += len(buys) + len(sells)
        
        metrics = self._calculate_metrics()
        return metrics
        
    def _initialize_grids(self, verbose: bool = True):
        """
        初始化网格价格
        
        Args:
            verbose: 是否打印详细信息
        """
        avg_price = self.orders_df['成交价格'].mean()
        grid_count = self.params['grid_count']
        deviation = self.params['price_deviation']
        
        self.grid_prices = []
        half_grids = grid_count // 2
        
        if verbose:
            print("\n初始化网格:")
            print(f"平均价格: {avg_price:.2f}")
            print(f"网格数量: {grid_count}")
            print(f"价格偏差: {deviation:.3f}")
        
        for i in range(-half_grids, half_grids + 1):
            grid_price = avg_price * (1 + i * deviation)
            grid_price = round(grid_price, 2)  # 保留两位小数
            self.grid_prices.append(grid_price)
            self.positions[grid_price] = 0
            
            if verbose:
                print(f"网格 {i+half_grids+1}: {grid_price:.2f}")
            
    def _check_buy_signals(self, price: float, time: pd.Timestamp) -> List[Dict]:
        """检查买入信号"""
        signals = []
        for grid_price in self.grid_prices:
            if (price <= grid_price and 
                self.positions.get(grid_price, 0) < self.params['position_limit']):
                signal = {
                    'grid_price': grid_price,
                    'price': price,
                    'time': time
                }
                signals.append(signal)
                self._execute_buy(grid_price, price, time)
        return signals

    def _check_sell_signals(self, price: float, time: pd.Timestamp) -> List[Dict]:
        """检查卖出信号"""
        signals = []
        for grid_price in self.grid_prices:
            if self.positions.get(grid_price, 0) > 0:
                profit_ratio = (price - grid_price) / grid_price
                if profit_ratio >= self.params['profit_ratio']:
                    signal = {
                        'grid_price': grid_price,
                        'price': price,
                        'time': time,
                        'profit_ratio': profit_ratio
                    }
                    signals.append(signal)
                    self._execute_sell(grid_price, price, time)
        return signals
                    
    def _execute_buy(self, grid_price: float, price: float, time: pd.Timestamp):
        """执行买入"""
        quantity = self.params['min_order_quantity']
        cost = quantity * price
        
        if cost <= self.cash:
            self.cash -= cost
            self.positions[grid_price] += quantity
            self.trades.append({
                'time': time,
                'type': 'buy',
                'price': price,
                'quantity': quantity,
                'grid_price': grid_price
            })
            
    def _execute_sell(self, grid_price: float, price: float, time: pd.Timestamp):
        """执行卖出"""
        quantity = self.positions[grid_price]
        revenue = quantity * price
        
        self.cash += revenue
        self.positions[grid_price] = 0
        self.trades.append({
            'time': time,
            'type': 'sell',
            'price': price,
            'quantity': quantity,
            'grid_price': grid_price
        })
        
    def _calculate_metrics(self) -> Dict:
        """计算回测指标"""
        if not self.trades:
            return {}
            
        trades_df = pd.DataFrame(self.trades)
        
        # 计算收益
        total_value = self.cash
        for grid_price, qty in self.positions.items():
            if qty > 0:
                current_price = trades_df['price'].iloc[-1]
                total_value += qty * current_price
        
        profit = total_value - Config.INITIAL_CAPITAL
        profit_ratio = profit / Config.INITIAL_CAPITAL
        
        return {
            'total_profit': profit,
            'profit_ratio': profit_ratio,
            'trade_count': len(trades_df),
            'win_rate': len(trades_df[trades_df['price'] > trades_df['grid_price']]) / len(trades_df) if len(trades_df) > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(trades_df),
            'final_value': total_value
        }
        
    def _calculate_max_drawdown(self, trades_df: pd.DataFrame) -> float:
        """计算最大回撤"""
        if len(trades_df) == 0:
            return 0
            
        equity_curve = []
        current_equity = Config.INITIAL_CAPITAL
        
        for _, trade in trades_df.iterrows():
            if trade['type'] == 'buy':
                current_equity -= trade['price'] * trade['quantity']
            else:
                current_equity += trade['price'] * trade['quantity']
            equity_curve.append(current_equity)
            
        equity_curve = np.array(equity_curve)
        peak = equity_curve[0]
        max_drawdown = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
            
        return max_drawdown
    
    def _is_valid_result(self, metrics: Dict) -> bool:
        """检查回测结果是否满足基本条件"""
        # 放宽检查条件
        if not metrics:
            return False
            
        return (
            metrics['profit_ratio'] > 0 and  # 只要有盈利就接受
            metrics['max_drawdown'] <= Config.BACKTEST_METRICS['max_drawdown'] and
            metrics['trade_count'] >= Config.BACKTEST_METRICS['min_trade_count']
        )