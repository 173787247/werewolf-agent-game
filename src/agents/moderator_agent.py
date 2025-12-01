"""
主持人 Agent 实现
负责协调游戏流程，确保阶段正确流转
"""

from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI


class ModeratorAgent:
    """主持人 Agent - 协调游戏流程"""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        初始化主持人 Agent
        
        Args:
            llm: LLM 实例（可选，用于智能判断）
        """
        self.llm = llm
        self.game_log: List[Dict] = []
    
    def announce_night(self, round_num: int) -> str:
        """宣布夜晚开始"""
        announcement = f"🌙 第 {round_num} 轮夜晚开始。所有玩家请闭眼。"
        self.log_event("night_start", {"round": round_num, "announcement": announcement})
        return announcement
    
    def announce_day(self, round_num: int, deaths: List[str]) -> str:
        """宣布天亮"""
        if deaths:
            death_list = "、".join(deaths)
            announcement = f"☀️ 天亮了！昨晚死亡的玩家是：{death_list}。"
        else:
            announcement = f"☀️ 天亮了！昨晚是平安夜，没有玩家死亡。"
        
        self.log_event("day_start", {
            "round": round_num,
            "deaths": deaths,
            "announcement": announcement
        })
        return announcement
    
    def announce_discussion(self, round_num: int, alive_players: List[str]) -> str:
        """宣布发言环节开始"""
        announcement = f"🗣️ 现在开始第 {round_num} 轮发言环节。请玩家按顺序发言：{', '.join(alive_players)}"
        self.log_event("discussion_start", {
            "round": round_num,
            "players": alive_players,
            "announcement": announcement
        })
        return announcement
    
    def announce_voting(self, round_num: int, alive_players: List[str]) -> str:
        """宣布投票环节开始"""
        announcement = f"🗳️ 现在开始投票环节。请所有存活玩家投票：{', '.join(alive_players)}"
        self.log_event("voting_start", {
            "round": round_num,
            "players": alive_players,
            "announcement": announcement
        })
        return announcement
    
    def announce_voting_result(self, votes: Dict[str, int], executed: str) -> str:
        """宣布投票结果"""
        vote_details = ", ".join([f"{player}: {count}票" for player, count in votes.items()])
        announcement = f"📊 投票结果：{vote_details}。玩家 {executed} 被处决。"
        self.log_event("voting_result", {
            "votes": votes,
            "executed": executed,
            "announcement": announcement
        })
        return announcement
    
    def announce_game_end(self, winner: str, reason: str) -> str:
        """宣布游戏结束"""
        announcement = f"🎮 游戏结束！{winner} 获胜！原因：{reason}"
        self.log_event("game_end", {
            "winner": winner,
            "reason": reason,
            "announcement": announcement
        })
        return announcement
    
    def check_game_end(self, game_state: Dict) -> tuple[bool, str, str]:
        """
        检查游戏是否结束
        
        Returns:
            (is_end, winner, reason)
        """
        alive_players = game_state.get("alive_players", [])
        player_roles = game_state.get("player_roles", {})
        
        # 统计存活角色
        alive_werewolves = sum(1 for p in alive_players if player_roles.get(p) == "werewolf")
        alive_villagers = sum(1 for p in alive_players if player_roles.get(p) == "villager")
        
        # 检查胜利条件
        if alive_werewolves == 0:
            return True, "村民", "所有狼人已被处决"
        elif alive_werewolves >= alive_villagers:
            return True, "狼人", "狼人数量大于等于村民数量"
        elif len(alive_players) <= 2:
            # 如果只剩2人，且还有狼人，狼人获胜
            if alive_werewolves > 0:
                return True, "狼人", "存活玩家过少，狼人获胜"
            else:
                return True, "村民", "存活玩家过少，但无狼人，村民获胜"
        
        return False, "", ""
    
    def log_event(self, event_type: str, data: Dict):
        """记录事件"""
        self.game_log.append({
            "type": event_type,
            "data": data
        })
    
    def get_game_log(self) -> List[Dict]:
        """获取游戏日志"""
        return self.game_log

