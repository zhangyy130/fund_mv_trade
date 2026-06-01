# 基金均值交易系统

基金净值采集、均线分析、交易策略配置与回测系统。

## 功能特性

- 📊 基金净值数据采集与管理
- 📈 交互式净值图表展示
- 🎯 交易策略配置
- 🔄 策略回测验证

## 技术栈

- Python 3.10+
- Streamlit (Web UI)
- pandas + numpy (数据处理)
- akshare (基金数据采集)
- plotly (交互式图表)
- SQLite (本地存储)

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python run.py
# 或
streamlit run views/app.py
```

应用将在 http://localhost:8501 启动

### GitHub Codespaces

1. 打开仓库页面，点击 "Code" -> "Codespaces"
2. 点击 "Create codespace on main"
3. 等待环境自动配置完成
4. 访问转发的 8501 端口

详见 [CODESPACE_README.md](CODESPACE_README.md)

## 项目结构

```
fund_mv_trade/
├── models/                 # 数据模型层
│   ├── fund_data.py       # 数据采集
│   ├── fund_db.py         # 数据库操作
│   └── indicators.py      # 技术指标计算
├── controllers/            # 控制器层
│   ├── fund_manager.py    # 基金管理
│   ├── strategy.py        # 策略框架
│   └── backtester.py      # 回测引擎
├── views/                  # 视图层
│   ├── app.py             # 入口页面
│   ├── page_fund.py       # 基金管理页面
│   ├── page_chart.py      # 净值图表页面
│   ├── page_strategy.py   # 策略配置页面
│   └── page_backtest.py   # 策略回测页面
├── .devcontainer/          # Codespace 配置
├── config.py              # 全局配置
├── run.py                 # 启动脚本
└── requirements.txt       # Python 依赖
```

## 开发规范

- **模型层**：纯函数无副作用，可独立测试
- **控制层**：通过模型层接口操作数据
- **视图层**：只做 UI 渲染，业务逻辑委托给控制层
- **配置**：所有可调参数统一放 `config.py`

## License

MIT
