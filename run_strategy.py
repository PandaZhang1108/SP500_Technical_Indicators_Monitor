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
from datetime import datetime, timedelta
import argparse
from typing import Dict, Any

# 导入自定义模块
from src.enhanced_siegel import EnhancedSiegelStrategy
from src.data_loader import DataLoader
from src.signal_analyzer import SignalAnalyzer

# 检查是否在 GitHub Actions 环境中运行
def is_github_actions() -> bool:
    """
    检查是否在GitHub Actions环境中运行
    
    Returns:
        是否在GitHub Actions中运行
    """
    return os.environ.get('GITHUB_ACTIONS') == 'true'

# 只有在非 GitHub Actions 环境中才导入 EmailNotifier
if not is_github_actions():
    try:
        from src.notification import EmailNotifier
    except ImportError:
        EmailNotifier = None
        print("警告: 未能导入 EmailNotifier 类，邮件通知功能不可用")
else:
    EmailNotifier = None

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
        'smtp_port': 587,
        # 添加策略参数的默认值
        'ma_long': 45,
        'ma_short': 20,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'adx_period': 14,
        'atr_period': 14,
        'atr_multiplier': 2.5,
        'signal_threshold': 0.5,
        'strong_signal': 0.75,
        'very_strong_signal': 0.9,
        'weak_signal': 0.65,
        'trend_weight': 0.4,
        'slope_weight': 0.25,
        'momentum_weight': 0.2,
        'environment_weight': 0.15
    }
    
    # 如果配置文件存在，则读取
    if os.path.exists(config_file):
        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)
            
            # 读取策略配置
            if 'Strategy' in parser:
                # 明确定义需要转换为int的参数
                int_params = ['ma_long', 'ma_short', 'rsi_period', 'macd_fast', 'macd_slow', 'macd_signal', 'adx_period', 'atr_period']
                # 明确定义需要转换为float的参数
                float_params = ['atr_multiplier', 'signal_threshold', 'strong_signal', 'very_strong_signal', 'weak_signal', 'trend_weight', 'slope_weight', 'momentum_weight', 'environment_weight']
                
                for key in parser['Strategy']:
                    try:
                        if key in int_params:
                            # 确保这些参数是整数
                            config[key] = int(float(parser['Strategy'][key]))
                            # 验证参数值是否有效
                            if config[key] <= 0 and key not in ['atr_multiplier']:  # atr_multiplier可以是小数
                                logger.warning(f"参数 {key} 的值 {config[key]} 无效，使用默认值")
                                config[key] = int(config.get(key, 1))  # 使用默认值，最小为1
                        elif key in float_params:
                            # 转换为浮点数
                            config[key] = float(parser['Strategy'][key])
                        else:
                            # 其他参数保持原样
                            config[key] = parser['Strategy'][key]
                    except (ValueError, TypeError) as e:
                        logger.warning(f"转换参数 {key} 时出错: {e}，使用默认值")
            
            # 读取数据配置
            if 'Data' in parser:
                for key in parser['Data']:
                    if key == 'lookback_years':
                        try:
                            config[key] = int(parser['Data'][key])
                            if config[key] <= 0:
                                config[key] = 10  # 使用默认值
                                logger.warning(f"lookback_years 必须大于0，使用默认值 10")
                        except (ValueError, TypeError):
                            config[key] = 10
                            logger.warning("无法将 lookback_years 转换为整数，使用默认值 10")
                    else:
                        config[key] = parser['Data'][key]
            
            # 读取通知配置
            if 'Notification' in parser:
                for key in parser['Notification']:
                    if key == 'smtp_port':
                        try:
                            config[key] = int(parser['Notification'][key])
                        except (ValueError, TypeError):
                            config[key] = 587
                            logger.warning("无法将 smtp_port 转换为整数，使用默认值 587")
                    else:
                        config[key] = parser['Notification'][key]
            
            logger.info("已从 {} 加载配置".format(config_file))
        except Exception as e:
            logger.error("读取配置文件时出错: {}".format(e))
    else:
        logger.warning("配置文件 {} 不存在，使用默认配置".format(config_file))
    
    # 环境变量优先级高于配置文件
    for env_var in ['FINNHUB_API_KEY', 'EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECIPIENT']:
        if os.environ.get(env_var):
            config[env_var.lower()] = os.environ.get(env_var)
    
    # 打印关键配置值用于调试(不包含敏感信息)
    logger.debug(f"配置加载完成，关键参数: ma_long={config['ma_long']}, ma_short={config['ma_short']}, lookback_years={config['lookback_years']}")
    
    return config


