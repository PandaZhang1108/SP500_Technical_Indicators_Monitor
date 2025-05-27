#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强西格尔策略主运行脚本
负责协调数据获取、策略执行、信号分析和通知发送
"""

import os
import sys
import logging
import configparser
import pandas as pd
from datetime import datetime
import argparse
from typing import Dict, Any

# 导入自定义模块
from src.enhanced_siegel import EnhancedSiegelStrategy
from src.data_loader import DataLoader
from src.signal_analyzer import SignalAnalyzer
from src.notification import EmailNotifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_siegel.log')
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_file: str = 'config.ini') -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
    """
    # 默认配置
    config = {
        'symbol': 'SPY',
        'lookback_years': 10,
        'finnhub_api_key': os.environ.get('FINNHUB_API_KEY', 'd0qh65pr01qt60oocosgd0qh65pr01qt60oocot0'),
        'data_dir': 'data',
        'charts_dir': 'charts',
        'email_sender': os.environ.get('EMAIL_SENDER', ''),
        'email_password': os.environ.get('EMAIL_PASSWORD', ''),
        'email_recipient': os.environ.get('EMAIL_RECIPIENT', ''),
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587
    }
    
    # 如果配置文件存在，则读取
    if os.path.exists(config_file):
        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)
            
            # 读取策略配置
            if 'Strategy' in parser:
                for key in parser['Strategy']:
                    # 尝试将数值转换为浮点数
                    try:
                        config[key] = float(parser['Strategy'][key])
                    except ValueError:
                        config[key] = parser['Strategy'][key]
            
            # 读取数据配置
            if 'Data' in parser:
                for key in parser['Data']:
                    if key == 'lookback_years':
                        config[key] = int(parser['Data'][key])
                    else:
                        config[key] = parser['Data'][key]
            
            # 读取通知配置
            if 'Notification' in parser:
                for key in parser['Notification']:
                    if key == 'smtp_port':
                        config[key] = int(parser['Notification'][key])
                    else:
                        config[key] = parser['Notification'][key]
            
            logger.info(f"已从 {config_file} 加载配置")
        except Exception as e:
            logger.error(f"读取配置文件时出错: {e}")
    else:
        logger.warning(f"配置文件 {config_file} 不存在，使用默认配置")
    
    # 环境变量优先级高于配置文件
    for env_var in ['FINNHUB_API_KEY', 'EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECIPIENT']:
        if os.environ.get(env_var):
            config[env_var.lower()] = os.environ.get(env_var)
    
    return config


def create_config_template(config_file: str = 'config.ini') -> None:
    """
    创建配置文件模板
    
    Args:
        config_file: 配置文件路径
    """
    if os.path.exists(config_file):
        logger.warning(f"配置文件 {config_file} 已存在，跳过创建模板")
        return
    
    config = configparser.ConfigParser()
    
    # 策略配置
    config['Strategy'] = {
        'ma_long': '45',
        'ma_short': '20',
        'rsi_period': '14',
        'macd_fast': '12',
        'macd_slow': '26',
        'macd_signal': '9',
        'adx_period': '14',
        'atr_period': '14',
        'atr_multiplier': '2.5',
        'signal_threshold': '0.5',
        'strong_signal': '0.75',
        'very_strong_signal': '0.9',
        'weak_signal': '0.65',
        'trend_weight': '0.4',
        'slope_weight': '0.25',
        'momentum_weight': '0.2',
        'environment_weight': '0.15'
    }
    
    # 数据配置
    config['Data'] = {
        'symbol': 'SPY',
        'lookback_years': '10',
        'finnhub_api_key': 'd0qh65pr01qt60oocosgd0qh65pr01qt60oocot0',
        'data_dir': 'data',
        'charts_dir': 'charts'
    }
    
    # 通知配置
    config['Notification'] = {
        'email_sender': 'your_email@gmail.com',
        'email_password': 'your_app_password',
        'email_recipient': 'recipient@example.com',
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': '587'
    }
    
    # 写入配置文件
    with open(config_file, 'w') as f:
        config.write(f)
    
    logger.info(f"已创建配置文件模板 {config_file}")


