# 增强西格尔策略 (Enhanced Siegel Strategy)

这是一个基于技术分析的交易系统，通过多信号组合和动态仓位管理，在保持较低回撤的同时提供稳定回报。该策略采用Python实现并部署在GitHub Actions上，可自动执行信号分析并通过邮件发送交易提醒。

## 核心性能指标

| 指标 | 增强西格尔 | 买入持有 |
|--------|----------------|------------|
| 总回报率 | 8,434.29% | 9,883.97% |
| 年化收益率 | 7.04% | 7.30% |
| 最大回撤 | -28.04% | -56.24% |
| **夏普比率** | **0.689** | 0.524 |
| 年化波动率 | 10.67% | 15.78% |
| 胜率 | 58.0% | - |
| 交易次数 | 185 | 1 |

## 项目结构

```
enhanced-siegel-strategy/
├── .github/
│   └── workflows/
│       └── strategy.yml        # GitHub Actions工作流配置
├── data/
│   ├── position_history.csv    # 仓位历史记录
│   └── SPX_data.csv            # 股票数据缓存
├── charts/                     # 生成的图表目录
├── src/
│   ├── enhanced_siegel.py      # 核心策略实现
│   ├── data_loader.py          # 数据获取模块
│   ├── signal_analyzer.py      # 信号分析模块
│   └── notification.py         # 邮件通知模块
├── run_strategy.py             # 主运行脚本
├── requirements.txt            # 依赖库列表
├── config.ini                  # 配置文件（需要自行创建）
└── README.md                   # 项目说明
```

## 安装与配置

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/enhanced-siegel-strategy.git
cd enhanced-siegel-strategy
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 创建配置文件

```bash
python run_strategy.py --create-config
```

这将创建一个`config.ini`文件，您需要编辑该文件以配置您的API密钥和邮件设置。

### 4. 配置文件说明

`config.ini`文件包含以下配置部分：

#### 策略配置 (Strategy)

```ini
[Strategy]
ma_long = 45
ma_short = 20
rsi_period = 14
macd_fast = 12
macd_slow = 26
macd_signal = 9
adx_period = 14
atr_period = 14
atr_multiplier = 2.5
signal_threshold = 0.5
strong_signal = 0.75
very_strong_signal = 0.9
weak_signal = 0.65
trend_weight = 0.4
slope_weight = 0.25
momentum_weight = 0.2
environment_weight = 0.15
```

#### 数据配置 (Data)

```ini
[Data]
symbol = SPY
lookback_years = 10
finnhub_api_key = your_finnhub_api_key
data_dir = data
charts_dir = charts
```

#### 通知配置 (Notification)

```ini
[Notification]
email_sender = your_email@gmail.com
email_password = your_app_password
email_recipient = recipient@example.com
smtp_server = smtp.gmail.com
smtp_port = 587
```

## 使用方法

### 本地运行

```bash
python run_strategy.py
```

### 命令行选项

- `--config <file>`: 指定配置文件路径（默认为`config.ini`）
- `--create-config`: 创建配置文件模板
- `--force-download`: 强制重新下载数据
- `--no-email`: 不发送邮件通知

示例：

```bash
python run_strategy.py --force-download --no-email
```

## 部署到GitHub Actions

### 1. Fork或克隆仓库到GitHub

在GitHub上创建一个新仓库，并将本地代码推送到该仓库。

### 2. 设置GitHub密钥

在GitHub仓库页面，进入`Settings` > `Secrets` > `Actions`，添加以下密钥：

- `EMAIL_SENDER`: 发送通知的邮箱地址
- `EMAIL_PASSWORD`: 邮箱应用专用密码
- `EMAIL_RECIPIENT`: 接收通知的邮箱地址
- `FINNHUB_API_KEY`: Finnhub API密钥（可选，如果不设置将使用配置文件中的密钥）

### 3. 启用GitHub Actions

在仓库的`Actions`选项卡中启用工作流。工作流将按照`.github/workflows/strategy.yml`文件中的配置定期运行（默认为每周一上午9点）。

您也可以手动触发工作流运行。

## 策略说明

### 核心技术特点

1. **多信号组合系统（加权）**
   - 主趋势信号（45周移动平均线，权重40%）
   - 趋势强度信号（20周移动平均线斜率，权重25%）
   - 动量信号（MACD和RSI组合，权重20%）
   - 市场环境信号（ADX和波动率，权重15%）

2. **动态仓位管理**
   - 基础信号阈值0.5（综合加权信号）
   - 强信号时增加仓位（≥0.75时为120%）
   - 极强信号时进一步增加仓位（≥0.9时为140%）
   - 弱信号时减少仓位（0.5-0.65为80%）

3. **智能止损系统**
   - 基于ATR的动态止损（2.5倍ATR）
   - 技术位止损（跌破20周移动平均线）
   - 使用两种止损中较高者，提供最佳保护

## 许可证

MIT

## 免责声明

本项目仅供学习和研究目的使用。交易涉及风险，过往业绩不代表未来表现。使用本策略进行实际交易前，请充分了解相关风险，并结合自身风险承受能力做出决策。作者不对使用本策略产生的任何损失负责。
# SPY-enhanced-siegel-strategy
