# AGENTS.md — AI 协作指南

## 项目架构

MVC 分层：`views/` → `controllers/` → `models/`，依赖单向向下。

## 修改规则

### 新增数据源
1. 在 `models/fund_data.py` 继承 `BaseFundDataSource`
2. 实现 `fetch_nav()` 和 `fetch_fund_info()`
3. 修改 `get_default_source()` 返回新实现
4. 上层代码无需改动

### 新增交易策略
1. 在 `controllers/strategy.py` 中新增规则工厂函数（返回 `Rule` 对象）
2. 在 `StrategyRegistry.BUILTIN_STRATEGIES` 中注册
3. 或通过 `StrategyRegistry.build_custom()` 从参数构建

### 新增技术指标
1. 在 `models/indicators.py` 中添加纯函数
2. 函数只接收 pandas Series/DataFrame，返回计算结果
3. 无副作用，不依赖数据库或外部服务

### 新增页面
1. 在 `views/` 下新建 `page_xxx.py`，定义 `render(mgr)` 函数
2. 在 `views/app.py` 的路由中添加页面入口
3. 页面只做 UI 渲染，业务逻辑调用 controllers 层

### 修改存储层
1. 新增 `models/fund_db_xxx.py` 实现与 `FundDB` 相同的接口
2. 在控制层构造函数中注入新实现
3. 不要修改已有的调用方代码

## 禁止事项

- **不要**在 models 层导入 views 或 controllers 的任何模块
- **不要**在 views 层直接操作数据库（通过 controllers 间接调用）
- **不要**在 indicators.py 中引入有副作用的操作（网络请求、文件 IO）
- **不要**把配置硬编码在业务代码中，统一放 `config.py`
- **不要**在视图层写业务计算逻辑

## 测试策略

- `models/indicators.py`：纯函数，可直接用 pytest 单元测试
- `controllers/strategy.py`：构造测试 DataFrame 验证规则触发
- `controllers/backtester.py`：用已知数据验证回测统计结果
- `models/fund_db.py`：用临时数据库文件测试 CRUD
- `models/fund_data.py`：mock 数据源接口测试上层逻辑

## 代码风格

- 类型注解：函数签名使用 type hints
- 命名：snake_case（变量/函数）、PascalCase（类）
- 注释：仅在非显而易见处添加，不写显而易见的注释
- 导入顺序：标准库 → 第三方库 → 本地模块