def is_github_actions() -> bool:
    """
    检查是否在GitHub Actions环境中运行
    
    Returns:
        是否在GitHub Actions中运行
    """
    return os.environ.get('GITHUB_ACTIONS') == 'true'


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='增强西格尔策略运行器')
    parser.add_argument('--config', type=str, default='config.ini', help='配置文件路径')
    parser.add_argument('--create-config', action='store_true', help='创建配置文件模板')
    parser.add_argument('--force-download', action='store_true', help='强制重新下载数据')
    parser.add_argument('--no-email', action='store_true', help='不发送邮件通知')
    args = parser.parse_args()
    
    # 创建配置文件模板
    if args.create_config:
        create_config_template(args.config)
        return
    
    # 加载配置
    config = load_config(args.config)
    
    try:
        # 确保数据和图表目录存在
        os.makedirs(config['data_dir'], exist_ok=True)
        os.makedirs(config['charts_dir'], exist_ok=True)
        
        # 1. 初始化数据加载器
        data_loader = DataLoader(config)
        
        # 2. 获取股票数据
        logger.info(f"获取 {config['symbol']} 的股票数据")
        daily_data = data_loader.load_or_download_data(
            symbol=config['symbol'],
            lookback_years=int(config.get('lookback_years', 10)),
            force_download=args.force_download
        )
        
        if daily_data.empty:
            logger.error(f"无法获取 {config['symbol']} 的数据，退出")
            return
        
        # 3. 将日线数据转换为周线数据
        weekly_data = data_loader.resample_to_weekly(daily_data)
        
        # 4. 初始化策略
        strategy = EnhancedSiegelStrategy(config)
        
        # 5. 运行策略
        logger.info("运行增强西格尔策略")
        results_df, stats = strategy.run_strategy(weekly_data)
        
        # 6. 获取最新信号
        latest_signal = strategy.get_latest_signal(weekly_data)
        
        # 7. 加载历史仓位数据
        position_history = data_loader.load_position_history()
        
        # 8. 更新仓位历史
        new_position = pd.DataFrame({
            'date': [latest_signal['date']],
            'position': [latest_signal['position']],
            'signal_value': [latest_signal['signal_value']],
            'close': [latest_signal['close']],
            'signal_type': [latest_signal['signal_type']]
        })
        new_position.set_index('date', inplace=True)
        
        # 如果是新的日期或仓位变化，则添加到历史记录
        if position_history.empty or \
           latest_signal['date'] not in position_history.index or \
           latest_signal['position'] != position_history.loc[latest_signal['date'], 'position']:
            position_history = pd.concat([position_history, new_position])
            data_loader.save_position_history(position_history)
            logger.info(f"已更新仓位历史，当前仓位: {latest_signal['position']:.2f}")
        
        # 9. 初始化信号分析器
        signal_analyzer = SignalAnalyzer(config)
        
        # 10. 生成仓位摘要
        position_summary = signal_analyzer.generate_position_summary(position_history)
        
        # 11. 生成信号报告
        report_text = signal_analyzer.generate_signal_report(latest_signal, position_summary)
        logger.info("信号报告:\n" + report_text)
        
        # 12. 生成图表
        chart_path = os.path.join(config['charts_dir'], f"strategy_chart_{datetime.now().strftime('%Y%m%d')}.png")
        signal_analyzer.plot_strategy_performance(results_df.tail(156), chart_path)  # 显示最近3年的数据
        
        # 生成交互式图表
        interactive_chart_path = os.path.join(config['charts_dir'], f"interactive_chart_{datetime.now().strftime('%Y%m%d')}.html")
        signal_analyzer.plot_interactive_chart(results_df.tail(156), interactive_chart_path)
        
        # 13. 发送邮件通知（如果配置了邮件且未禁用，且不是在GitHub Actions中运行）
        if not args.no_email and all([config.get('email_sender'), config.get('email_password'), config.get('email_recipient')]) and not is_github_actions():
            logger.info("发送邮件通知")
            notifier = EmailNotifier(config)
            notifier.send_signal_email(latest_signal, report_text, chart_path)
        elif is_github_actions():
            logger.info("在GitHub Actions环境中运行，邮件将由GitHub Actions发送")
        
        logger.info("策略执行完成")
        
    except Exception as e:
        logger.exception(f"运行策略时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
