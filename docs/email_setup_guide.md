# GitHub Actions 邮件通知配置指南

本指南将帮助你正确配置GitHub Actions的邮件通知功能，确保增强西格尔策略信号能够及时通过邮件发送给你。

## 配置步骤

### 1. 在GitHub仓库中设置Secrets

1. 打开你的GitHub仓库
2. 点击 `Settings` -> `Secrets and variables` -> `Actions`
3. 点击 `New repository secret` 添加以下Secrets：

| 名称 | 说明 | 示例值 |
|------|------|--------|
| `EMAIL_SENDER` | 发送邮件的邮箱地址 | 1521080337@qq.com |
| `EMAIL_PASSWORD` | 邮箱授权码/应用密码（非登录密码） | htbfsspjqdtljigg |
| `EMAIL_RECIPIENT` | 接收邮件的邮箱地址 | 1521080337@qq.com |
| `SMTP_SERVER` | SMTP服务器地址 | smtp.qq.com |
| `SMTP_PORT` | SMTP服务器端口 | 465 |
| `FINNHUB_API_KEY` | Finnhub API密钥 | d0qh65pr01qt60oocosgd0qh65pr01qt60oocot0 |

### 2. 获取邮箱授权码/应用密码

#### QQ邮箱

1. 登录你的QQ邮箱 (https://mail.qq.com/)
2. 点击 `设置` -> `账户`
3. 找到 "POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务" 部分
4. 开启 "POP3/SMTP服务" 或 "IMAP/SMTP服务"
5. 按照提示验证你的身份，获取授权码
6. 将授权码作为 `EMAIL_PASSWORD` 添加到GitHub Secrets中

#### Gmail

1. 登录你的Google账户
2. 访问 [Google账户安全设置](https://myaccount.google.com/security)
3. 开启 "两步验证"
4. 访问 [应用专用密码](https://myaccount.google.com/apppasswords)
5. 在 "选择应用" 下选择 "邮件"，在 "选择设备" 下选择你使用的设备
6. 点击 "生成" 获取应用专用密码
7. 将应用专用密码作为 `EMAIL_PASSWORD` 添加到GitHub Secrets中

### 3. 邮箱服务器设置参考

| 邮箱服务 | SMTP_SERVER | SMTP_PORT (SSL) | SMTP_PORT (TLS) | 说明 |
|---------|------------|----------------|----------------|------|
| QQ邮箱 | smtp.qq.com | 465 | 587 | 建议使用SSL端口465 |
| Gmail | smtp.gmail.com | 465 | 587 | 建议使用SSL端口465 |
| 163邮箱 | smtp.163.com | 465 | 25 | 建议使用SSL端口465 |
| Outlook/Hotmail | smtp-mail.outlook.com | 587 | 587 | 只支持TLS端口587 |

## 测试配置是否正确

配置完成后，你可以手动触发工作流来测试邮件发送功能：

1. 打开你的GitHub仓库
2. 点击 `Actions` 标签页
3. 找到 `Enhanced Siegel Strategy Monitor` 工作流
4. 点击 `Run workflow` 手动触发工作流

工作流运行完成后，检查你的邮箱是否收到通知邮件。如果没有收到，请检查：

1. 工作流运行日志中是否有错误信息
2. 垃圾邮件文件夹
3. Secrets配置是否正确
4. 邮箱服务是否限制了第三方应用登录

## 本地测试邮件配置

你也可以在本地测试邮件配置是否正确：

```bash
# 测试本地配置文件中的邮件设置
python send_test_email.py

# 测试特定邮箱配置
python test_github_actions_email.py --sender your-email@example.com --password your-password --recipient your-email@example.com --smtp smtp.example.com --port 465
```

## 常见问题排查

### 1. 认证失败

错误信息: `SMTPAuthenticationError: (535, 'Error: authentication failed')`

可能原因:
- 密码错误，确保使用的是授权码/应用密码，而不是登录密码
- 邮箱安全设置限制了第三方应用访问

解决方案:
- 重新生成授权码/应用密码
- 检查邮箱安全设置，允许第三方应用访问

### 2. 连接超时

错误信息: `socket.timeout: timed out`

可能原因:
- 网络问题导致无法连接到SMTP服务器
- SMTP服务器地址错误

解决方案:
- 检查SMTP服务器地址是否正确
- 尝试使用不同的SMTP端口
- 检查网络连接

### 3. 邮件被标记为垃圾邮件

可能原因:
- 邮件主题或内容含有垃圾邮件特征
- 发送频率过高
- 邮件服务提供商的策略

解决方案:
- 检查垃圾邮件文件夹
- 将GitHub Actions邮箱添加到安全发件人名单
- 适当减少邮件发送频率 