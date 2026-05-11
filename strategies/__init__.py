"""
策略模块导出接口

提供策略注册机制和基类导出
"""
from strategies.registry import Registry, StrategyMetadata
from strategies.base.framework_strategy import BaseStrategy

__all__ = [
    'Registry',
    'StrategyMetadata',
    'BaseStrategy',
]