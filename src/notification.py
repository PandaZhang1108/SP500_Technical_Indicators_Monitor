#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通知模块
负责发送策略信号和报告的邮件通知
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """邮件通知类，负责发送策略信号和报告"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化邮件通知器
        
        Args:
            config: 配置字典，包含邮件服务器和账户信息
        """
        self.config = config
        self.sender_email = config.get('email_sender')
        self.password = config.get('email_password')
        self.recipient_email = config.get('email_recipient')
        
        # SMTP服务器配置
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        
        # 检查必要的配置
        if not all([self.sender_email, self.password, self.recipient_email]):
            logger.warning("邮件配置不完整，通知功能将不可用")
    
    def send_signal_email(self, signal_info: Dict[str, Any], report_text: str,
                         chart_path: Optional[str] = None) -> bool:
        """
        发送策略信号邮件
        
        Args:
            signal_info: 信号信息字典
            report_text: 报告文本
            chart_path: 图表文件路径（可选）
            
        Returns:
            发送成功返回True，否则返回False
        """
        if not all([self.sender_email, self.password, self.recipient_email]):
            logger.error("邮件配置不完整，无法发送通知")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['Subject'] = self._create_subject(signal_info)
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # 添加HTML正文
            html_body = self._create_html_body(signal_info, report_text)
            msg.attach(MIMEText(html_body, 'html'))
            
            # 如果提供了图表，添加为附件
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, 'rb') as f:
                    if chart_path.endswith('.html'):
                        # HTML图表作为附件
                        attachment = MIMEApplication(f.read(), _subtype='html')
                        attachment.add_header('Content-Disposition', 'attachment', 
                                            filename=os.path.basename(chart_path))
                    else:
                        # 图片作为内嵌图片
                        attachment = MIMEImage(f.read())
                        attachment.add_header('Content-ID', '<strategy_chart>')
                        attachment.add_header('Content-Disposition', 'inline', 
                                            filename=os.path.basename(chart_path))
                    
                    msg.attach(attachment)
            
            # 发送邮件
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.password)
                server.send_message(msg)
            
            logger.info(f"已成功发送信号通知邮件至 {self.recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件时出错: {e}")
            return False
    
    def _create_subject(self, signal_info: Dict[str, Any]) -> str:
        """
        创建邮件主题
        
        Args:
            signal_info: 信号信息字典
            
        Returns:
            邮件主题字符串
        """
        # 获取当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 获取信号类型和仓位
        signal_type = signal_info['signal_type']
        position = signal_info['position']
        
        # 创建主题
        if "买入" in signal_type:
            subject = f"【增强西格尔策略】买入信号 - 仓位 {position:.2f} ({current_date})"
        elif "卖出" in signal_type:
            subject = f"【增强西格尔策略】卖出信号 - 清仓 ({current_date})"
        else:
            subject = f"【增强西格尔策略】持仓更新 - 仓位 {position:.2f} ({current_date})"
        
        return subject
    
    def _create_html_body(self, signal_info: Dict[str, Any], report_text: str) -> str:
        """
        创建HTML格式的邮件正文
        
        Args:
            signal_info: 信号信息字典
            report_text: 报告文本
            
        Returns:
            HTML格式的邮件正文
        """
        # 获取信号信息
        signal_type = signal_info['signal_type']
        signal_value = signal_info['signal_value']
        position = signal_info['position']
        close_price = signal_info['close']
        
        # 设置信号颜色
        if "买入" in signal_type:
            signal_color = "green"
        elif "卖出" in signal_type:
            signal_color = "red"
        else:
            signal_color = "blue"
        
        # 创建样式 CSS
        css = """
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background-color: #f5f5f5;
                padding: 15px;
                border-bottom: 2px solid #ddd;
                margin-bottom: 20px;
            }
            .signal-box {
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
                background-color: #f9f9f9;
                border-left: 5px solid """ + signal_color + """;
            }
            .report {
                white-space: pre-wrap;
                font-family: monospace;
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            .chart {
                margin: 20px 0;
                text-align: center;
            }
            .footer {
                margin-top: 30px;
                font-size: 0.8em;
                color: #777;
                text-align: center;
            }
        """
        
        # 计算价格相对45周均线百分比
        price_vs_ma = (close_price/signal_info['ma_long'] - 1) * 100
        
        # 生成时间
        generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_year = datetime.now().year
        
        # 创建HTML正文内容
        html = f"""
        <html>
        <head>
            <style>
            {css}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>增强西格尔策略信号通知</h1>
                    <p>生成时间: {generated_time}</p>
                </div>
                
                <div class="signal-box">
                    <h2 style="color: {signal_color};">{signal_type}</h2>
                    <table>
                        <tr>
                            <th>信号强度</th>
                            <td>{signal_value:.2f}</td>
                            <th>建议仓位</th>
                            <td>{position:.2f}</td>
                        </tr>
                        <tr>
                            <th>当前价格</th>
                            <td>{close_price:.2f}</td>
                            <th>价格/45周均线</th>
                            <td>{price_vs_ma:.2f}%</td>
                        </tr>
                    </table>
                </div>
                
                <h2>详细报告</h2>
                <div class="report">
                    {report_text.replace('\n', '<br>')}
                </div>
                
                <div class="chart">
                    <h2>策略图表</h2>
                    <img src="cid:strategy_chart" alt="策略表现图表" style="max-width:100%;">
                </div>
                
                <div class="footer">
                    <p>此邮件由增强西格尔策略自动生成，请勿直接回复。</p>
                    <p>© {current_year} 增强西格尔策略 - GitHub Actions 自动化通知系统</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
