# 增强西格尔策略（Sharpe比率0.689）与GitHub自动化通知系统

## 策略概述

增强西格尔策略是一种基于技术分析的交易系统，通过多信号组合和动态仓位管理，在保持较低回撤的同时提供稳定回报。该策略采用Python实现并部署在GitHub Actions上，可自动执行信号分析并通过邮件发送交易提醒。

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

## 策略优势

1. **卓越的风险控制**：最大回撤仅为买入持有策略的一半，投资过程更平稳
2. **优化的风险调整收益**：虽然总回报率略低，但夏普比率显著高于买入持有策略
3. **低交易频率**：65年测试周期中仅185次交易，年均交易约2.8次
4. **市场环境适应性**：能够根据不同市场条件自动调整仓位和策略行为

## 核心技术特点

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

## GitHub部署架构

该策略采用GitHub Actions实现自动化运行，主要包含以下组件：

1. **数据获取模块**
   - 使用YFinance API获取最新标普500指数数据
   - 自动处理数据清洗和周度转换

2. **策略执行模块**
   - 计算技术指标和生成信号
   - 记录历史仓位和交易建议

3. **通知系统**
   - 邮件通知：检测到新信号时自动发送
   - 结果存储：将分析结果保存至仓库

4. **自动化工作流**
   - 定时执行：每周/每日自动运行策略
   - 错误处理：包含完整的日志和重试机制
   - 数据持久化：使用GitHub存储历史记录

## 部署到GitHub的步骤

1. **Fork或克隆仓库**
```bash
git clone https://github.com/yourusername/enhanced-siegel-strategy.git
cd enhanced-siegel-strategy
```

2. **设置GitHub密钥**
   - 在仓库Settings > Secrets > Actions中添加以下密钥：
     - `EMAIL_SENDER`: 发送通知的邮箱地址
     - `EMAIL_PASSWORD`: 邮箱应用专用密码
     - `EMAIL_RECIPIENT`: 接收通知的邮箱地址

3. **配置工作流文件**
   - 确保`.github/workflows/strategy.yml`文件存在
   - 可根据需要调整运行频率（默认每周一运行）

4. **初始化数据（可选）**
   - 推送初始数据文件到`data/`目录
   - 或在首次工作流运行时自动下载

5. **启用GitHub Actions**
   - 在仓库Actions选项卡中启用工作流
   - 可手动触发一次来验证设置

## GitHub工作流配置示例

```yaml
name: Enhanced Siegel Strategy

on:
  schedule:
    - cron: '0 9 * * 1'  # 每周一上午9点运行
  workflow_dispatch:  # 允许手动触发

jobs:
  run-strategy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      
      - name: Run strategy
        env:
          EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          EMAIL_RECIPIENT: ${{ secrets.EMAIL_RECIPIENT }}
        run: |
          python run_strategy.py
      
      - name: Commit results
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/position_history.csv charts/
          git commit -m "Update strategy results [skip ci]" || echo "No changes to commit"
          git push
```

## 代码文件结构

```
enhanced-siegel-strategy/
├── .github/
│   └── workflows/
│       └── strategy.yml
├── data/
│   ├── position_history.csv
│   └── SPX_data.csv
├── charts/
├── src/
│   ├── enhanced_siegel.py    # 核心策略实现
│   ├── data_loader.py        # 数据获取模块
│   ├── signal_analyzer.py    # 信号分析模块
│   └── notification.py       # 邮件通知模块
├── run_strategy.py           # 主运行脚本
├── requirements.txt
├── README.md
└── docs/
    └── Enhenced_sigel_github_PRD.md
```

## 扩展和定制

1. **调整信号权重**：可修改`src/enhanced_siegel.py`中的权重配置
2. **添加其他数据源**：扩展`data_loader.py`支持其他API
3. **自定义通知内容**：修改`notification.py`中的邮件模板
4. **增加其他资产**：扩展策略以支持更多指数或股票

## 注意事项

- GitHub Actions有运行时间限制，策略执行时间不应过长
- 敏感信息（如API密钥和密码）应通过GitHub Secrets管理
- 定期检查工作流运行状态和通知系统是否正常工作
- 数据可能会随时间累积，考虑定期清理或存档旧数据

