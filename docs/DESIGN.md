# 系统设计文档

## 1. 架构选择

### 1.1 框架选择：LangChain + LangGraph

**选择理由：**
- **流程可控性强**：LangGraph 提供了清晰的状态图定义，可以精确控制游戏流程的每个阶段
- **易于集成 RAG 与记忆模块**：LangChain 生态提供了丰富的工具链，便于集成向量数据库和 RAG 功能
- **状态管理**：LangGraph 的状态管理机制非常适合游戏状态的多阶段流转
- **可扩展性**：易于添加新的游戏阶段和功能

### 1.2 系统架构

```
┌─────────────────────────────────────────┐
│         Streamlit 可视化界面             │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         GameFlow (LangGraph)             │
│  ┌──────────┐  ┌──────────┐            │
│  │ Night    │→ │ Day      │            │
│  │ Action   │  │ Announce │            │
│  └──────────┘  └──────────┘            │
│        │              │                 │
│        ▼              ▼                 │
│  ┌──────────┐  ┌──────────┐            │
│  │Discussion│→ │ Voting   │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌─────────────────┐
│  Player Agents  │  │ Moderator Agent│
└─────────────────┘  └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         RAG Engine                      │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Memory       │→ │ Vector Store │   │
│  │ Manager      │  │ (FAISS)      │   │
│  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
```

## 2. 核心模块设计

### 2.1 Agent 角色建模

**实现方式：**
- 使用 `RoleTemplate` 类定义不同角色的 Prompt 模板
- 支持角色性格注入（激进型、谨慎型、分析型、观察型）
- 每个 Agent 在初始化时获得角色特定的系统提示词

**关键代码：**
```python
class RoleTemplate:
    BASE_ROLE_PROMPTS = {
        Role.WEREWOLF: "...",
        Role.VILLAGER: "..."
    }
    PERSONALITY_TRAITS = {
        Personality.AGGRESSIVE: "...",
        Personality.CAUTIOUS: "...",
        ...
    }
```

### 2.2 游戏流程控制

**实现方式：**
- 使用 LangGraph 构建状态图
- 定义节点：`night_action` → `day_announce` → `discussion` → `voting` → `check_end`
- 使用条件边判断游戏是否继续

**流程：**
1. 夜晚行动：狼人选择目标
2. 天亮公布：主持人宣布死亡
3. 发言环节：所有玩家依次发言
4. 投票环节：所有玩家投票
5. 检查结束：判断游戏是否结束

### 2.3 记忆管理

**实现方式：**
- **情景记忆（Episodic Memory）**：按时间顺序存储所有游戏事件
- **语义记忆（Semantic Memory）**：使用向量数据库（FAISS）存储，支持语义检索

**记忆类型：**
- 发言记录
- 投票记录
- 行动记录
- 死亡记录

**检索机制：**
- 使用向量相似度搜索
- 支持按玩家、轮次、类型过滤

### 2.4 RAG 增强推理

**实现方式：**
- 在发言阶段，Agent 检索相关历史发言
- 使用语义搜索找到与当前讨论相关的历史记录
- 将检索结果作为上下文注入到 Prompt 中

**RAG 应用场景：**
1. **反驳证据**：检索其他玩家的历史发言，找出矛盾
2. **支持证据**：检索支持当前怀疑的历史记录
3. **策略参考**：参考历史游戏中的成功策略

### 2.5 可视化执行追踪

**实现方式：**
- **JSON 日志**：结构化存储所有游戏数据
- **HTML 日志**：可视化展示思考链、动作、观察
- **Streamlit 界面**：实时展示游戏进程

**追踪内容：**
- 每轮各 Agent 的思考链（Thought）
- 动作（Action）
- 观察（Observation）

## 3. 技术实现细节

### 3.1 向量数据库选择

**FAISS（本地）：**
- 优点：无需额外服务，部署简单
- 缺点：数据不持久化（可选：保存到文件）

**Milvus（可选）：**
- 优点：支持分布式，数据持久化
- 缺点：需要额外部署服务

**当前实现：** 默认使用 FAISS，支持切换到 Milvus

