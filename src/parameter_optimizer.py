# src/parameter_optimizer.py
# moomoo-grid-optimizer/src/parameter_optimizer.py

import itertools
from typing import Dict, List
import pandas as pd
from .config import Config
from .backtest_engine import GridBacktester
from tqdm import tqdm
import csv

class ParameterOptimizer:
    """网格策略参数优化器"""
    
    def __init__(self, csv_path: str, timeframe: str):
        """
        初始化优化器
        
        Args:
            csv_path: CSV文件路径
            timeframe: 时间周期 ('daily' or '30min')
        """
        self.timeframe = timeframe
        self.orders_df = self._load_csv(csv_path)
        self.param_ranges = self._get_param_ranges()

    def _load_csv(self, csv_path: str) -> pd.DataFrame:
        """加载并处理CSV数据"""
        try:
            # 尝试以不同格式读取CSV
            try:
                df = pd.read_csv(csv_path, quoting=csv.QUOTE_MINIMAL)
            except:
                df = pd.read_csv(csv_path, quoting=csv.QUOTE_ALL)
            
            # 统一处理时间列
            df['成交时间'] = pd.to_datetime(df['成交时间'].str.strip(), format='%Y/%m/%d %H:%M:%S' if self.timeframe == 'daily' else '%Y/%m/%d %H:%M')
            
            # 确保数值列的类型
            df['成交价格'] = pd.to_numeric(df['成交价格'], errors='coerce')
            df['成交数量'] = pd.to_numeric(df['成交数量'], errors='coerce')
            
            # 过滤有效交易
            df = df[
                (df['交易状态'] == '全部成交') & 
                (df['成交价格'].notna()) & 
                (df['成交数量'].notna())
            ]
            
            return df
            
        except Exception as e:
            raise Exception(f"CSV加载失败: {str(e)}")
        
    def optimize(self) -> List[Dict]:
        """执行参数优化"""
        results = []
        param_combinations = self._generate_param_combinations()
        
        print(f"\n开始{self.timeframe}参数优化...")
        with tqdm(total=len(param_combinations), desc="参数组合测试") as pbar:
            for params in param_combinations:
                backtester = GridBacktester(self.orders_df.copy(), params)
                metrics = backtester.run_backtest()
                
                if self._is_valid_result(metrics, verbose=False):
                    results.append({
                        'params': params,
                        'metrics': metrics
                    })
                pbar.update(1)
        
        # 按收益率排序
        results.sort(key=lambda x: x['metrics']['profit_ratio'], reverse=True)
        
        # 只打印最终结果数量
        if results:
            print(f"\n找到 {len(results)} 组有效参数组合")
        
        return results

    def _is_valid_result(self, metrics: Dict, verbose: bool = False) -> bool:
        """检查回测结果是否满足基本条件"""
        if not metrics:
            return False
        
        checks = {
            '收益率': metrics['profit_ratio'] > Config.BACKTEST_METRICS['min_profit_ratio'],
            '最大回撤': metrics['max_drawdown'] <= Config.BACKTEST_METRICS['max_drawdown'],
            '交易次数': metrics['trade_count'] >= Config.BACKTEST_METRICS['min_trade_count'],
            '胜率': metrics['win_rate'] >= Config.BACKTEST_METRICS['min_win_rate']
        }
        
        return all(checks.values())
        
    def _calculate_order_quantity(self, deviation: float) -> int:
        """计算订单数量"""
        avg_price = self.orders_df['成交价格'].mean()
        grid_capital = Config.INITIAL_CAPITAL * Config.SINGLE_GRID_MAX_RATIO
        
        # 基于网格间距调整数量
        quantity = int(grid_capital / avg_price * deviation * 2)
        # 调整为100的整数倍
        quantity = (quantity // 100) * 100
        
        return max(100, min(quantity, 1000))
    
    def _get_param_ranges(self) -> Dict:
        """获取参数范围设置"""
        # 基于时间周期返回不同的参数范围
        avg_price = self.orders_df['成交价格'].mean()
        price_std = self.orders_df['成交价格'].std()
        volatility = price_std / avg_price
        
        # 根据波动率自适应调整参数范围
        if self.timeframe == 'daily':
            param_ranges = {
                'grid_counts': [3, 5, 7],
                'deviation_ratios': [
                    round(volatility * mult, 3) 
                    for mult in [0.5, 0.75, 1.0]
                ],
                'profit_ratios': [
                    round(volatility * mult, 3) 
                    for mult in [0.3, 0.4, 0.5]
                ],
                'position_steps': [0.2, 0.25, 0.3]
            }
        else:  # 30min
            param_ranges = {
                'grid_counts': [5, 7, 9],
                'deviation_ratios': [
                    round(volatility * mult, 3) 
                    for mult in [0.3, 0.4, 0.5]
                ],
                'profit_ratios': [
                    round(volatility * mult, 3) 
                    for mult in [0.2, 0.3, 0.4]
                ],
                'position_steps': [0.15, 0.2, 0.25]
            }
            
        # 添加每个网格的最大持仓限制
        max_position = int((Config.INITIAL_CAPITAL * 0.8) / avg_price)
        max_position = (max_position // 100) * 100  # 调整为100的整数倍
        
        # 为每个网格数量计算相应的position_limit
        param_ranges['position_limits'] = {
            grid_count: max_position // grid_count
            for grid_count in param_ranges['grid_counts']
        }
        
        return param_ranges

    def _generate_param_combinations(self) -> List[Dict]:
        """生成参数组合"""
        combinations = []
        
        for grid_count in self.param_ranges['grid_counts']:
            position_limit = self.param_ranges['position_limits'][grid_count]
            min_order_quantity = max(100, position_limit // 3)
            
            for deviation in self.param_ranges['deviation_ratios']:
                for profit in self.param_ranges['profit_ratios']:
                    for step in self.param_ranges['position_steps']:
                        params = {
                            'grid_count': grid_count,
                            'price_deviation': deviation,
                            'profit_ratio': profit,
                            'position_step': step,
                            'position_limit': position_limit,
                            'min_order_quantity': min_order_quantity
                        }
                        combinations.append(params)
        
        return combinations
        