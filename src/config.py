# src/config.py - 配置文件
# moomoo-grid-optimizer/src/config.py

class Config:
    """配置参数管理"""
    
    # 资金配置
    INITIAL_CAPITAL = 100000  # 初始资金
    MAX_CAPITAL_USAGE = 0.8   # 最大资金使用率
    SINGLE_GRID_MAX_RATIO = 0.15  # 单网格最大资金占比
    
    # 网格优化范围
    GRID_PARAMS = {
        'daily': {
            'grid_counts': range(3, 9, 2),     # 测试3,5,7个网格
            'deviation_ratios': [0.02, 0.025, 0.03, 0.035, 0.04],  # 网格间距
            'profit_ratios': [0.015, 0.02, 0.025, 0.03],  # 止盈比例
            'position_steps': [0.2, 0.25, 0.3],  # 建仓比例
            'position_limit_ratio': 0.15  # 单网格持仓上限占总资金比例
        },
        '30min': {
            'grid_counts': range(5, 12, 2),    # 测试5,7,9,11个网格
            'deviation_ratios': [0.01, 0.015, 0.02, 0.025, 0.03],
            'profit_ratios': [0.01, 0.015, 0.02, 0.025],
            'position_steps': [0.15, 0.2, 0.25],
            'position_limit_ratio': 0.15
        }
    }

    # 回测评估标准
    BACKTEST_METRICS = {
        'min_profit_ratio': 0.05,    # 最小收益率5%
        'max_drawdown': 0.85,        # 最大回撤限制85%
        'min_trade_count': 10,       # 最小交易次数
        'min_win_rate': 0.25         # 最小胜率25%
    }
    
    # 交易相关
    MIN_ORDER_SIZE = 100    # 最小交易数量
    SIZE_STEP = 100        # 数量步长