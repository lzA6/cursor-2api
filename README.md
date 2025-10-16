<div align="center">

# cursor-2api 🚀

**将 Cursor.com 网页版转化为 OpenAI 标准 API 的解决方案**

![版本](https://img.shields.io/badge/version-v3.1-blue)
![协议](https://img.shields.io/badge/license-Apache%202.0-green)
![技术栈](https://img.shields.io/badge/tech-FastAPI%20%7C%20Playwright%20%7C%20Docker-orange)
![讨论](https://img.shields.io/badge/discussions-welcome-purple)

</div>

> "我们并非在创造魔法，我们只是在用代码揭示早已存在的可能性。正如黑客精神的本质——不是破坏，而是用一种前所未有的方式，让系统展现出它被设计时未曾预料到的美丽。"

---

## ✨ 项目简介

`cursor-2api` 是一个创新的中间件解决方案，它通过浏览器自动化技术将 Cursor.com 的网页聊天界面转化为标准的 OpenAI API 格式。

由于 Cursor 官方未提供公开的 API 接口，本项目通过自动化浏览器操作，模拟真实用户行为，让你能够以标准 OpenAI API 的方式调用 Cursor 背后的强大 AI 模型（包括 GPT-4o、Claude 3.5 Sonnet 等）。

### 🎯 核心价值

- **无缝集成**: 100% 兼容 OpenAI API 格式，可直接接入任何支持 OpenAI 的第三方应用
- **模型多样性**: 支持 Cursor 提供的所有可用模型
- **零配置部署**: 提供 Docker 一键部署方案
- **实时流式响应**: 完整支持 Server-Sent Events (SSE) 流式传输

---

## 🏗️ 架构原理

### 核心工作流程

```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI
    participant P as Playwright
    participant B as Browser
    participant S as Cursor Server

    C->>F: 发送 OpenAI 格式请求
    F->>P: 处理并准备 Payload
    P->>B: 注入拦截脚本
    B->>S: 发送修改后的请求
    S->>B: 返回流式响应
    B->>P: 通过队列实时转发
    P->>F: 转换为 SSE 格式
    F->>C: 流式返回响应
```

### 关键技术点

1. **浏览器自动化**: 使用 Playwright 控制无头浏览器访问 Cursor 网页
2. **请求拦截**: 通过注入的 JavaScript 脚本修改浏览器 fetch 请求
3. **实时流处理**: 利用 asyncio.Queue 实现浏览器到后端的实时数据传递
4. **格式转换**: 将 Cursor 的响应格式转换为标准 OpenAI API 格式

---

## 📁 项目结构

```
cursor-2api/
├── .env                    # 环境配置文件
├── .env.example           # 环境配置模板
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── main.py                # FastAPI 应用入口
├── nginx.conf             # Nginx 反向代理配置
├── requirements.txt       # Python 依赖列表
└── app/                   # 核心应用代码
    ├── core/
    │   ├── __init__.py
    │   └── config.py      # 配置管理
    ├── providers/
    │   ├── __init__.py
    │   ├── base_provider.py    # Provider 基类
    │   ├── cursor_provider.py  # Cursor 提供商实现
    │   └── fetch_override.js   # 请求拦截脚本
    └── utils/
        └── sse_utils.py   # SSE 工具函数
```

---

## 🚀 快速部署

### 环境要求

- Docker & Docker Compose
- 至少 2GB 可用内存
- 稳定的网络连接

### 部署步骤

#### 1. 克隆项目

```bash
git clone https://github.com/lzA6/cursor-2api.git
cd cursor-2api
```

#### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# ====================================================================
# cursor-2api 配置文件
# ====================================================================

# API 访问密钥（建议设置为复杂字符串）
API_MASTER_KEY=your-secret-key-here

# 服务端口
NGINX_PORT=8088
```

#### 3. 启动服务

```bash
docker-compose up -d
```

#### 4. 验证部署

```bash
curl -X POST http://localhost:8088/v1/chat/completions \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": "你好，请介绍一下你自己"
      }
    ],
    "stream": true
  }'
```

---

## 🛠️ 技术栈详解

| 技术组件 | 作用 | 学习资源 | 复杂度 |
|---------|------|----------|--------|
| **FastAPI** | 构建高性能 Web API 服务 | [官方文档](https://fastapi.tiangolo.com/) | ⭐⭐☆☆☆ |
| **Playwright** | 浏览器自动化与控制 | [Playwright Python](https://playwright.dev/python/) | ⭐⭐⭐☆☆ |
| **Docker** | 应用容器化与部署 | [Docker 教程](https://docs.docker.com/get-started/) | ⭐⭐⭐☆☆ |
| **Nginx** | 反向代理与负载均衡 | [Nginx 指南](https://nginx.org/en/docs/) | ⭐⭐☆☆☆ |
| **Asyncio** | 异步编程与并发处理 | [Python Asyncio](https://docs.python.org/3/library/asyncio.html) | ⭐⭐⭐⭐☆ |
| **JavaScript Injection** | 浏览器请求拦截与修改 | [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) | ⭐⭐⭐⭐☆ |

---

## 📊 功能特性

### ✅ 已实现功能

- [x] OpenAI API 标准兼容
- [x] 多模型支持（GPT-4o、Claude 3.5 Sonnet 等）
- [x] 流式响应（Server-Sent Events）
- [x] 自动上下文管理
- [x] 动态 Token 计数
- [x] 会话持久化
- [x] Docker 容器化部署

### 🚧 待实现功能

- [ ] 多账户轮换
- [ ] 请求频率限制
- [ ] 使用量统计
- [ ] Web 管理界面
- [ ] 健康检查端点

---

## ⚖️ 优势与局限

### ✅ 优势

1. **成本效益**: 免费使用 Cursor 提供的顶级 AI 模型
2. **兼容性强**: 无缝对接现有 OpenAI 生态应用
3. **智能上下文**: 自动检测和管理对话上下文限制
4. **持续更新**: 随 Cursor 官网更新而自动获取新功能
5. **开源透明**: 完整源代码，可自定义扩展

### ⚠️ 局限与风险

1. **依赖网站结构**: Cursor 前端更新可能导致服务中断
2. **性能开销**: 浏览器自动化相比原生 API 有额外资源消耗
3. **服务条款**: 可能违反 Cursor 的使用协议
4. **功能限制**: 仅支持聊天功能，不支持图像生成等其他能力

---

## 🔮 发展路线图

### 近期目标
- 增强错误处理和自动恢复机制
- 添加请求队列和限流功能
- 实现配置热重载

### 中期规划  
- 支持多提供商架构（Poe、Claude 官网等）
- 开发 Web 管理面板
- 优化资源使用效率

### 长期愿景
- 一键云平台部署
- 智能模型路由
- 社区驱动的功能开发

---

## 🤖 技术深度解析

### 核心模块说明

#### 1. Playwright 管理器 (`cursor_provider.py`)
```python
class PlaywrightManager:
    """管理浏览器实例的生命周期"""
    async def get_page(self) -> Page:
        # 获取或创建浏览器页面
        pass
    
    async def cleanup(self):
        # 清理资源
        pass
```

#### 2. 请求拦截机制 (`fetch_override.js`)
```javascript
// 拦截并修改 fetch 请求
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    if (args[0].includes('/chat/completions')) {
        // 修改请求体并处理响应流
        return handleChatCompletion(...args);
    }
    return originalFetch.apply(this, args);
};
```

#### 3. 流式响应处理 (`sse_utils.py`)
```python
async def stream_generator(queue: asyncio.Queue):
    """从队列生成 SSE 流"""
    while True:
        chunk = await queue.get()
        if chunk is None:  # 结束信号
            break
        yield f"data: {chunk}\n\n"