def create_config_template(config_file: str = 'config.ini') -> None:
    """
    创建配置文件模板
    
    Args:
        config_file: 配置文件路径
    """
    if os.path.exists(config_file):
        logger.warning("配置文件 {} 已存在，跳过创建模板".format(config_file))
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
    
    logger.info("已创建配置文件模板 {}".format(config_file))


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
        logger.info("获取 {} 的股票数据".format(config['symbol']))
        daily_data = data_loader.load_or_download_data(
            symbol=config['symbol'],
            lookback_years=int(config.get('lookback_years', 10)),
            force_download=args.force_download
        )
        
        # 检查是否成功获取数据
        if daily_data.empty:
            error_message = "无法获取 {} 的真实市场数据，请检查数据源和网络连接。".format(config['symbol'])
            logger.error(error_message)
            
            # 发送错误通知邮件
            if not args.no_email and EmailNotifier is not None:
                email_config_valid = all([
                    config.get('email_sender'), 
                    config.get('email_password'), 
                    config.get('email_recipient')
                ])
                
                if email_config_valid:
                    logger.info("发送错误通知邮件")
                    notifier = EmailNotifier(config)
                    subject = "【数据获取错误】增强西格尔策略 - 无法获取市场数据"
                    body = f"""
                    # 增强西格尔策略数据获取错误
                    
                    无法获取 {config['symbol']} 的真实市场数据，请检查以下可能的原因：
                    
                    1. 网络连接问题
                    2. API密钥是否有效（如果使用Finnhub）
                    3. 数据提供商服务是否可用
                    4. 市场是否休市或有其他特殊情况
                    
                    请手动检查数据来源并解决问题。
                    
                    错误发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    notifier.send_email(subject, body)
            
            # 在GitHub Actions环境中也创建错误报告，方便查看
            if is_github_actions():
                error_report = f"""
                数据获取错误
                
                无法获取 {config['symbol']} 的真实市场数据
                
                请检查数据源和网络连接。
                """
                logger.info("信号报告:\n" + error_report)
            
            sys.exit(1)  # 直接退出程序，不继续执行
        
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
            position_value = latest_signal['position']
            logger.info("已更新仓位历史，当前仓位: {:.2f}".format(position_value))
        
        # 9. 初始化信号分析器
        signal_analyzer = SignalAnalyzer(config)
        
        # 10. 生成仓位摘要
        position_summary = signal_analyzer.generate_position_summary(position_history)
        
        # 11. 生成信号报告
        report_text = signal_analyzer.generate_signal_report(latest_signal, position_summary)
        logger.info("信号报告:\n" + report_text)
        
        # 12. 生成图表
        current_date = datetime.now().strftime('%Y%m%d')
        chart_path = os.path.join(config['charts_dir'], "strategy_chart_{}.png".format(current_date))
        
        # 只显示最近3年的数据，如果数据不足3年，则显示所有可用数据
        lookback_periods = min(156, len(results_df))
        chart_data = results_df.tail(lookback_periods)
        
        try:
            signal_analyzer.plot_strategy_performance(chart_data, chart_path)
        except Exception as e:
            logger.error("生成策略图表时出错: {}".format(e))
            # 创建一个简单的替代图表
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 6))
            plt.plot(chart_data.index, chart_data['close'], label='收盘价')
            plt.title('策略表现 (简化版)')
            plt.xlabel('日期')
            plt.ylabel('价格')
            plt.legend()
            plt.savefig(chart_path)
            plt.close()
        
        # 生成交互式图表
        interactive_chart_path = os.path.join(config['charts_dir'], "interactive_chart_{}.html".format(current_date))
        try:
            signal_analyzer.plot_interactive_chart(chart_data, interactive_chart_path)
        except Exception as e:
            logger.error("生成交互式图表时出错: {}".format(e))
        
        # 13. 发送邮件通知（如果配置了邮件且未禁用，且不是在GitHub Actions中运行）
        if not args.no_email and not is_github_actions() and EmailNotifier is not None:
            email_config_valid = all([
                config.get('email_sender'), 
                config.get('email_password'), 
                config.get('email_recipient')
            ])
            
            if email_config_valid:
                logger.info("发送邮件通知")
                notifier = EmailNotifier(config)
                notifier.send_signal_email(latest_signal, report_text, chart_path)
            else:
                logger.warning("邮件配置不完整，跳过发送通知")
        elif is_github_actions():
            logger.info("在GitHub Actions环境中运行，邮件将由GitHub Actions发送")
        
        logger.info("策略执行完成")
        
    except Exception as e:
        logger.exception("运行策略时出错: {}".format(e))
        
        # 在GitHub Actions环境中，即使出错也要生成最低限度的报告
        if is_github_actions():
            try:
                # 创建一个基本的报告
                error_report = f"""
                运行增强西格尔策略时出错
                
                错误信息:
                {str(e)}
                
                请检查日志和代码以解决此问题。
                """
                
                # 记录到日志文件中，以便GitHub Actions可以提取
                logger.info("信号报告:\n" + error_report)
                
                # 在charts目录中创建一个空白图片，以便GitHub Actions可以找到
                import matplotlib.pyplot as plt
                current_date = datetime.now().strftime('%Y%m%d')
                chart_path = os.path.join(config['charts_dir'], f"strategy_chart_{current_date}.png")
                plt.figure(figsize=(10, 6))
                plt.text(0.5, 0.5, "策略执行出错，请查看日志", ha='center', va='center', fontsize=20)
                plt.axis('off')
                plt.savefig(chart_path)
                plt.close()
            except Exception as inner_e:
                logger.error(f"尝试创建错误报告时又出错: {inner_e}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
