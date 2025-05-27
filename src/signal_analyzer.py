#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
信号分析模块
负责分析策略信号，生成交易建议和图表
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SignalAnalyzer:
    """信号分析器类，负责分析策略信号并生成报告"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化信号分析器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.charts_dir = config.get('charts_dir', 'charts')
        
        # 确保图表目录存在
        os.makedirs(self.charts_dir, exist_ok=True)
    
    def analyze_signal_change(self, current_position: float, previous_position: float) -> Dict[str, Any]:
        """
        分析信号变化并生成交易建议
        
        Args:
            current_position: 当前仓位
            previous_position: 前一个仓位
            
        Returns:
            包含交易建议的字典
        """
        if current_position > previous_position:
            if previous_position == 0:
                action = "买入"
                description = "新建仓位"
            else:
                action = "加仓"
                description = f"从 {previous_position:.2f} 增加到 {current_position:.2f}"
        elif current_position < previous_position:
            if current_position == 0:
                action = "卖出"
                description = "清空仓位"
            else:
                action = "减仓"
                description = f"从 {previous_position:.2f} 减少到 {current_position:.2f}"
        else:
            action = "持有"
            description = "维持当前仓位"
        
        return {
            "action": action,
            "description": description,
            "position_change": current_position - previous_position
        }
    
    def generate_position_summary(self, position_history: pd.DataFrame) -> Dict[str, Any]:
        """
        生成仓位历史摘要
        
        Args:
            position_history: 包含仓位历史的DataFrame
            
        Returns:
            包含仓位摘要的字典
        """
        if position_history.empty:
            return {
                "current_position": 0,
                "last_change_date": None,
                "days_since_change": None,
                "position_trend": "无历史数据"
            }
        
        # 获取最新仓位
        current_position = position_history['position'].iloc[-1]
        
        # 查找最近的仓位变化
        position_history['position_change'] = position_history['position'].diff()
        changes = position_history[position_history['position_change'] != 0]
        
        if len(changes) > 0:
            last_change_date = changes.index[-1]
            days_since_change = (pd.Timestamp.now() - last_change_date).days
            
            # 分析最近的仓位趋势
            recent_changes = changes.tail(3)
            if len(recent_changes) >= 2:
                increases = (recent_changes['position_change'] > 0).sum()
                decreases = (recent_changes['position_change'] < 0).sum()
                
                if increases > decreases:
                    position_trend = "上升趋势"
                elif decreases > increases:
                    position_trend = "下降趋势"
                else:
                    position_trend = "震荡"
            else:
                position_trend = "数据不足"
        else:
            last_change_date = position_history.index[0]
            days_since_change = (pd.Timestamp.now() - last_change_date).days
            position_trend = "无变化"
        
        return {
            "current_position": current_position,
            "last_change_date": last_change_date,
            "days_since_change": days_since_change,
            "position_trend": position_trend
        }
    
    def plot_strategy_performance(self, results_df: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """
        绘制策略表现图表
        
        Args:
            results_df: 包含策略结果的DataFrame
            save_path: 图表保存路径，如果不提供则显示图表
        """
        # 创建包含4个子图的图表
        fig, axs = plt.subplots(4, 1, figsize=(14, 16), gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        
        # 设置共享x轴
        for i in range(1, 4):
            axs[0].get_shared_x_axes().join(axs[0], axs[i])
        
        # 1. 价格和移动平均线
        axs[0].plot(results_df.index, results_df['close'], label='价格', color='black')
        axs[0].plot(results_df.index, results_df['MA45'], label='45周MA', color='blue', alpha=0.7)
        axs[0].plot(results_df.index, results_df['MA20'], label='20周MA', color='red', alpha=0.7)
        
        # 添加买卖点标记
        buy_signals = results_df[(results_df['position'] > 0) & (results_df['position'].shift(1) == 0)]
        sell_signals = results_df[(results_df['position'] == 0) & (results_df['position'].shift(1) > 0)]
        
        axs[0].scatter(buy_signals.index, buy_signals['close'], marker='^', color='green', s=100, label='买入信号')
        axs[0].scatter(sell_signals.index, sell_signals['close'], marker='v', color='red', s=100, label='卖出信号')
        
        axs[0].set_title('增强西格尔策略表现', fontsize=16)
        axs[0].set_ylabel('价格', fontsize=12)
        axs[0].legend(loc='upper left')
        axs[0].grid(True)
        
        # 2. 仓位图
        axs[1].fill_between(results_df.index, results_df['position'], color='blue', alpha=0.3)
        axs[1].plot(results_df.index, results_df['position'], color='blue')
        axs[1].set_ylabel('仓位', fontsize=12)
        axs[1].set_ylim(0, 1.5)
        axs[1].grid(True)
        
        # 3. 复合信号
        axs[2].plot(results_df.index, results_df['composite_signal'], color='purple')
        axs[2].axhline(y=0.5, color='r', linestyle='--', alpha=0.3)  # 信号阈值
        axs[2].axhline(y=0.75, color='g', linestyle='--', alpha=0.3)  # 强信号阈值
        axs[2].axhline(y=0.9, color='g', linestyle='--', alpha=0.3)  # 极强信号阈值
        axs[2].set_ylabel('综合信号', fontsize=12)
        axs[2].set_ylim(0, 1)
        axs[2].grid(True)
        
        # 4. RSI
        axs[3].plot(results_df.index, results_df['RSI'], color='orange')
        axs[3].axhline(y=70, color='r', linestyle='--', alpha=0.3)
        axs[3].axhline(y=30, color='g', linestyle='--', alpha=0.3)
        axs[3].set_ylabel('RSI', fontsize=12)
        axs[3].set_ylim(0, 100)
        axs[3].grid(True)
        
        # 设置x轴格式
        for ax in axs:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.YearLocator())
        
        plt.tight_layout()
        
        # 保存或显示图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"策略表现图表已保存到 {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_interactive_chart(self, results_df: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """
        使用Plotly创建交互式图表
        
        Args:
            results_df: 包含策略结果的DataFrame
            save_path: HTML图表保存路径
        """
        # 创建子图
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                           vertical_spacing=0.05,
                           subplot_titles=('价格和移动平均线', '仓位', '综合信号', 'RSI'),
                           row_heights=[0.5, 0.15, 0.15, 0.2])
        
        # 1. 价格和移动平均线
        fig.add_trace(go.Scatter(x=results_df.index, y=results_df['close'],
                                mode='lines', name='价格', line=dict(color='black')),
                     row=1, col=1)
        
        fig.add_trace(go.Scatter(x=results_df.index, y=results_df['MA45'],
                                mode='lines', name='45周MA', line=dict(color='blue', width=1)),
                     row=1, col=1)
        
        fig.add_trace(go.Scatter(x=results_df.index, y=results_df['MA20'],
                                mode='lines', name='20周MA', line=dict(color='red', width=1)),
                     row=1, col=1)
        
        # 添加买卖点标记
        buy_signals = results_df[(results_df['position'] > 0) & (results_df['position'].shift(1) == 0)]
        sell_signals = results_df[(results_df['position'] == 0) & (results_df['position'].shift(1) > 0)]
        
        fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['close'],
                                mode='markers', name='买入信号',
                                marker=dict(symbol='triangle-up', size=10, color='green')),
                     row=1, col=1)
        
        fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['close'],
                                mode='markers', name='卖出信号',
                                marker=dict(symbol='triangle-down', size=10, color='red')),
                     row=1, col=1)
        
        # 2. 仓位图
        fig.add_trace(go.Scatter(x=results_df.index, y=results_df['position'],
                                mode='lines', name='仓位', fill='tozeroy',
                                line=dict(color='blue'), fillcolor='rgba(0, 0, 255, 0.2)'),
                     row=2, col=1)
        
        # 3. 复合信号
        fig.add_trace(go.Scatter(x=results_df.index, y=results_df['composite_signal'],
                                mode='lines', name='综合信号', line=dict(color='purple')),
                     row=3, col=1)
        
        # 添加信号阈值线
        fig.add_shape(type="line", x0=results_df.index[0], x1=results_df.index[-1], y0=0.5, y1=0.5,
                     line=dict(color="red", width=1, dash="dash"), row=3, col=1)
        
        fig.add_shape(type="line", x0=results_df.index[0], x1=results_df.index[-1], y0=0.75, y1=0.75,
                     line=dict(color="green", width=1, dash="dash"), row=3, col=1)
        
        fig.add_shape(type="line", x0=results_df.index[0], x1=results_df.index[-1], y0=0.9, y1=0.9,
                     line=dict(color="green", width=1, dash="dash"), row=3, col=1)
        
        # 4. RSI
        fig.add_trace(go.Scatter(x=results_df.index, y=results_df['RSI'],
                                mode='lines', name='RSI', line=dict(color='orange')),
                     row=4, col=1)
        
        # 添加RSI阈值线
        fig.add_shape(type="line", x0=results_df.index[0], x1=results_df.index[-1], y0=70, y1=70,
                     line=dict(color="red", width=1, dash="dash"), row=4, col=1)
        
        fig.add_shape(type="line", x0=results_df.index[0], x1=results_df.index[-1], y0=30, y1=30,
                     line=dict(color="green", width=1, dash="dash"), row=4, col=1)
        
        # 更新布局
        fig.update_layout(
            title='增强西格尔策略表现',
            height=900,
            width=1200,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis4=dict(title='日期'),
            yaxis=dict(title='价格'),
            yaxis2=dict(title='仓位', range=[0, 1.5]),
            yaxis3=dict(title='综合信号', range=[0, 1]),
            yaxis4=dict(title='RSI', range=[0, 100])
        )
        
        # 保存或显示图表
        if save_path:
            fig.write_html(save_path)
            logger.info(f"交互式图表已保存到 {save_path}")
        
        return fig
    
    def generate_signal_report(self, signal_info: Dict[str, Any], position_summary: Dict[str, Any]) -> str:
        """
        生成信号报告文本
        
        Args:
            signal_info: 信号信息字典
            position_summary: 仓位摘要字典
            
        Returns:
            格式化的报告文本
        """
        # 获取当前日期
        current_date = pd.Timestamp.now().strftime('%Y-%m-%d')
        
        # 获取信号信息
        signal_date = signal_info['date'].strftime('%Y-%m-%d') if isinstance(signal_info['date'], pd.Timestamp) else signal_info['date']
        signal_type = signal_info['signal_type']
        signal_value = signal_info['signal_value']
        position = signal_info['position']
        close_price = signal_info['close']
        
        # 获取技术指标
        ma_long = signal_info['ma_long']
        ma_short = signal_info['ma_short']
        rsi = signal_info['rsi']
        
        # 获取统计信息
        stats = signal_info['stats']
        sharpe_ratio = stats['sharpe_ratio']
        max_drawdown = stats['max_drawdown'] * 100
        
        # 获取仓位变化信息
        previous_position = position_summary.get('current_position', 0)
        position_change = self.analyze_signal_change(position, previous_position)
        
        # 格式化报告
        report = f"""
