"""
游戏可视化工具
"""

from typing import Dict, List, Any
import json


class GameVisualizer:
    """游戏可视化工具"""
    
    @staticmethod
    def format_thought_chain(player_thoughts: Dict[str, List[Dict]]) -> str:
        """
        格式化思考链
        
        Args:
            player_thoughts: 玩家思考链 {player: [thoughts]}
            
        Returns:
            格式化的文本
        """
        output = []
        
        for player, thoughts in player_thoughts.items():
            output.append(f"\n{'='*50}")
            output.append(f"玩家: {player}")
            output.append(f"{'='*50}")
            
            for i, thought_data in enumerate(thoughts, 1):
                output.append(f"\n[步骤 {i}]")
                
                if "thought" in thought_data:
                    output.append(f"思考 (Thought): {thought_data['thought']}")
                
                if "action" in thought_data:
                    output.append(f"动作 (Action): {thought_data['action']}")
                
                if "observation" in thought_data:
                    output.append(f"观察 (Observation): {thought_data['observation']}")
        
        return "\n".join(output)
    
    @staticmethod
    def get_game_timeline(game_history: List[Dict]) -> List[Dict]:
        """
        获取游戏时间线
        
        Args:
            game_history: 游戏历史记录
            
        Returns:
            时间线数据
        """
        timeline = []
        
        for entry in game_history:
            timeline.append({
                "round": entry.get("round", 0),
                "phase": entry.get("phase", ""),
                "player": entry.get("player", ""),
                "data": entry.get("data", {})
            })
        
        return timeline
    
    @staticmethod
    def get_player_statistics(game_history: List[Dict], player_roles: Dict[str, str]) -> Dict[str, Dict]:
        """
        获取玩家统计信息
        
        Args:
            game_history: 游戏历史记录
            player_roles: 玩家角色映射
            
        Returns:
            玩家统计 {player: stats}
        """
        stats = {}
        
        for player, role in player_roles.items():
            stats[player] = {
                "role": role,
                "speeches": 0,
                "votes": 0,
                "suspicions": []
            }
        
        for entry in game_history:
            player = entry.get("player", "")
            phase = entry.get("phase", "")
            data = entry.get("data", {})
            
            if player in stats:
                if phase == "discussion":
                    stats[player]["speeches"] += 1
                    if "suspicion" in data:
                        stats[player]["suspicions"].append(data["suspicion"])
                
                elif phase == "voting":
                    if "vote" in data:
                        stats[player]["votes"] += 1
        
        return stats

