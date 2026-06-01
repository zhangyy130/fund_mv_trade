# 基金均值交易系统

## 项目概述

基金净值采集、均线分析、交易策略配置与回测系统。基于 Streamlit + Python，采用 MVC 分层架构。

## 技术栈

- Python 3.10+
- Streamlit（视图层）
- pandas + numpy（计算引擎）
- akshare（基金数据采集）
- plotly（交互式图表）
- SQLite（本地存储）

## 架构分层

```
views/       → 控制层 → models/
（Streamlit UI）  （业务逻辑）  （数据 & 算法）
```

**依赖方向**：views → controllers → models，单向不反向。models 不依赖任何上层。

- `models/` — 数据采集（抽象接口）、存储（SQLite）、技术指标（纯函数）
- `controllers/` — 基金管理、策略框架（规则引擎）、回测引擎
- `views/` — Streamlit 页面，仅负责 UI 交互与数据展示
- `config.py` — 全局配置集中管理

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动项目
python run.py
# 或
streamlit run views/app.py
```

## 开发规范

- **模型层**：纯函数无副作用，可独立测试。新增数据源实现 `BaseFundDataSource` 接口即可替换。
- **控制层**：通过模型层接口操作数据，不直接引用具体实现。策略通过规则引擎组合，新增策略用工厂函数。
- **视图层**：只做 UI 渲染和用户输入，业务逻辑全部委托给控制层。
- **配置**：所有可调参数统一放 `config.py`，不要散落在各模块。
- **数据源切换**：修改 `models/fund_data.py` 中的 `get_default_source()` 工厂函数。
- **存储切换**：新增 `fund_db_xxx.py` 实现相同接口，在控制层注入即可。

## 关键文件

| 文件 | 职责 |
|---|---|
| `models/fund_data.py` | 数据采集抽象 + akshare 实现 |
| `models/fund_db.py` | SQLite CRUD 封装 |
| `models/indicators.py` | 均线计算、上穿检测、走平检测（纯函数） |
| `controllers/strategy.py` | 策略框架、规则工厂、内置策略、自定义构建器 |
| `controllers/backtester.py` | 回测引擎（模拟交易、统计指标计算） |
| `controllers/fund_manager.py` | 基金管理业务逻辑 |
| `views/app.py` | Streamlit 入口 & 页面路由 |
| `config.py` | 全局配置 |
