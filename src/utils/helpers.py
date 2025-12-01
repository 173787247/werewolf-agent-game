"""
辅助函数
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


def format_game_log(game_history: List[Dict]) -> str:
    """
    格式化游戏日志为可读文本
    
    Args:
        game_history: 游戏历史记录
        
    Returns:
        格式化的日志文本
    """
    log_lines = []
    
    for entry in game_history:
        round_num = entry.get("round", 0)
        phase = entry.get("phase", "")
        player = entry.get("player", "")
        
        if phase == "night_action":
            data = entry.get("data", {})
            target = data.get("target", "")
            log_lines.append(f"[第{round_num}轮-夜晚] {player} 选择目标: {target}")
        
        elif phase == "day_announce":
            deaths = entry.get("deaths", [])
            if deaths:
                log_lines.append(f"[第{round_num}轮-天亮] 死亡玩家: {', '.join(deaths)}")
            else:
                log_lines.append(f"[第{round_num}轮-天亮] 平安夜，无人死亡")
        
        elif phase == "discussion":
            data = entry.get("data", {})
            speech = data.get("speech", "")
            log_lines.append(f"[第{round_num}轮-发言] {player}: {speech}")
        
        elif phase == "voting":
            votes = entry.get("votes", {})
            vote_counts = entry.get("vote_counts", {})
            log_lines.append(f"[第{round_num}轮-投票] 投票结果: {json.dumps(vote_counts, ensure_ascii=False)}")
        
        elif phase == "execution":
            executed = entry.get("executed", "")
            log_lines.append(f"[第{round_num}轮-处决] 玩家 {executed} 被处决")
    
    return "\n".join(log_lines)


def save_game_log(
    game_history: List[Dict],
    cost_summary: Dict,
    output_dir: str = "./logs",
    filename: Optional[str] = None
):
    """
    保存游戏日志到文件
    
    Args:
        game_history: 游戏历史记录
        cost_summary: 成本统计摘要
        output_dir: 输出目录
        filename: 文件名（可选，默认使用时间戳）
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_{timestamp}.json"
    
    filepath = os.path.join(output_dir, filename)
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "game_history": game_history,
        "cost_summary": cost_summary,
        "formatted_log": format_game_log(game_history)
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"游戏日志已保存到: {filepath}")
    
    # 同时保存格式化的文本日志
    text_filepath = filepath.replace(".json", ".txt")
    with open(text_filepath, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("游戏日志\n")
        f.write("=" * 50 + "\n\n")
        f.write(log_data["formatted_log"])
        f.write("\n\n" + "=" * 50 + "\n")
        f.write("成本统计\n")
        f.write("=" * 50 + "\n\n")
        f.write(json.dumps(cost_summary, ensure_ascii=False, indent=2))
    
    print(f"格式化日志已保存到: {text_filepath}")

