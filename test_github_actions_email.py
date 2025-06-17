#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模拟GitHub Actions环境中的邮件发送测试
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试GitHub Actions邮件发送')
    parser.add_argument('--sender', required=True, help='发件人邮箱')
    parser.add_argument('--password', required=True, help='邮箱密码/授权码')
    parser.add_argument('--recipient', required=True, help='收件人邮箱')
    parser.add_argument('--smtp', required=True, help='SMTP服务器')
    parser.add_argument('--port', type=int, required=True, help='SMTP端口')
    
    args = parser.parse_args()
    
    # 邮件配置
    sender_email = args.sender
    password = args.password
    recipient_email = args.recipient
    smtp_server = args.smtp
    smtp_port = args.port

    print(f"配置信息:")
    print(f"- 发件人: {sender_email}")
    print(f"- 收件人: {recipient_email}")
    print(f"- SMTP服务器: {smtp_server}")
    print(f"- SMTP端口: {smtp_port}")

    # 创建邮件
    msg = MIMEMultipart()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg['Subject'] = f"【GitHub Actions测试】增强西格尔策略系统 - {current_time}"
    msg['From'] = f"GitHub Actions <{sender_email}>"
    msg['To'] = recipient_email

    # 邮件正文
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #f5f5f5; padding: 15px; margin-bottom: 20px; }}
            .content {{ padding: 15px; }}
            .footer {{ margin-top: 20px; font-size: 0.8em; color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>GitHub Actions 邮件测试</h1>
                <p>生成时间: {current_time}</p>
            </div>
            
            <div class="content">
                <h2>模拟 GitHub Actions 邮件发送测试</h2>
                <p>这是一封模拟 GitHub Actions 发送的测试邮件，用于验证增强西格尔策略监控系统的邮件发送功能是否正常工作。</p>
                <p>如果您收到此邮件，说明邮件配置正确，GitHub Actions 可以正常发送邮件通知。</p>
                <p>这是从本地环境模拟的 GitHub Actions 运行，使用与 GitHub Actions 相同的配置。</p>
            </div>
            
            <div class="footer">
                <p>此邮件由增强西格尔策略自动生成，用于测试目的，请勿直接回复。</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    # 发送邮件
    try:
        print("\n尝试发送测试邮件...")
        context = ssl.create_default_context()
        
        # 根据端口选择合适的连接方式
        if smtp_port == 465:
            # 使用SSL连接
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                print("- 建立SSL连接")
                server.login(sender_email, password)
                print("- 登录成功")
                server.sendmail(sender_email, recipient_email, msg.as_string())
                print("- 发送邮件")
                
                # 安全关闭连接
                try:
                    server.quit()
                    print("- 连接已安全关闭")
                except Exception as e:
                    print(f"- 关闭连接时发生异常，但邮件已发送: {e}")
        else:
            # 使用STARTTLS
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                print("- 建立STARTTLS连接")
                server.starttls(context=context)
                print("- 启用TLS加密")
                server.login(sender_email, password)
                print("- 登录成功")
                server.sendmail(sender_email, recipient_email, msg.as_string())
                print("- 发送邮件")
                
                # 安全关闭连接
                try:
                    server.quit()
                    print("- 连接已安全关闭")
                except Exception as e:
                    print(f"- 关闭连接时发生异常，但邮件已发送: {e}")
        
        print(f"\n✅ 邮件发送成功！请检查 {recipient_email} 收件箱")
        print("如果没有收到邮件，请检查垃圾邮件文件夹")
        
    except Exception as e:
        print(f"\n❌ 发送邮件时出错: {e}")
        print("\n可能的问题排查:")
        print("1. 检查SMTP服务器和端口配置是否正确")
        print("2. 检查邮箱密码是否正确(QQ邮箱需要使用授权码，Gmail需要使用应用专用密码)")
        print("3. 检查邮箱是否开启了SMTP服务")
        print("4. 如果使用Gmail，检查是否开启了两步验证并创建了应用专用密码")
        print("5. 检查网络连接是否正常")


if __name__ == "__main__":
    main() 