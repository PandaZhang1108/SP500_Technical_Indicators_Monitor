#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强西格尔策略核心实现
该策略基于多信号组合和动态仓位管理，旨在提供稳定的风险调整收益
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List, Optional


class EnhancedSiegelStrategy:
    """增强西格尔策略实现类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化策略参数
        
        Args:
            config: 策略配置参数字典
        """
        # 默认配置
        self.default_config = {
            'ma_long': 45,  # 长期移动平均线周期（主趋势信号）
            'ma_short': 20,  # 短期移动平均线周期（趋势强度信号）
            'rsi_period': 14,  # RSI周期
            'macd_fast': 12,  # MACD快线
            'macd_slow': 26,  # MACD慢线
            'macd_signal': 9,  # MACD信号线
            'adx_period': 14,  # ADX周期
            'atr_period': 14,  # ATR周期
            'atr_multiplier': 2.5,  # ATR乘数（用于止损）
            'signal_threshold': 0.5,  # 基础信号阈值
            'strong_signal': 0.75,  # 强信号阈值
            'very_strong_signal': 0.9,  # 极强信号阈值
            'weak_signal': 0.65,  # 弱信号阈值
            # 信号权重
            'trend_weight': 0.4,  # 主趋势信号权重
            'slope_weight': 0.25,  # 趋势强度信号权重
            'momentum_weight': 0.2,  # 动量信号权重
            'environment_weight': 0.15,  # 市场环境信号权重
        }
        
        # 使用用户配置覆盖默认配置
        self.config = self.default_config.copy()
        if config:
            self.config.update(config)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            data: 包含OHLC数据的DataFrame
            
        Returns:
            添加了技术指标的DataFrame
        """
        df = data.copy()
        
        # 1. 计算移动平均线
        df[f'MA{self.config["ma_long"]}'] = df['close'].rolling(window=self.config['ma_long']).mean()
        df[f'MA{self.config["ma_short"]}'] = df['close'].rolling(window=self.config['ma_short']).mean()
        
        # 2. 计算短期MA斜率
        df['MA_slope'] = df[f'MA{self.config["ma_short"]}'].diff(4) / df[f'MA{self.config["ma_short"]}'].shift(4)
        
        # 3. 计算RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=self.config['rsi_period']).mean()
        avg_loss = loss.rolling(window=self.config['rsi_period']).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 4. 计算MACD
        ema_fast = df['close'].ewm(span=self.config['macd_fast'], adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.config['macd_slow'], adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_signal'] = df['MACD'].ewm(span=self.config['macd_signal'], adjust=False).mean()
        df['MACD_hist'] = df['MACD'] - df['MACD_signal']
        
        # 5. 计算ADX
        # 简化版ADX计算
        tr1 = abs(df['high'] - df['low'])
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=self.config['atr_period']).mean()
        
        # 简化版ADX
        df['ADX'] = abs(df[f'MA{self.config["ma_short"]}'].diff(2) / df[f'MA{self.config["ma_short"]}'].shift(2) * 100).rolling(window=self.config['adx_period']).mean()
        
        # 6. 计算波动率（基于ATR的相对波动率）
        df['Volatility'] = df['ATR'] / df['close'] * 100
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            添加了信号的DataFrame
        """
        # 复制数据框
        data = df.copy()
        
        # 1. 主趋势信号 (0-1)
        data['trend_signal'] = np.where(
            data['close'] > data[f'MA{self.config["ma_long"]}'],
            1.0,  # 价格在长期均线上方，看多
            0.0   # 价格在长期均线下方，看空
        )
        
        # 2. 趋势强度信号 (0-1)
        # 标准化MA斜率到0-1区间
        max_slope = data['MA_slope'].rolling(window=52).max()
        min_slope = data['MA_slope'].rolling(window=52).min()
        data['slope_signal'] = (data['MA_slope'] - min_slope) / (max_slope - min_slope)
        data['slope_signal'] = data['slope_signal'].clip(0, 1)  # 限制在0-1范围内
        
        # 3. 动量信号 (0-1)
        # 组合RSI和MACD
        # RSI标准化 (0-100 -> 0-1)
        data['rsi_norm'] = data['RSI'] / 100
        
        # MACD标准化到0-1
        max_macd = data['MACD_hist'].rolling(window=52).max()
        min_macd = data['MACD_hist'].rolling(window=52).min()
        data['macd_norm'] = (data['MACD_hist'] - min_macd) / (max_macd - min_macd)
        data['macd_norm'] = data['macd_norm'].clip(0, 1)
        
        # 组合RSI和MACD为动量信号
        data['momentum_signal'] = 0.5 * data['rsi_norm'] + 0.5 * data['macd_norm']
        
        # 4. 市场环境信号 (0-1)
        # 基于ADX和波动率
        # ADX标准化 (通常0-100 -> 0-1)
        data['adx_norm'] = data['ADX'] / 100
        data['adx_norm'] = data['adx_norm'].clip(0, 1)
        
        # 波动率标准化 (反向，波动率低为好)
        max_vol = data['Volatility'].rolling(window=52).max()
        min_vol = data['Volatility'].rolling(window=52).min()
        data['vol_norm'] = 1 - (data['Volatility'] - min_vol) / (max_vol - min_vol)
        data['vol_norm'] = data['vol_norm'].clip(0, 1)
        
        # 组合ADX和波动率为市场环境信号
        data['environment_signal'] = 0.6 * data['adx_norm'] + 0.4 * data['vol_norm']
        
        # 5. 综合信号 (加权平均)
        data['composite_signal'] = (
            self.config['trend_weight'] * data['trend_signal'] +
            self.config['slope_weight'] * data['slope_signal'] +
            self.config['momentum_weight'] * data['momentum_signal'] +
            self.config['environment_weight'] * data['environment_signal']
        )
        
        return data
    
    def calculate_position_size(self, signal_value: float) -> float:
        """
        根据信号强度计算仓位大小
        
        Args:
            signal_value: 综合信号值 (0-1)
            
        Returns:
            仓位大小 (0-1.4)
        """
        if signal_value >= self.config['very_strong_signal']:
            return 1.4  # 极强信号，140%仓位
        elif signal_value >= self.config['strong_signal']:
            return 1.2  # 强信号，120%仓位
        elif signal_value >= self.config['signal_threshold']:
            if signal_value < self.config['weak_signal']:
                return 0.8  # 弱信号，80%仓位
            return 1.0  # 中等信号，100%仓位
        else:
            return 0.0  # 无信号，0%仓位
    
    def calculate_stop_loss(self, data: pd.DataFrame, current_index: int) -> float:
        """
        计算止损价格
        
        Args:
            data: 数据框
            current_index: 当前索引
            
        Returns:
            止损价格
        """
        # 1. 基于ATR的动态止损
        atr_stop = data.iloc[current_index]['close'] - (data.iloc[current_index]['ATR'] * self.config['atr_multiplier'])
        
        # 2. 技术位止损（20周均线）
        ma_stop = data.iloc[current_index][f'MA{self.config["ma_short"]}']
        
        # 使用两种止损中较高者
        return max(atr_stop, ma_stop)
    
    def run_strategy(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        运行策略并返回结果
        
        Args:
            data: 包含OHLC数据的DataFrame
            
        Returns:
            包含信号和仓位的DataFrame，以及策略统计信息
        """
        # 确保数据按日期排序
        df = data.copy().sort_index()
        
        # 计算技术指标
        df = self.calculate_indicators(df)
        
        # 生成信号
        df = self.generate_signals(df)
        
        # 计算仓位
        df['position'] = df['composite_signal'].apply(self.calculate_position_size)
        
        # 计算每日止损价格
        stop_loss_prices = []
        for i in range(len(df)):
            if i < max(self.config['ma_long'], self.config['adx_period']):
                stop_loss_prices.append(np.nan)
            else:
                stop_loss_prices.append(self.calculate_stop_loss(df, i))
        
        df['stop_loss'] = stop_loss_prices
        
        # 计算策略统计信息
        stats = self.calculate_stats(df)
        
        return df, stats
    
    def calculate_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算策略统计信息
        
        Args:
            df: 包含信号和仓位的DataFrame
            
        Returns:
            策略统计信息字典
        """
        # 删除NaN值以进行计算
        clean_df = df.dropna(subset=['position'])
        
        # 计算交易信号变化点
        clean_df['position_change'] = clean_df['position'].diff().fillna(0)
        trades = clean_df[clean_df['position_change'] != 0]
        
        # 计算胜率
        if len(trades) > 1:
            # 简化的胜率计算（基于信号方向和价格变化）
            trades['next_return'] = trades['close'].shift(-1) / trades['close'] - 1
            trades['win'] = (trades['position'] > 0) & (trades['next_return'] > 0) | (trades['position'] == 0) & (trades['next_return'] < 0)
            win_rate = trades['win'].sum() / len(trades)
        else:
            win_rate = float('nan')
        
        # 计算最大回撤
        clean_df['equity_curve'] = (1 + (clean_df['close'].pct_change() * clean_df['position'].shift(1))).cumprod()
        clean_df['equity_curve'].fillna(1, inplace=True)
        clean_df['previous_peak'] = clean_df['equity_curve'].cummax()
        clean_df['drawdown'] = (clean_df['equity_curve'] / clean_df['previous_peak']) - 1
        max_drawdown = clean_df['drawdown'].min()
        
        # 计算年化收益率
        total_days = (clean_df.index[-1] - clean_df.index[0]).days
        total_years = total_days / 365
        total_return = clean_df['equity_curve'].iloc[-1] - 1
        annual_return = (1 + total_return) ** (1 / total_years) - 1
        
        # 计算夏普比率（假设无风险利率为0）
        daily_returns = clean_df['equity_curve'].pct_change().dropna()
        sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'trade_count': len(trades),
            'volatility': daily_returns.std() * np.sqrt(252)
        }
    
    def get_latest_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        获取最新的交易信号
        
        Args:
            data: 包含OHLC数据的DataFrame
            
        Returns:
            最新信号信息字典
        """
        df, stats = self.run_strategy(data)
        
        # 获取最新行
        latest = df.iloc[-1]
        
        # 确定信号类型
        if latest['position'] > 0:
            if latest['position'] >= 1.4:
                signal_type = "极强买入信号"
            elif latest['position'] >= 1.2:
                signal_type = "强买入信号"
            elif latest['position'] >= 1.0:
                signal_type = "买入信号"
            else:
                signal_type = "弱买入信号"
        else:
            signal_type = "卖出信号"
        
        # 返回信号信息
        return {
            'date': latest.name,
            'close': latest['close'],
            'signal_value': latest['composite_signal'],
            'position': latest['position'],
            'signal_type': signal_type,
            'stop_loss': latest['stop_loss'],
            'ma_long': latest[f'MA{self.config["ma_long"]}'],
            'ma_short': latest[f'MA{self.config["ma_short"]}'],
            'rsi': latest['RSI'],
            'macd': latest['MACD'],
            'adx': latest['ADX'],
            'stats': stats
        }
