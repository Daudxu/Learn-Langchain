# 小浪助手（钉钉版）

<div align="center">
   <img src="https://img.shields.io/github/stars/neilzhangpro/xiaolang-dingtalk?style=social" alt="GitHub stars" />
   <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
   <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python" />
   <img src="https://img.shields.io/badge/🦜_LangChain-Powered-blue" alt="LangChain" />
</div>
<div align="center">作者: tomieweb@gmail.com</div>
<div align="center">1goto.ai</div>

***

## 📖 项目简介
小浪助手是一个基于 LangChain 框架开发的智能 Agent 教学案例，旨在展示如何构建一个具有实际应用价值的 AI 助手。在当前 AI 技术快速迭代的背景下，掌握 AI Agents 开发已成为技术从业者的必备技能。本项目通过实战案例，帮助开发者快速入门 AI Agents 开发领域。

## 🚀 核心功能

- 🤖 基础 Agent 交互系统
- 📚 基于 RAG (检索增强生成) 的知识库查询
- 🔍 实时在线搜索能力
- 📅 钉钉日历与待办事项自然语言交互
- 🎭 情绪识别与多轮对话策略
- ⚡ 智能任务优先级调整

## 🛠️ 技术栈

- LangChain
- Python 3.9+
- DingTalk OpenAPI
- Vector Database
- Emotion Analysis Models

## ✍️ 基本技术架构图
![](系统架构.png)

## ⚙️ 安装说明

### 1. 系统要求
- Python 3.9 或更高版本
- Redis Stack 服务器
- Git（用于克隆项目）

### 2. 安装步骤

#### 2.1 克隆项目
```bash
git clone https://git.imooc.com/coding-925/jiaoxue.git
cd Single
```

#### 2.2 安装 Redis Stack
根据您的操作系统选择相应的安装方式：

**MacOS**:
```bash
brew install redis-stack
```

**Ubuntu/Debian**:
```bash
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis-stack-server
```

**Windows**:
- 访问 [Redis 下载页面](https://redis.io/download/)
- 下载并安装 Redis Stack

#### 2.3 安装 Python 依赖
使用 Poetry 安装项目依赖：
```bash
# 安装 Poetry（如果未安装）
pip install poetry

# 安装项目依赖
poetry install

# 激活虚拟环境（二选一）：
# 方式1：使用新的 env activate 命令（推荐）
poetry env use python3
source $(poetry env info --path)/bin/activate  # Unix/MacOS
# 或
.\$(poetry env info --path)\Scripts\activate   # Windows

# 方式2：安装并使用 shell 插件
poetry self add poetry-plugin-shell
poetry shell
```
### 3. 环境配置

在项目根目录创建 `.env` 文件，配置以下必要参数：

```env
# API Keys
SERPAPI_API_KEY=your_serpapi_key          # 搜索引擎 API key
OPENAI_API_KEY=your_openai_key            # OpenAI API key
OPENAI_API_BASE=your_openai_proxy         # OpenAI 代理地址（如果需要）
AZURE_API_KEY=your_azure_key              # 微软云 API key

# 主模型配置
BASE_MODEL=gpt-4                          # 主模型名称
DEEPSEEK_API_KEY=your_deepseek_key       # 备用模型 key
DEEPSEEK_API_BASE=https://api.siliconflow.cn/v1
BACKUP_MODEL=deepseek-ai/DeepSeek-V2.5   # 备用模型名称

# 嵌入模型配置
EMBEDDING_MODEL=Pro/BAAI/bge-m3
EMBEDDING_API_KEY=your_embedding_key
EMBEDDING_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_COLLECTION=xiaolang_documents

# 向量数据库配置
PERSIST_DIR=./vector_db
CHUNK_SIZE=800
CHUNK_OVERLAP=50
MEMORY_KEY=chat_history

# 钉钉配置
DINGDING_ID=your_dingding_appkey         # 钉钉机器人 appkey
DINGDING_SECRET=your_dingding_secret     # 钉钉机器人 appsecret
DINGDING_UNION_ID=your_dingding_unionid  # 钉钉 unionId
```

## 🔧 使用指南

### 1. 启动服务

#### 1.1 启动 Redis 服务
```bash
# MacOS
brew services start redis-stack

# Ubuntu/Debian
sudo systemctl start redis-stack-server

# Windows
# 通过安装程序启动 Redis 服务
```

#### 1.2 启动小浪助手
```bash
# 确保虚拟环境已激活（命令行前缀应显示虚拟环境名称）
# 运行主程序
poetry run python -m src.DingWebHook
```

### 2. 钉钉配置

1. 登录钉钉开发者后台
2. 创建自定义机器人应用
3. 获取并配置以下信息：
   - AppKey (DINGDING_ID)
   - AppSecret (DINGDING_SECRET)
   - UnionId (DINGDING_UNION_ID)
4. 配置机器人回调地址（直接设置为DingStream模式）
5. 在需要使用的群组中添加机器人

### 3. 基本使用

- **知识库查询**：直接向机器人提问，它会从知识库中检索相关信息
- **日程管理**：使用自然语言创建、查询或修改日程
- **待办事项**：通过对话方式管理待办任务
- **实时搜索**：询问实时信息，机器人会通过搜索引擎获取答案

### 4. 常见问题处理

- **Redis 连接失败**：检查 Redis 服务是否正常运行
- **知识库添加**: 入口在 localhost:8000/docs中，目前只支持批量添加url


## 📈 项目亮点

- **教学导向设计**：项目结构清晰，代码注释完善，适合学习和二次开发
- **实际应用场景**：与钉钉深度集成，展示了 AI 在企业协作中的实际应用
- **情感计算集成**：创新性地引入情绪识别，实现更智能的人机交互
- **自动化工作流**：通过自然语言处理，简化日常工作流程

## ⚠️ 重要提示

随着 AI 技术的快速发展，掌握 AI Agents 开发已成为开发者的核心竞争力。建议开发者及早开始 AI 相关技能的学习和实践。如需系统化学习 AI Agents 开发，推荐访问 [1goto.ai](https://1goto.ai) 获取更多学习资源。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。在提交 PR 之前，请确保：

1. 更新已经经过测试
2. 更新相关文档
3. 遵循项目代码规范

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🔗 相关链接

- [项目仓库](https://github.com/neilzhangpro)
- [AI 开发学习资源](https://1goto.ai)
- [问题反馈](https://github.com/neilzhangpro/issues)

## 📢 免责声明

本项目仅用于教育目的。在将 AI 应用于实际生产环境时，请确保符合相关法律法规和伦理准则。随着 AI 技术的发展，开发者有责任确保 AI 的安全和负责任使用。