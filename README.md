# 基于智能体协作的狼人杀游戏系统

## 项目简介

本项目使用 LangChain + LangGraph 框架实现一个可运行、可观测的狼人杀游戏系统，探索 AI 在复杂社交决策场景中的表现。

## 技术架构

- **框架**: LangChain + LangGraph
- **LLM**: DeepSeek API / OpenAI API
- **向量数据库**: Milvus (可选) / FAISS (本地)
- **可视化**: Streamlit
- **记忆管理**: 向量数据库 + 长期记忆存储

## 核心功能

1. **Agent 角色建模**: 定义不同角色 Prompt 模板，注入角色性格
2. **游戏流程控制**: 主持人 Agent 协调阶段流转
3. **记忆管理**: 跨轮次记忆存储，语义记忆召回
4. **RAG 增强推理**: 检索历史发言记录进行反驳或佐证
5. **可视化执行追踪**: 输出每轮各 Agent 的思考链、动作、观察
6. **成本与复杂度分析**: 统计 token 数、响应延迟、GPU 资源预估

## 项目结构

```
werewolf-agent-game/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   └── game_config.yaml
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── player_agent.py      # 玩家 Agent
│   │   ├── moderator_agent.py   # 主持人 Agent
│   │   └── role_templates.py    # 角色 Prompt 模板
│   ├── game/
│   │   ├── __init__.py
│   │   ├── game_state.py        # 游戏状态管理
│   │   ├── game_flow.py         # 游戏流程控制
│   │   └── game_logic.py        # 游戏核心逻辑
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── memory_manager.py    # 记忆管理器
│   │   └── vector_store.py      # 向量数据库
│   ├── rag/
│   │   ├── __init__.py
│   │   └── rag_engine.py        # RAG 增强推理引擎
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── logger.py            # 日志记录器
│   │   └── visualizer.py        # 可视化工具
│   └── utils/
│       ├── __init__.py
│       ├── cost_tracker.py      # 成本追踪
│       └── helpers.py           # 辅助函数
├── app/
│   └── streamlit_app.py         # Streamlit 可视化界面
├── logs/                        # 游戏日志
├── data/                        # 数据文件
└── tests/                       # 测试文件
```

## 安装与运行

### 1. 安装依赖

```bash
cd werewolf-agent-game
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件并填入你的 API Key：

```bash
# 方式1：使用 DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com/v1

# 方式2：使用 OpenAI API
OPENAI_API_KEY=your_openai_api_key
```

### 3. 运行游戏

#### 方式1：使用示例脚本（推荐）
```bash
python run_game.py
```

#### 方式2：直接运行模块
```bash
python -m src.game.game_flow
```

#### 方式3：Streamlit 可视化界面（推荐用于调试）
```bash
streamlit run app/streamlit_app.py
```

### 4. 查看日志

游戏运行后，日志会保存在 `./logs/` 目录：
- `game_*.json` - 完整游戏数据（JSON格式）
- `game_*.txt` - 格式化日志（文本格式）

## 游戏规则

- **玩家数量**: 5 名（3 村民 + 2 狼人）
- **游戏流程**:
  1. 夜晚行动（狼人选择目标）
  2. 天亮公布死亡
  3. 发言环节
  4. 投票处决
  5. 重复直到游戏结束

## 设计文档

详见 `docs/DESIGN.md`

## 许可证

MIT License

