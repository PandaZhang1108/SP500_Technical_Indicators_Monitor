#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用AkShare获取标普500指数历史数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AkShareLoader:
    """
    使用AkShare API获取标普500指数历史数据
    """
    
    def __init__(self):
        """
        初始化AkShare数据加载器
        """
        self.symbol = "^GSPC"  # 标普500指数的代码
        
    def get_sp500_history(self, start_date=None, end_date=None):
        """
        获取标普500指数的历史数据
        
        参数:
            start_date (str): 开始日期，格式为'YYYY-MM-DD'
            end_date (str): 结束日期，格式为'YYYY-MM-DD'
            
        返回:
            pandas.DataFrame: 包含标普500指数历史数据的DataFrame
        """
        try:
            logger.info(f"正在获取标普500指数历史数据，时间范围: {start_date} 至 {end_date}")
            
            # 使用AkShare的index_us_stock_sina接口获取标普500指数数据
            df = ak.index_us_stock_sina(symbol=".INX")
            
            # 将日期列转换为datetime类型
            df['date'] = pd.to_datetime(df['date'])
            
            # 如果指定了开始日期和结束日期，则进行过滤
            if start_date and end_date:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            # 重命名列名为更通用的名称
            df = df.rename(columns={
                'date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            # 按日期排序
            df = df.sort_values('date')
            
            logger.info(f"成功获取标普500指数历史数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取标普500指数历史数据失败: {e}")
            raise
    
    def get_sp500_constituents(self):
        """
        获取标普500指数成分股列表
        
        返回:
            pandas.DataFrame: 包含标普500指数成分股信息的DataFrame
        """
        try:
            logger.info("正在获取标普500指数成分股列表")
            
            # 使用AkShare的index_stock_info接口获取标普500指数成分股
            df = ak.index_stock_us_sp_500_constituent()
            
            logger.info(f"成功获取标普500指数成分股列表，共 {len(df)} 支股票")
            return df
            
        except Exception as e:
            logger.error(f"获取标普500指数成分股列表失败: {e}")
            raise
    
    def get_sp500_technical_indicators(self, start_date=None, end_date=None):
        """
        计算标普500指数的技术指标
        
        参数:
            start_date (str): 开始日期，格式为'YYYY-MM-DD'
            end_date (str): 结束日期，格式为'YYYY-MM-DD'
            
        返回:
            pandas.DataFrame: 包含标普500指数技术指标的DataFrame
        """
        try:
            # 获取历史数据
            df = self.get_sp500_history(start_date, end_date)
            
            if df.empty:
                logger.warning("没有获取到数据，无法计算技术指标")
                return pd.DataFrame()
            
            # 计算移动平均线 (5日, 10日, 20日, 50日, 200日)
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA10'] = df['close'].rolling(window=10).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            df['MA50'] = df['close'].rolling(window=50).mean()
            df['MA200'] = df['close'].rolling(window=200).mean()
            
            # 计算相对强弱指标 (RSI, 14日)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI14'] = 100 - (100 / (1 + rs))
            
            # 计算MACD (12, 26, 9)
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            df['MACD'] = macd
            df['MACD_Signal'] = signal
            df['MACD_Hist'] = macd - signal
            
            # 计算布林带 (20日, 2标准差)
            df['BB_Middle'] = df['close'].rolling(window=20).mean()
            df['BB_Upper'] = df['BB_Middle'] + 2 * df['close'].rolling(window=20).std()
            df['BB_Lower'] = df['BB_Middle'] - 2 * df['close'].rolling(window=20).std()
            
            logger.info("成功计算标普500指数技术指标")
            return df
            
        except Exception as e:
            logger.error(f"计算标普500指数技术指标失败: {e}")
            raise

if __name__ == "__main__":
    # 测试代码
    loader = AkShareLoader()
    
    # 获取最近90天的数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    # 获取标普500指数历史数据
    df = loader.get_sp500_history(start_date, end_date)
    print(df.head())
    
    # 获取标普500指数成分股列表
    constituents_df = loader.get_sp500_constituents()
    print(constituents_df.head())
    
    # 获取标普500指数技术指标
    indicators_df = loader.get_sp500_technical_indicators(start_date, end_date)
    print(indicators_df.head()) 