# 快速开始指南

## 1. 环境准备

### 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 配置 API Key

创建 `.env` 文件：

```bash
# 使用 DeepSeek API（推荐，价格更便宜）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com/v1

# 或使用 OpenAI API
# OPENAI_API_KEY=your_openai_api_key_here
```

## 2. 快速运行

### 方式1：命令行运行（最简单）

```bash
python run_game.py
```

### 方式2：Streamlit 可视化界面（推荐）

```bash
streamlit run app/streamlit_app.py
```

然后在浏览器中打开显示的地址（通常是 http://localhost:8501）

## 3. 查看结果

游戏运行后，会在 `./logs/` 目录生成日志文件：

- `game_*.json` - 完整游戏数据
- `game_*.txt` - 格式化日志
- `game_log_*.html` - 可视化日志（如果使用 GameLogger）

## 4. 自定义配置

### 修改玩家列表

编辑 `run_game.py`：

```python
players = ["玩家1", "玩家2", "玩家3", "玩家4", "玩家5"]
```

### 修改游戏设置

```python
game = GameFlow(
    players=players,
    use_rag=True,      # 是否启用 RAG
    use_memory=True    # 是否启用记忆管理
)

result = game.run(
    max_rounds=10,     # 最大轮数
    save_log=True      # 是否保存日志
)
```

## 5. 常见问题

### Q: API 调用失败？

A: 检查 `.env` 文件中的 API Key 是否正确，以及网络连接是否正常。

### Q: 向量数据库初始化失败？

A: 确保已安装 `faiss-cpu`：
```bash
pip install faiss-cpu
```

### Q: 游戏运行很慢？

A: 这是正常的，因为每个 Agent 都需要调用 LLM API。可以：
- 使用更快的 API（如 DeepSeek）
- 减少最大轮数
- 使用更小的模型

### Q: 如何查看详细的思考过程？

A: 使用 Streamlit 界面，在"思考链追踪"标签页中查看。

## 6. 下一步

- 阅读 `docs/DESIGN.md` 了解系统架构
- 查看 `src/` 目录下的源代码
- 尝试修改角色 Prompt 模板，观察游戏行为变化
- 调整 RAG 检索参数，优化推理效果

## 7. 示例输出

运行成功后，你会看到类似这样的输出：

```
==================================================
游戏开始！
==================================================

玩家列表: Alice, Bob, Charlie, David, Eve
角色分配: {'Alice': 'werewolf', 'Bob': 'villager', ...}

==================================================

🌙 第 1 轮夜晚开始。所有玩家请闭眼。

☀️ 天亮了！昨晚死亡的玩家是：Charlie。

🗣️ 现在开始第 1 轮发言环节。请玩家按顺序发言：Alice, Bob, David, Eve

[Alice] 我认为 Bob 很可疑，因为...

...

🎮 游戏结束！村民 获胜！原因：所有狼人已被处决
```

