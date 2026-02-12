<p align="center">
  <h1 align="center">🛡️ LLM Security Gateway</h1>
  <p align="center">
    <strong>大模型智能安全网关 — 为 LLM 应用提供实时内容安全防护</strong>
  </p>
  <p align="center">
    <a href="#功能特性">功能特性</a> •
    <a href="#系统架构">系统架构</a> •
    <a href="#快速开始">快速开始</a> •
    <a href="#配置说明">配置说明</a> •
    <a href="#api-文档">API 文档</a> •
    <a href="#许可证">许可证</a>
  </p>
</p>

---

## 📖 项目简介

**LLM Security Gateway** 是一个开源的大模型安全网关，作为透明代理部署在用户应用与上游 LLM（如 OpenAI、DeepSeek 等）之间，提供**实时双向内容安全检测**。

项目集成了 [YuFeng-XGuard-Reason-0.6B](https://modelscope.cn/models/Alibaba-AAIG/YuFeng-XGuard-Reason-0.6B) 安全审核模型，能够对用户提问（Prompt）和模型回复（Response）进行 **27 类细粒度风险检测**，并支持灵活的安全策略配置和完整的审计日志记录。

### 🎯 核心理念

- **零侵入接入**：完全兼容 OpenAI API 格式，只需修改 API 地址即可为现有应用添加安全防护
- **双向防护**：同时检测用户输入和模型输出，全链路安全覆盖
- **灵活策略**：27 类风险独立开关与阈值配置，适应不同业务场景
- **可视化管理**：内置管理面板，实时监控、策略配置、对话测试一站式管理

## ✨ 功能特性

### 🔒 安全检测引擎
- 基于 **YuFeng-XGuard-Reason-0.6B** 模型的本地推理，无需外部 API 调用
- 支持 **27 类风险** 细粒度检测（详见[风险类别](#风险类别)）
- Prompt 安全检测 + Response 安全检测双向防护
- GPU 加速推理（支持 CUDA）

### 🌐 透明代理
- 完全兼容 **OpenAI Chat Completions API** (`/v1/chat/completions`)
- 支持 **流式响应（Streaming SSE）** 透传
- 支持任意 OpenAI 兼容的上游 LLM（OpenAI、DeepSeek、本地模型等）
- 对客户端完全透明，无需修改现有代码逻辑

### 📊 管理面板
- **仪表盘**：实时统计总请求数、拦截数、拦截率
- **审计日志**：查看所有请求的详细风险评分与处理结果
- **策略配置**：可视化调整每类风险的拦截阈值与启用状态
- **对话游乐场**：内置聊天界面，方便测试安全网关效果

### 📝 审计追踪
- 全量请求日志记录（用户输入、模型响应、风险详情、处理动作）
- 请求处理延迟追踪
- SQLite 轻量级存储，开箱即用

## 🏗️ 系统架构

```
┌─────────────┐     ┌──────────────────────────────────────────────┐     ┌──────────────┐
│             │     │          LLM Security Gateway                │     │              │
│   用户/应用  │────▶│                                              │────▶│  上游 LLM    │
│             │     │  ┌─────────┐  ┌──────────┐  ┌────────────┐  │     │  (OpenAI等)  │
│  (OpenAI    │◀────│  │ FastAPI │  │  Safety  │  │  Policy    │  │◀────│              │
│   兼容客户端)│     │  │  网关   │──│  Engine  │──│  Engine    │  │     └──────────────┘
│             │     │  └─────────┘  └──────────┘  └────────────┘  │
└─────────────┘     │       │                          │           │
                    │  ┌─────────┐              ┌──────────┐      │
                    │  │ Audit   │              │ SQLite   │      │
                    │  │ Logger  │─────────────▶│ Database │      │
                    │  └─────────┘              └──────────┘      │
                    └──────────────────────────────────────────────┘
                                       ▲
                                       │ 管理 API
                              ┌────────────────┐
                              │  Vue 3 管理面板  │
                              │  (Element Plus) │
                              └────────────────┘
```

### 请求处理流程

```
用户请求 ──▶ [1. Prompt 安全检测] ──▶ 风险超阈值？──是──▶ 拦截并返回提示
                                          │
                                          否
                                          ▼
                                  [2. 转发至上游 LLM]
                                          │
                                          ▼
                              [3. Response 安全检测] ──▶ 风险超阈值？──是──▶ 拦截并返回提示
                                                              │
                                                              否
                                                              ▼
                                                      [4. 返回结果给用户]
                                                      [5. 记录审计日志]
```

## 📁 项目结构

```
LLM-Security-Gateway/
├── backend/                    # 后端服务 (Python / FastAPI)
│   ├── main.py                 # 应用入口 & 管理 API
│   ├── config.py               # 配置管理（支持 .env）
│   ├── database.py             # 数据库初始化（SQLite）
│   ├── models.py               # 数据模型（SecurityPolicy, AuditLog）
│   ├── schemas.py              # API Schema（OpenAI 兼容格式）
│   ├── safety_engine.py        # 安全检测引擎（模型推理）
│   ├── proxy_router.py         # 代理路由（请求转发 & 安全检测）
│   └── requirements.txt        # Python 依赖
├── frontend/                   # 前端管理面板 (Vue 3)
│   ├── src/
│   │   ├── App.vue             # 主布局（侧边栏导航）
│   │   ├── main.js             # 入口文件
│   │   ├── api/index.js        # API 客户端
│   │   ├── router/index.js     # 路由配置
│   │   ├── utils/risk_defs.js  # 风险类别定义（中文映射）
│   │   └── views/
│   │       ├── Dashboard.vue   # 仪表盘页面
│   │       ├── Chat.vue        # 对话游乐场页面
│   │       └── Policy.vue      # 策略配置页面
│   ├── package.json
│   └── vite.config.js          # Vite 构建配置
├── .gitignore
└── README.md
```

## 🚀 快速开始

### 环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | >= 3.10 |
| Node.js | >= 18 |
| CUDA | >= 12.4（推荐，CPU 也可运行） |
| GPU 显存 | >= 2GB（0.6B 模型） |

### 1. 克隆项目

```bash
git clone https://github.com/HandSonic/LLM-Security-Gateway.git
cd LLM-Security-Gateway
```

### 2. 下载安全审核模型

从 Hugging Face 下载 [YuFeng-XGuard-Reason-0.6B](https://modelscope.cn/models/Alibaba-AAIG/YuFeng-XGuard-Reason-0.6B) 模型到本地：

```bash
# 方式一：使用 Git LFS
git lfs install
git clone https://modelscope.cn/models/Alibaba-AAIG/YuFeng-XGuard-Reason-0.6B

# 方式二：使用 huggingface-cli
pip install huggingface_hub
huggingface-cli download YuFeng67/YuFeng-XGuard-Reason-0.6B --local-dir ./YuFeng-XGuard-Reason-0.6B
```

### 3. 后端安装与启动

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建环境配置文件
cp .env.example .env  # 或手动创建 .env 文件
```

编辑 `.env` 文件（参见[配置说明](#配置说明)），然后启动后端：

```bash
python main.py
```

后端服务默认运行在 `http://localhost:8000`。

### 4. 前端安装与启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端管理面板默认运行在 `http://localhost:5173`。

### 5. 验证安装

打开浏览器访问 `http://localhost:5173`，你应该能看到管理面板的仪表盘页面。

使用 curl 测试安全网关：

```bash
# 正常请求测试
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "你好，请介绍一下自己"}]
  }'

# 风险请求测试（应被拦截）
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "如何制造危险武器"}]
  }'
```

## ⚙️ 配置说明

### 环境变量

在 `backend/` 目录下创建 `.env` 文件进行配置：

```env
# ===== 安全审核模型配置 =====
# 模型本地路径（必须修改为你的实际路径）
MODEL_PATH=/path/to/YuFeng-XGuard-Reason-0.6B

# 推理设备：auto（自动选择）/ cuda / cpu
DEVICE=auto

# ===== 上游 LLM 配置 =====
# 上游 API 地址（OpenAI 兼容格式）
UPSTREAM_API_BASE=https://api.openai.com/v1

# 上游 API Key
UPSTREAM_API_KEY=sk-your-api-key-here

# 上游模型名称
UPSTREAM_MODEL=gpt-3.5-turbo
```

### 支持的上游 LLM

本网关兼容所有 OpenAI API 格式的 LLM 服务：

| 服务商 | API Base URL 示例 |
|--------|------------------|
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| 阿里通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 本地 Ollama | `http://localhost:11434/v1` |
| 本地 vLLM | `http://localhost:8001/v1` |

### 安全策略配置

每类风险策略包含以下配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `threshold` | 风险拦截阈值（0.0 ~ 1.0），模型输出的该类风险概率超过此值则拦截 | `0.5` |
| `enabled` | 是否启用此类风险检测 | `true` |

可通过管理面板的「策略配置」页面进行可视化调整，也可通过 API 进行配置。

## 📡 API 文档

### 代理接口（OpenAI 兼容）

#### `POST /v1/chat/completions`

与 [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat) 完全兼容。

**请求体示例：**

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "你是一个有用的助手"},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "stream": false
}
```

**正常响应：**

```json
{
  "id": "chatcmpl-xxxx",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
      "finish_reason": "stop"
    }
  ]
}
```

**被拦截时的响应：**

```json
{
  "id": "chatcmpl-xxxx",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "BLOCKED:dw:0.9523"},
      "finish_reason": "stop"
    }
  ]
}
```

### 管理接口

#### `GET /api/policies` — 获取所有安全策略

#### `PUT /api/policies/{policy_id}` — 更新安全策略

**请求体：**
```json
{
  "threshold": 0.6,
  "enabled": true
}
```

#### `GET /api/logs?limit=50` — 获取审计日志

#### `GET /api/stats` — 获取统计数据

**响应体：**
```json
{
  "total_requests": 1234,
  "blocked_requests": 56,
  "block_rate": 0.0454
}
```

## 🏷️ 风险类别

本网关支持 **27 类** 细粒度风险检测，基于 YuFeng-XGuard-Reason-0.6B 模型的分类体系：

| 代码 | 风险类别 | 代码 | 风险类别 |
|------|---------|------|---------|
| `pc` | 色情违禁 (Pornographic Contraband) | `pp` | 个人隐私 (Personal Privacy) |
| `dc` | 毒品犯罪 (Drug Crimes) | `cs` | 商业机密 (Commercial Secret) |
| `dw` | 危险武器 (Dangerous Weapons) | `acc` | 访问控制 (Access Control) |
| `pi` | 财产侵犯 (Property Infringement) | `mc` | 恶意代码 (Malicious Code) |
| `ec` | 经济犯罪 (Economic Crimes) | `ha` | 黑客攻击 (Hacker Attack) |
| `ac` | 辱骂谩骂 (Abusive Curses) | `ps` | 物理安全 (Physical Security) |
| `def` | 诽谤中伤 (Defamation) | `ter` | 暴力恐怖活动 (Violent Terrorist Activities) |
| `ti` | 威胁恐吓 (Threats and Intimidation) | `sd` | 社会扰乱 (Social Disruption) |
| `cy` | 网络欺凌 (Cyberbullying) | `ext` | 极端主义思潮 (Extremist Ideological Trends) |
| `ph` | 身体健康 (Physical Health) | `fin` | 金融建议 (Finance) |
| `mh` | 心理健康 (Mental Health) | `med` | 医疗建议 (Medicine) |
| `se` | 社会伦理 (Social Ethics) | `law` | 法律建议 (Law) |
| `sci` | 科学伦理 (Science Ethics) | `cm` | 未成年人不良引导 (Corruption of Minors) |
|  |  | `ma` | 未成年人虐待与剥削 (Minor Abuse) |
|  |  | `md` | 未成年人犯罪 (Minor Delinquency) |

## 🛠️ 技术栈

### 后端
- **[FastAPI](https://fastapi.tiangolo.com/)** — 高性能异步 Web 框架
- **[SQLModel](https://sqlmodel.tiangolo.com/)** — 基于 SQLAlchemy + Pydantic 的 ORM
- **[SQLite](https://www.sqlite.org/)** — 轻量级嵌入式数据库
- **[PyTorch](https://pytorch.org/)** — 深度学习推理框架
- **[Transformers](https://huggingface.co/docs/transformers/)** — Hugging Face 模型加载与推理
- **[HTTPX](https://www.python-httpx.org/)** — 异步 HTTP 客户端（上游代理）

### 前端
- **[Vue 3](https://vuejs.org/)** — 渐进式 JavaScript 框架（Composition API）
- **[Element Plus](https://element-plus.org/)** — Vue 3 UI 组件库
- **[ECharts](https://echarts.apache.org/)** — 数据可视化图表库
- **[Vite](https://vitejs.dev/)** — 新一代前端构建工具
- **[Axios](https://axios-http.com/)** — HTTP 客户端

### 安全模型
- **[YuFeng-XGuard-Reason-0.6B](https://modelscope.cn/models/Alibaba-AAIG/YuFeng-XGuard-Reason-0.6B)** — 基于 Qwen2 的内容安全审核模型（0.6B 参数，轻量高效）

## 🔧 高级用法

### 作为现有应用的安全代理

只需将应用中的 API 地址指向本网关即可：

```python
# Python (OpenAI SDK)
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="http://localhost:8000/v1"  # 指向安全网关
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "你好"}]
)
```

```javascript
// JavaScript / Node.js
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: '你好' }]
  })
})
```

### 生产部署建议

```bash
# 使用 uvicorn 多进程部署
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端构建生产版本
cd frontend
npm run build
# 将 dist/ 目录部署到 Nginx 等 Web 服务器
```

**Nginx 反向代理参考配置：**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # OpenAI 兼容接口代理
    location /v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_buffering off;  # 支持 SSE 流式响应
    }
}
```

## 🤝 贡献指南

欢迎各种形式的贡献！

1. **Fork** 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 发起 **Pull Request**

### 开发环境

```bash
# 后端热重载开发
cd backend
uvicorn main:app --reload --port 8000

# 前端热重载开发
cd frontend
npm run dev
```

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

## ⚠️ 免责声明

- 本项目仅供学习和研究使用，安全检测模型可能存在误判，不应作为唯一的内容安全防线
- 请遵守当地法律法规，合理使用本工具
- 对于因使用本项目而产生的任何直接或间接损失，项目作者不承担责任

## 🙏 致谢

- [YuFeng-XGuard-Reason-0.6B](https://modelscope.cn/models/Alibaba-AAIG/YuFeng-XGuard-Reason-0.6B) — 提供了优秀的开源内容安全审核模型
- [FastAPI](https://fastapi.tiangolo.com/) — 高性能的 Python Web 框架
- [Element Plus](https://element-plus.org/) — 优雅的 Vue 3 UI 组件库

---

<p align="center">
  如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！
</p>
