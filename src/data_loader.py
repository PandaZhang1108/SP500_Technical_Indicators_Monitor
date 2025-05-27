#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据获取模块
负责从Finnhub API和其他来源获取股票数据，并进行必要的处理
"""

import os
import pandas as pd
import numpy as np
import finnhub
import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataLoader:
    """数据加载器类，负责获取和处理股票数据"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据加载器
        
        Args:
            config: 配置字典，包含API密钥等信息
        """
        self.config = config
        self.finnhub_client = None
        
        # 如果提供了Finnhub API密钥，则初始化客户端
        if 'finnhub_api_key' in config and config['finnhub_api_key']:
            self.finnhub_client = finnhub.Client(api_key=config['finnhub_api_key'])
        
        # 数据存储路径
        self.data_dir = config.get('data_dir', 'data')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_stock_data_finnhub(self, symbol: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        从Finnhub获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        if not self.finnhub_client:
            logger.error("Finnhub客户端未初始化，请提供有效的API密钥")
            return pd.DataFrame()
        
        # 默认结束日期为今天
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 转换日期为UNIX时间戳
        start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
        
        try:
            # 从Finnhub获取股票数据
            logger.info(f"从Finnhub获取{symbol}的数据，从{start_date}到{end_date}")
            res = self.finnhub_client.stock_candles(
                symbol=symbol,
                resolution='D',  # 日线数据
                _from=start_timestamp,
                to=end_timestamp
            )
            
            # 检查返回状态
            if res['s'] == 'no_data':
                logger.warning(f"Finnhub未返回{symbol}的数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame({
                'open': res['o'],
                'high': res['h'],
                'low': res['l'],
                'close': res['c'],
                'volume': res['v']
            }, index=pd.to_datetime([datetime.fromtimestamp(t) for t in res['t']]))
            
            return df
            
        except Exception as e:
            logger.error(f"从Finnhub获取数据时出错: {e}")
            return pd.DataFrame()
    
    def get_stock_data_yfinance(self, symbol: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        从Yahoo Finance获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        # 默认结束日期为今天
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 从Yahoo Finance获取股票数据
            logger.info(f"从Yahoo Finance获取{symbol}的数据，从{start_date}到{end_date}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            # 重命名列以匹配我们的格式
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"从Yahoo Finance获取数据时出错: {e}")
            return pd.DataFrame()
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str = None, source: str = 'auto') -> pd.DataFrame:
        """
        获取股票数据，自动选择数据源或使用指定的数据源
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天
            source: 数据源 ('finnhub', 'yfinance', 或 'auto')
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        if source == 'finnhub' or (source == 'auto' and self.finnhub_client):
            df = self.get_stock_data_finnhub(symbol, start_date, end_date)
            if not df.empty:
                return df
            
            # 如果Finnhub返回空数据且source为auto，则尝试使用yfinance
            if source == 'auto':
                logger.info("Finnhub返回空数据，尝试使用Yahoo Finance")
                return self.get_stock_data_yfinance(symbol, start_date, end_date)
        
        # 如果指定使用yfinance或其他情况
        return self.get_stock_data_yfinance(symbol, start_date, end_date)
    
    def load_or_download_data(self, symbol: str, lookback_years: int = 10, force_download: bool = False) -> pd.DataFrame:
        """
        加载本地数据文件，如果不存在或强制下载则从API获取
        
        Args:
            symbol: 股票代码
            lookback_years: 回溯年数
            force_download: 是否强制重新下载数据
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        # 构建本地数据文件路径
        file_path = os.path.join(self.data_dir, f"{symbol.replace('^', '')}_data.csv")
        
        # 如果本地文件存在且不强制下载，则加载本地文件
        if os.path.exists(file_path) and not force_download:
            # 检查文件是否为空
            if os.path.getsize(file_path) == 0:
                logger.warning(f"本地文件 {file_path} 为空，将重新下载数据")
                force_download = True
            else:
                try:
                    logger.info(f"从本地文件加载{symbol}数据")
                    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                    
                    # 检查是否需要更新数据
                    if df.index[-1].date() < (datetime.now() - timedelta(days=1)).date():
                        # 获取最新数据
                        logger.info(f"更新{symbol}数据")
                        start_date = (df.index[-1] + timedelta(days=1)).strftime('%Y-%m-%d')
                        end_date = datetime.now().strftime('%Y-%m-%d')
                        
                        new_data = self.get_stock_data(symbol, start_date, end_date)
                        if not new_data.empty:
                            # 合并新旧数据
                            df = pd.concat([df, new_data])
                            # 保存更新后的数据
                            df.to_csv(file_path)
                except Exception as e:
                    logger.error(f"加载本地数据文件时出错: {e}")
                    logger.info("将重新下载数据")
                    force_download = True
        
        # 如果需要下载数据（文件不存在、为空、无法解析或强制下载）
        if not os.path.exists(file_path) or force_download:
            # 计算开始日期（默认10年前）
            start_date = (datetime.now() - timedelta(days=365 * lookback_years)).strftime('%Y-%m-%d')
            
            # 下载数据
            logger.info(f"下载{symbol}的历史数据，从{start_date}开始")
            df = self.get_stock_data(symbol, start_date)
            
            # 保存数据到本地
            if not df.empty:
                df.to_csv(file_path)
                logger.info(f"数据已保存到 {file_path}")
            else:
                logger.error(f"无法获取 {symbol} 的数据")
        
        return df
    
    def resample_to_weekly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将日线数据重采样为周线数据
        
        Args:
            df: 日线数据DataFrame
            
        Returns:
            周线数据DataFrame
        """
        # 创建一个副本以避免修改原始数据
        df_copy = df.copy()
        
        # 确保索引是日期时间类型，并处理时区问题
        try:
            if not isinstance(df_copy.index, pd.DatetimeIndex):
                # 尝试直接转换为无时区的日期时间
                df_copy.index = pd.to_datetime(df_copy.index).tz_localize(None)
            elif df_copy.index.tz is not None:
                # 如果索引已经是DatetimeIndex但有时区，移除时区
                df_copy.index = df_copy.index.tz_localize(None)
        except Exception as e:
            logger.warning(f"处理日期时间索引时出错: {e}")
            # 如果转换失败，则创建新的无时区索引
            try:
                # 尝试手动转换每个日期
                new_index = []
                for idx in df_copy.index:
                    if hasattr(idx, 'to_pydatetime'):  # 如果是时间戳对象
                        dt = idx.to_pydatetime().replace(tzinfo=None)
                    elif isinstance(idx, str):  # 如果是字符串
                        dt = pd.to_datetime(idx).to_pydatetime()
                    else:  # 其他情况
                        dt = pd.to_datetime(idx).to_pydatetime()
                    new_index.append(dt)
                
                df_copy.index = pd.DatetimeIndex(new_index)
            except Exception as inner_e:
                logger.error(f"无法创建有效的DatetimeIndex: {inner_e}")
                # 最后的尝试：如果无法处理日期索引，创建一个简单的范围索引
                # 并使用最近的日期作为起点
                today = pd.Timestamp.now()
                start_date = today - pd.Timedelta(days=len(df_copy) - 1)
                df_copy.index = pd.date_range(start=start_date, periods=len(df_copy), freq='D')
                logger.warning("使用生成的日期范围作为索引")
        
        # 确保索引是DatetimeIndex类型，否则无法重采样
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            logger.error("无法创建DatetimeIndex，无法执行重采样")
            # 返回原始数据，无法重采样
            return df_copy
        
        # 重采样为周线，使用以下规则：
        # - 开盘价：取一周内第一个交易日的开盘价
        # - 最高价：取一周内的最高价
        # - 最低价：取一周内的最低价
        # - 收盘价：取一周内最后一个交易日的收盘价
        # - 成交量：取一周内成交量之和
        try:
            weekly = df_copy.resample('W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })
            return weekly
        except Exception as e:
            logger.error(f"重采样为周线数据时出错: {e}")
            # 如果重采样失败，返回原始数据
            return df_copy
    
    def save_position_history(self, position_history: pd.DataFrame) -> None:
        """
        保存仓位历史记录
        
        Args:
            position_history: 包含仓位历史的DataFrame
        """
        file_path = os.path.join(self.data_dir, 'position_history.csv')
        position_history.to_csv(file_path)
        logger.info(f"仓位历史已保存到 {file_path}")
    
    def load_position_history(self) -> pd.DataFrame:
        """
        加载仓位历史记录
        
        Returns:
            包含仓位历史的DataFrame，如果文件不存在则返回空DataFrame
        """
        file_path = os.path.join(self.data_dir, 'position_history.csv')
        if os.path.exists(file_path):
            # 检查文件是否为空
            if os.path.getsize(file_path) == 0:
                logger.warning(f"仓位历史文件 {file_path} 为空，返回空DataFrame")
                return pd.DataFrame(columns=['position', 'signal_value', 'close', 'signal_type'])
            
            try:
                return pd.read_csv(file_path, index_col=0, parse_dates=True)
            except Exception as e:
                logger.error(f"加载仓位历史文件时出错: {e}")
                return pd.DataFrame(columns=['position', 'signal_value', 'close', 'signal_type'])
        else:
            return pd.DataFrame(columns=['position', 'signal_value', 'close', 'signal_type'])
