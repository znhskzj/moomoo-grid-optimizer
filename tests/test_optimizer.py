# tests/test_optimizer.py
# moomoo-grid-optimizer/tests/test_optimizer.py

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parameter_optimizer import ParameterOptimizer
import pandas as pd

def test_parameter_optimization():
    try:
        # 测试日线数据
        daily_file = os.path.join('data', 'mara-daily-20241001-1028.csv')
        daily_optimizer = ParameterOptimizer(daily_file, 'daily')
        daily_results = daily_optimizer.optimize()
        print_results(daily_results, '日线')
        
        # 测试30分钟线数据
        min30_file = os.path.join('data', 'mara-30min-20241001-1028.csv')
        min30_optimizer = ParameterOptimizer(min30_file, '30min')
        min30_results = min30_optimizer.optimize()
        print_results(min30_results, '30分钟线')
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        print(traceback.format_exc())

def print_results(results, timeframe):
    if not results:
        print(f"\n{timeframe}: 未找到满足条件的参数组合")
        return
    
    print(f"\n{timeframe}最优参数组合 TOP 3:")
    for i, result in enumerate(results[:3], 1):
        metrics = result['metrics']
        params = result['params']
        
        print(f"\n[{i}] 性能指标:")
        print(f"    收益率: {metrics['profit_ratio']:.2%}")
        print(f"    最大回撤: {metrics['max_drawdown']:.2%}")
        print(f"    交易次数: {metrics['trade_count']}")
        print(f"    胜率: {metrics['win_rate']:.2%}")
        
        print(f"    参数配置:")
        print(f"    - 网格数量: {params['grid_count']}")
        print(f"    - 网格间距: {params['price_deviation']:.3f}")
        print(f"    - 获利比例: {params['profit_ratio']:.3f}")
        print(f"    - 仓位步长: {params['position_step']:.3f}")
        print(f"    - 单格上限: {params['position_limit']}")
        print(f"    - 单次数量: {params['min_order_quantity']}")

if __name__ == "__main__":
    test_parameter_optimization()