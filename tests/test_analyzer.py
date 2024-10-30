# tests/test_analyzer.py
# moomoo-grid-optimizer/tests/test_analyzer.py

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.order_analyzer import GridOrderAnalyzer

def test_basic_analysis():
    analyzer = GridOrderAnalyzer()
    
    # 测试日线数据
    daily_file = os.path.join('data', 'mara-daily-20241001-1028.csv')
    analyzer.load_orders(daily_file)
    daily_suggestions = analyzer.suggest_parameters()
    print("\n日线分析结果:")
    for key, value in daily_suggestions.items():
        print(f"{key}: {value}")
        
    # 测试30分钟线数据
    min30_file = os.path.join('data', 'mara-30min-20241001-1028.csv')
    analyzer.load_orders(min30_file)
    min30_suggestions = analyzer.suggest_parameters()
    print("\n30分钟线分析结果:")
    for key, value in min30_suggestions.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_basic_analysis()