增强西格尔策略信号报告
====================
生成日期: {current_date}
数据日期: {signal_date}

信号概要:
--------
信号类型: {signal_type}
信号强度: {signal_value:.2f}
建议仓位: {position:.2f}
当前价格: {close_price:.2f}

技术指标:
--------
45周均线: {ma_long:.2f}
20周均线: {ma_short:.2f}
RSI(14): {rsi:.2f}
价格相对45周均线: {(close_price/ma_long - 1) * 100:.2f}%
价格相对20周均线: {(close_price/ma_short - 1) * 100:.2f}%

仓位变化:
--------
操作建议: {position_change['action']}
变化描述: {position_change['description']}
上次变化日期: {position_summary.get('last_change_date', 'N/A')}
距上次变化天数: {position_summary.get('days_since_change', 'N/A')}
仓位趋势: {position_summary.get('position_trend', 'N/A')}

策略统计:
--------
夏普比率: {sharpe_ratio:.3f}
最大回撤: {max_drawdown:.2f}%
胜率: {stats['win_rate']*100:.1f}%
交易次数: {stats['trade_count']}

注意事项:
--------
* 本报告仅供参考，不构成投资建议
* 实际操作请结合市场环境和个人风险偏好
* 建议配合其他分析工具一起使用
"""
        
        return report
