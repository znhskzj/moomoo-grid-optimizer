# src/config.py - 配置文件
# moomoo-grid-optimizer/src/config.py

class Config:
    """配置参数管理"""
    
    # 资金配置
    INITIAL_CAPITAL = 100000  # 初始资金
    MAX_CAPITAL_USAGE = 0.8   # 最大资金使用率
    SINGLE_GRID_MAX_RATIO = 0.15  # 单网格最大资金占比
    
    # 网格配置
    DEFAULT_GRID_COUNT = {
        'daily': 5,      # 日线网格数
        '30min': 7,      # 30分钟线网格数
        '5min': 9        # 5分钟线网格数
    }
    
    # 交易参数
    MIN_ORDER_QUANTITY = 100  # 最小交易数量
    MAX_ORDER_QUANTITY = 1000  # 最大交易数量
    
    # 回测评估参数
    MIN_PROFIT_MULTIPLE = 1.5  # 相对买入持有策略的最小收益倍数
    MAX_DRAWDOWN_LIMIT = 0.2   # 最大回撤限制
    
    # 数据文件配置
    DATA_FOLDER = "data"