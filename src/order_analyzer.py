# src/order_analyzer.py - 订单分析核心
# moomoo-grid-optimizer/src/order_analyzer.py

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from .config import Config

class GridOrderAnalyzer:
    """分析网格交易订单数据，为策略参数优化提供建议"""
    
    def __init__(self, initial_capital: float = Config.INITIAL_CAPITAL):
        """
        初始化分析器
        
        Args:
            initial_capital: 初始资金量
        """
        self.initial_capital = initial_capital
        self.orders_df = None
        self.symbol = None
        self.avg_price = None
        self.time_frame = None  # 'daily' or '30min'
        
    def load_orders(self, file_path: str) -> None:
        """
        加载订单数据并进行初步处理
        
        Args:
            file_path: CSV文件路径
        """
        df = pd.read_csv(file_path)
        df['成交时间'] = pd.to_datetime(df['成交时间'])
        df = df[df['交易状态'] == '全部成交'].copy()
        
        # 判断时间周期
        time_diffs = df['成交时间'].diff().dropna()
        median_diff = time_diffs.median()
        if median_diff.total_seconds() >= 24*3600:
            self.time_frame = 'daily'
        else:
            self.time_frame = '30min'
            
        self.orders_df = df
        self.symbol = df['代码'].iloc[0]
        self.avg_price = df['成交价格'].mean()
        
    def analyze_price_movement(self) -> Dict:
        """
        分析价格波动特征
        
        Returns:
            Dict: 包含价格分析结果的字典
        """
        if self.orders_df is None:
            return {}
            
        prices = self.orders_df['成交价格']
        
        # 计算日内波动率
        volatility_daily = self._calculate_intraday_volatility()
        
        return {
            'mean_price': prices.mean(),
            'price_std': prices.std(),
            'price_range': prices.max() - prices.min(),
            'volatility': prices.std() / prices.mean(),
            'daily_volatility': volatility_daily
        }
    
    def _calculate_intraday_volatility(self) -> float:
        """计算日内波动率"""
        if self.time_frame == 'daily':
            return self.orders_df['成交价格'].std() / self.orders_df['成交价格'].mean()
            
        # 对于30分钟数据，按天分组计算
        df = self.orders_df.copy()
        df['date'] = df['成交时间'].dt.date
        daily_volatility = df.groupby('date')['成交价格'].agg(['std', 'mean'])
        daily_volatility['volatility'] = daily_volatility['std'] / daily_volatility['mean']
        return daily_volatility['volatility'].mean()
        
    def suggest_parameters(self) -> Dict:
        """
        基于分析结果提供参数建议
        
        Returns:
            Dict: 包含建议参数的字典
        """
        if self.orders_df is None:
            return {}
            
        price_analysis = self.analyze_price_movement()
        volatility = price_analysis['volatility']
        
        # 根据不同时间周期调整参数
        grid_count = Config.DEFAULT_GRID_COUNT[self.time_frame]
        price_deviation = round(volatility * (0.5 if self.time_frame == 'daily' else 0.3), 3)
        
        # 基础建议
        suggestions = {
            'time_frame': self.time_frame,
            'grid_count': grid_count,
            'single_grid_amount': self.initial_capital * Config.SINGLE_GRID_MAX_RATIO,
            'position_limit': int((self.initial_capital * Config.MAX_CAPITAL_USAGE) / self.avg_price),
            'price_deviation': price_deviation,
            'min_profit_ratio': round(volatility * 0.3, 3)
        }
        
        # 计算建议的单次交易数量
        single_trade_amount = min(
            int(suggestions['single_grid_amount'] / self.avg_price),
            int(suggestions['position_limit'] * 0.2)
        )
        # 调整为100的整数倍
        single_trade_amount = (single_trade_amount // 100) * 100
        suggestions['min_order_quantity'] = max(
            Config.MIN_ORDER_QUANTITY,
            min(single_trade_amount, Config.MAX_ORDER_QUANTITY)
        )
        
        return suggestions