### 3.2 LLM 选择

**支持：**
- DeepSeek API
- OpenAI API

**配置方式：**
- 通过环境变量配置 API Key
- 支持自定义 Base URL（用于 DeepSeek）

### 3.3 成本追踪

**追踪指标：**
- 总 Token 数（Prompt + Completion）
- 平均响应延迟
- 各模型使用统计
- GPU 资源估算

**实现：**
- 使用 `langchain.callbacks.get_openai_callback()` 追踪
- 自定义 `CostTracker` 类记录所有调用

## 4. RAG 应用方式

### 4.1 在发言阶段的应用

```python
# 检索相关历史发言
rag_context = rag_engine.retrieve_relevant_speeches(
    query="分析局势，找出可疑玩家",
    current_player=player,
    current_round=round_num
)

# 将检索结果注入 Prompt
speech_result = agent.discuss(game_state, rag_context)
```

### 4.2 矛盾检测

```python
# 获取玩家的矛盾证据
evidence = rag_engine.get_contradiction_evidence(
    player_name="Alice",
    current_round=3
)
```

### 4.3 支持证据检索

```python
# 获取支持某个怀疑的证据
evidence = rag_engine.get_supporting_evidence(
    suspicion="Bob 可能是狼人",
    current_round=3
)
```

## 5. 调试方法

### 5.1 日志查看

- **JSON 日志**：`./logs/game_*.json` - 完整游戏数据
- **文本日志**：`./logs/game_*.txt` - 格式化日志
- **HTML 日志**：`./logs/game_log_*.html` - 可视化日志

### 5.2 思考链追踪

```python
# 获取玩家的思考链
thoughts = agent.get_thoughts()
for thought in thoughts:
    print(f"思考: {thought['thought']}")
    print(f"动作: {thought['action']}")
    print(f"观察: {thought['observation']}")
```

### 5.3 记忆检索测试

```python
# 测试记忆检索
memories = memory_manager.retrieve_semantic_memory(
    query="谁怀疑过 Bob",
    top_k=5
)
```

### 5.4 Streamlit 调试

运行 Streamlit 界面，实时查看：
- 游戏进程
- 思考链
- 成本统计

## 6. 迭代改进建议

### 6.1 基础版本问题

**可能的问题：**
- 狼人暴露太早
- 村民推理能力不足
- 游戏节奏过快或过慢

### 6.2 优化方向

1. **增强角色性格**：更细致的性格定义，影响决策
2. **改进 RAG 检索**：更精准的语义搜索
3. **优化 Prompt**：基于实际游戏结果调整 Prompt
4. **添加策略学习**：从历史游戏中学习策略

## 7. 部署建议

### 7.1 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行游戏
python -m src.game.game_flow

# 或使用 Streamlit
streamlit run app/streamlit_app.py
```

### 7.2 生产环境

- 使用 Milvus 作为向量数据库
- 配置日志轮转
- 添加监控和告警
- 考虑使用 GPU 加速（如果使用本地模型）

## 8. 扩展功能

### 8.1 可能的扩展

- 支持更多角色（预言家、女巫等）
- 支持更多玩家
- 添加游戏回放功能
- 支持多人联机
- 添加 AI 训练功能（强化学习）

## 9. 性能优化

### 9.1 Token 优化

- 压缩 Prompt 长度
- 使用更小的模型（如果效果可接受）
- 批量处理请求

### 9.2 延迟优化

- 并行处理多个 Agent 的请求
- 使用更快的 API
- 缓存常用查询

## 10. 总结

本系统通过 LangChain + LangGraph 实现了完整的狼人杀游戏系统，核心特点：

1. **流程可控**：使用 LangGraph 精确控制游戏流程
2. **RAG 增强**：通过向量检索增强 Agent 推理能力
3. **记忆管理**：实现跨轮次的情景记忆和语义记忆
4. **可视化追踪**：完整的思考链、动作、观察记录
5. **成本分析**：详细的 Token 和延迟统计

该系统展示了 AI Agent 在复杂社交决策场景中的应用潜力。