```

### 扩展开发指南

要添加新的提供商：

1. 继承 `BaseProvider` 类
2. 实现 `chat_completion` 方法
3. 添加对应的浏览器自动化逻辑
4. 注册到提供商工厂

---

## 📜 开源协议

本项目采用 **Apache License 2.0** 协议。

**你可以：**
- 商业使用
- 修改代码
- 分发副本
- 专利授权

**你需要：**
- 包含版权声明
- 声明修改内容

**你不能：**
- 使用商标
- 追究责任

完整协议内容请参阅 [LICENSE](./LICENSE) 文件。

---

## 🤝 贡献与支持

### 问题反馈
如遇问题，请通过 [GitHub Issues](https://github.com/lzA6/cursor-2api/issues) 提交。

### 技术讨论
欢迎加入 [Discussions](https://github.com/lzA6/cursor-2api/discussions) 参与技术交流。

### 开发贡献
1. Fork 本仓库
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

---

## 💭 结语

> 技术是中立的工具，关键在于我们如何使用它。这个项目展示了如何通过创新思维突破技术限制，让更多人能够接触到先进的 AI 技术。
>
> 我们鼓励负责任的使用方式，尊重服务提供商的权益，同时推动技术的开放和普及。
>
> 希望这个项目能启发你探索更多的技术可能性，用代码创造价值。

**Happy Coding! 🚀**

---
