"""
游戏日志记录器
输出每轮各 Agent 的思考链（Thought）、动作（Action）、观察（Observation）
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os


class GameLogger:
    """游戏日志记录器"""
    
    def __init__(self, output_dir: str = "./logs"):
        """
        初始化日志记录器
        
        Args:
            output_dir: 日志输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.logs: List[Dict] = []
    
    def log_round(
        self,
        round_num: int,
        phase: str,
        player_thoughts: Dict[str, List[Dict]],
        game_state: Dict
    ):
        """
        记录一轮的完整信息
        
        Args:
            round_num: 轮次
            phase: 阶段
            player_thoughts: 各玩家的思考链 {player: [thoughts]}
            game_state: 游戏状态
        """
        log_entry = {
            "round": round_num,
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "game_state": game_state,
            "player_thoughts": player_thoughts
        }
        self.logs.append(log_entry)
    
    def export_json(self, filename: Optional[str] = None) -> str:
        """
        导出为 JSON 格式
        
        Args:
            filename: 文件名（可选）
            
        Returns:
            文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_log_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def export_html(self, filename: Optional[str] = None) -> str:
        """
        导出为 HTML 格式（可视化展示）
        
        Args:
            filename: 文件名（可选）
            
        Returns:
            文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_log_{timestamp}.html"
        
        filepath = os.path.join(self.output_dir, filename)
        
        html_content = self._generate_html()
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_html(self) -> str:
        """生成 HTML 内容"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>狼人杀游戏日志</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .round {
            background-color: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .round-header {
            font-size: 20px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ddd;
        }
        .phase {
            margin: 15px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 4px solid #4CAF50;
            border-radius: 4px;
        }
        .player-section {
            margin: 10px 0;
            padding: 10px;
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .player-name {
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 5px;
        }
        .thought, .action, .observation {
            margin: 5px 0;
            padding: 8px;
            border-radius: 4px;
        }
        .thought {
            background-color: #E3F2FD;
            border-left: 3px solid #2196F3;
        }
        .action {
            background-color: #FFF3E0;
            border-left: 3px solid #FF9800;
        }
        .observation {
            background-color: #E8F5E9;
            border-left: 3px solid #4CAF50;
        }
        .label {
            font-weight: bold;
            color: #666;
            margin-right: 5px;
        }
    </style>
</head>
<body>
    <h1>🐺 狼人杀游戏执行追踪日志</h1>
"""
        
        for log in self.logs:
            round_num = log.get("round", 0)
            phase = log.get("phase", "")
            player_thoughts = log.get("player_thoughts", {})
            
            html += f"""
    <div class="round">
        <div class="round-header">第 {round_num} 轮 - {phase}</div>
"""
            
            for player, thoughts in player_thoughts.items():
                html += f"""
        <div class="player-section">
            <div class="player-name">👤 {player}</div>
"""
                
                for thought_data in thoughts:
                    thought_type = thought_data.get("phase", "unknown")
                    thought_content = thought_data.get("thought", "")
                    action = thought_data.get("action", "")
                    observation = thought_data.get("observation", "")
                    
                    if thought_content:
                        html += f"""
            <div class="thought">
                <span class="label">思考 (Thought):</span>{thought_content}
            </div>
"""
                    
                    if action:
                        html += f"""
            <div class="action">
                <span class="label">动作 (Action):</span>{action}
            </div>
"""
                    
                    if observation:
                        html += f"""
            <div class="observation">
                <span class="label">观察 (Observation):</span>{observation}
            </div>
"""
                
                html += """
        </div>
"""
            
            html += """
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def get_logs(self) -> List[Dict]:
        """获取所有日志"""
        return self.logs
    
    def clear(self):
        """清空日志"""
        self.logs = []

