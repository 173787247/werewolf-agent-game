"""
运行狼人杀游戏的示例脚本
"""

import os
from dotenv import load_dotenv
from src.game.game_flow import GameFlow

# 加载环境变量
load_dotenv()


def main():
    """主函数"""
    # 玩家列表
    players = ["Alice", "Bob", "Charlie", "David", "Eve"]
    
    # 创建游戏
    game = GameFlow(
        players=players,
        use_rag=True,      # 启用 RAG 增强推理
        use_memory=True    # 启用记忆管理
    )
    
    # 运行游戏
    result = game.run(max_rounds=10, save_log=True)
    
    # 打印结果
    print("\n" + "="*50)
    print("游戏结果")
    print("="*50)
    print(f"获胜方: {result['winner']}")
    print(f"原因: {result['reason']}")
    print(f"总轮数: {result['rounds']}")
    print("\n成本统计:")
    cost_summary = result['cost_summary']
    print(f"  总调用次数: {cost_summary.get('total_calls', 0)}")
    print(f"  总 Token 数: {cost_summary.get('total_tokens', 0):,}")
    print(f"  平均延迟: {cost_summary.get('average_latency', 0):.2f}s")
    print("="*50)


if __name__ == "__main__":
    main()

