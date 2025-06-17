#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试AkShare数据加载器
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 导入AkShareLoader类
from akshare_loader import AkShareLoader

def test_sp500_history():
    """
    测试获取标普500指数历史数据
    """
    print("测试获取标普500指数历史数据...")
    
    # 创建AkShareLoader实例
    loader = AkShareLoader()
    
    # 获取最近90天的数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    # 获取数据
    try:
        df = loader.get_sp500_history(start_date, end_date)
        
        # 打印数据信息
        print(f"获取到 {len(df)} 条记录")
        print("\n数据前5行:")
        print(df.head())
        
        # 绘制收盘价走势图
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['close'])
        plt.title('标普500指数收盘价走势')
        plt.xlabel('日期')
        plt.ylabel('收盘价')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('sp500_history.png')
        print("收盘价走势图已保存为 sp500_history.png")
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_sp500_constituents():
    """
    测试获取标普500指数成分股列表
    """
    print("\n测试获取标普500指数成分股列表...")
    
    # 创建AkShareLoader实例
    loader = AkShareLoader()
    
    # 获取数据
    try:
        df = loader.get_sp500_constituents()
        
        # 打印数据信息
        print(f"获取到 {len(df)} 支成分股")
        print("\n数据前5行:")
        print(df.head())
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_sp500_technical_indicators():
    """
    测试计算标普500指数的技术指标
    """
    print("\n测试计算标普500指数的技术指标...")
    
    # 创建AkShareLoader实例
    loader = AkShareLoader()
    
    # 获取最近180天的数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    # 获取数据
    try:
        df = loader.get_sp500_technical_indicators(start_date, end_date)
        
        # 打印数据信息
        print(f"获取到 {len(df)} 条记录")
        print("\n数据前5行:")
        print(df.head())
        
        # 绘制技术指标图
        plt.figure(figsize=(12, 10))
        
        # 第一个子图：价格和移动平均线
        plt.subplot(3, 1, 1)
        plt.plot(df['date'], df['close'], label='收盘价')
        plt.plot(df['date'], df['MA20'], label='20日MA')
        plt.plot(df['date'], df['MA50'], label='50日MA')
        plt.plot(df['date'], df['MA200'], label='200日MA')
        plt.title('标普500指数价格和移动平均线')
        plt.legend()
        plt.grid(True)
        
        # 第二个子图：RSI
        plt.subplot(3, 1, 2)
        plt.plot(df['date'], df['RSI14'])
        plt.axhline(y=70, color='r', linestyle='-')
        plt.axhline(y=30, color='g', linestyle='-')
        plt.title('相对强弱指标 (RSI)')
        plt.grid(True)
        
        # 第三个子图：MACD
        plt.subplot(3, 1, 3)
        plt.bar(df['date'], df['MACD_Hist'], color=['g' if x > 0 else 'r' for x in df['MACD_Hist']])
        plt.plot(df['date'], df['MACD'], label='MACD')
        plt.plot(df['date'], df['MACD_Signal'], label='Signal')
        plt.title('MACD')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig('sp500_indicators.png')
        print("技术指标图已保存为 sp500_indicators.png")
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    # 运行测试
    history_test = test_sp500_history()
    constituents_test = test_sp500_constituents()
    indicators_test = test_sp500_technical_indicators()
    
    # 打印测试结果摘要
    print("\n测试结果摘要:")
    print(f"标普500指数历史数据测试: {'成功' if history_test else '失败'}")
    print(f"标普500指数成分股列表测试: {'成功' if constituents_test else '失败'}")
    print(f"标普500指数技术指标测试: {'成功' if indicators_test else '失败'}") 