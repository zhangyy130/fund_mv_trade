# 在 GitHub Codespaces 中运行

## 快速开始

1. 打开 GitHub 仓库页面
2. 点击绿色的 "Code" 按钮
3. 选择 "Codespaces" 选项卡
4. 点击 "Create codespace on main"

Codespace 启动后会自动：
- 安装 Python 3.10 环境
- 安装所有依赖 (requirements.txt)
- 启动 Streamlit 应用

## 访问应用

启动完成后，你会在终端看到类似输出：
```
Streamlit app running at: http://localhost:8501
```

Codespace 会自动转发 8501 端口，点击 "Open in Browser" 即可访问应用。

## 手动启动

如果应用没有自动启动，可以在终端运行：

```bash
# 激活虚拟环境（如果存在）
source .venv/bin/activate

# 启动应用
python run.py
# 或
streamlit run views/app.py --server.headless true --server.port 8501 --server.address 0.0.0.0
```

## 项目结构

```
fund_mv_trade/
├── .devcontainer/
│   ├── devcontainer.json    # Codespace 配置
│   └── start.sh            # 启动脚本
├── models/                 # 数据模型层
├── controllers/            # 控制器层
├── views/                  # 视图层 (Streamlit)
├── config.py              # 全局配置
├── run.py                 # 启动脚本
└── requirements.txt       # Python 依赖
```

## 常见问题

### 端口无法访问
- 检查 Codespace 的端口转发设置
- 确认应用监听地址为 `0.0.0.0`

### 依赖安装失败
- 检查网络连接
- 尝试手动运行 `pip install -r requirements.txt`

### 数据源连接问题
- akshare 需要访问东方财富等网站
- 确保网络可以访问这些数据源
