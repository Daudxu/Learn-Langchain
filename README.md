# LangChain 学习笔记目录

LangChain 是一个用于构建与大语言模型（LLMs）相关应用程序的开源框架。它提供了高层次的抽象和工具，帮助开发者更高效地构建、部署和管理基于自然语言处理（NLP）的应用。LangChain 的核心目标是简化与大语言模型的交互，支持多种应用场景，如自动化任务、问答系统、对话代理、文档分析等。

本学习笔记旨在系统性地记录 LangChain 的使用方法、核心模块和最佳实践，帮助开发者快速上手并深入理解其功能。


## 目录

### 第一部分：基础知识
1. [LangChain 简介](./01-introduction/langchain-intro.md)
2. [环境搭建](./01-introduction/environment-setup.md)
3. [核心概念与架构](./01-introduction/core-concepts.md)
4. [模型接入与配置](./01-introduction/model-configuration.md)

### 第二部分：PromptTemplate 提示词工程在 LangChain 中的实践
1. [提示工程基础](./02-prompt-engineering/prompt-basics.md)
2. [字符串模板](./02-prompt-engineering/string-templates.md)
3. [对话模板应用](./02-prompt-engineering/chat-templates.md)
4. [消息占位符应用](./02-prompt-engineering/message-placeholders.md)
5. [组合模板](./02-prompt-engineering/composing-templates.md)
6. [自定义模板](./02-prompt-engineering/custom-templates.md)
7. [Few-Shot 学习技术](./02-prompt-engineering/few-shot.md)
8. [Partial 格式化技术](./02-prompt-engineering/partial-formatting.md)
9. [模板序列化与共享](./02-prompt-engineering/template-serialization.md)

### 第三部分：规范化输出 OutputParsers 的关键技术
1. [输出解析器概述](./03-output-parsers/parsers-overview.md)
2. [结构化输出解析](./03-output-parsers/structured-output.md)
3. [JSON 格式解析器](./03-output-parsers/json-parser.md)
4. [列表与枚举解析器](./03-output-parsers/list-enum-parser.md)
5. [自定义解析器开发](./03-output-parsers/custom-parsers.md)
6. [错误处理与重试机制](./03-output-parsers/error-handling.md)
7. [解析器与模板组合使用](./03-output-parsers/parser-template-combination.md)

### 第四部分：LCEL 组件化开发的新范式
1. [LCEL 简介与基础](./04-lcel/lcel-introduction.md)
2. [Runnable 接口体系](./04-lcel/runnable-interface.md)
3. [链式操作构建](./04-lcel/chain-operations.md)
4. [条件控制与分支](./04-lcel/conditional-branching.md)
5. [并行处理与聚合](./04-lcel/parallel-processing.md)
6. [组件复用与封装](./04-lcel/component-reuse.md)
7. [调试与追踪技术](./04-lcel/debugging-tracing.md)
8. [性能优化策略](./04-lcel/performance-optimization.md)

### 第五部分：高级应用开发
1. [RAG 检索增强生成系统](./05-advanced-applications/rag-systems.md)
2. [对话式智能助手](./05-advanced-applications/conversational-agents.md)
3. [工具使用与代理系统](./05-advanced-applications/tools-agents.md)
4. [知识库构建](./05-advanced-applications/knowledge-base.md)
5. [文档分析与处理](./05-advanced-applications/document-processing.md)
6. [多模态应用](./05-advanced-applications/multimodal-applications.md)
7. [批处理与异步处理](./05-advanced-applications/batch-async-processing.md)

### 第六部分：生产环境部署与最佳实践
1. [系统架构设计](./06-production/system-architecture.md)
2. [性能调优与扩展](./06-production/performance-tuning.md)
3. [监控与可观测性](./06-production/monitoring.md)
4. [安全与隐私考量](./06-production/security-privacy.md)
5. [成本优化策略](./06-production/cost-optimization.md)
6. [CI/CD 与自动化测试](./06-production/ci-cd-testing.md)
7. [与现有系统集成](./06-production/system-integration.md)

### 第七部分：附录
1. [常见问题解答](./07-appendix/faq.md)
2. [学习资源汇总](./07-appendix/resources.md)
3. [版本更新与迁移指南](./07-appendix/version-migration.md)
4. [社区贡献指南](./07-appendix/contribution-guide.md)
5. [示例项目代码库](./07-appendix/example-projects.md)

---

通过本目录，您可以快速定位到感兴趣的章节，逐步学习 LangChain 的功能与应用。每个章节都包含详细的解释、代码示例和最佳实践，帮助您在实际项目中高效应用 LangChain。

