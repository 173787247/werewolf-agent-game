"""
游戏状态管理
"""

from typing import Dict, List, Optional, Any
from copy import deepcopy


class GameState:
    """游戏状态管理器"""
    
    def __init__(self, players: List[str], roles: Dict[str, str]):
        """
        初始化游戏状态
        
        Args:
            players: 玩家列表
            roles: 玩家角色映射 {player_name: role}
        """
        self.players = players
        self.roles = roles
        self.alive_players = players.copy()
        self.round = 0
        self.phase = "night_action"
        
        # 游戏历史
        self.night_actions: List[Dict] = []  # 夜晚行动记录
        self.last_night_deaths: List[str] = []  # 昨晚死亡玩家
        self.discussion_logs: List[Dict] = []  # 发言记录
        self.voting_logs: List[Dict] = []  # 投票记录
        self.execution_history: List[str] = []  # 被处决的玩家
        
        # 完整游戏历史（用于可视化）
        self.full_history: List[Dict] = []
    
    def start_new_round(self):
        """开始新的一轮"""
        self.round += 1
        self.phase = "night_action"
        self.last_night_deaths = []
    
    def set_phase(self, phase: str):
        """设置当前阶段"""
        self.phase = phase
    
    def record_night_action(self, player: str, action: Dict):
        """记录夜晚行动"""
        self.night_actions.append({
            "round": self.round,
            "player": player,
            "action": action
        })
        self.full_history.append({
            "round": self.round,
            "phase": "night_action",
            "player": player,
            "data": action
        })
    
    def record_deaths(self, deaths: List[str]):
        """记录死亡玩家"""
        self.last_night_deaths = deaths
        for death in deaths:
            if death in self.alive_players:
                self.alive_players.remove(death)
        
        self.full_history.append({
            "round": self.round,
            "phase": "day_announce",
            "deaths": deaths
        })
    
    def record_discussion(self, player: str, speech: Dict):
        """记录发言"""
        self.discussion_logs.append({
            "round": self.round,
            "player": player,
            "speech": speech
        })
        self.full_history.append({
            "round": self.round,
            "phase": "discussion",
            "player": player,
            "data": speech
        })
    
    def record_voting(self, votes: Dict[str, str]):
        """记录投票"""
        # 统计投票
        vote_counts: Dict[str, int] = {}
        for voter, target in votes.items():
            if target:
                vote_counts[target] = vote_counts.get(target, 0) + 1
        
        self.voting_logs.append({
            "round": self.round,
            "votes": votes,
            "vote_counts": vote_counts
        })
        self.full_history.append({
            "round": self.round,
            "phase": "voting",
            "votes": votes,
            "vote_counts": vote_counts
        })
        
        return vote_counts
    
    def record_execution(self, executed: str):
        """记录处决"""
        if executed in self.alive_players:
            self.alive_players.remove(executed)
        self.execution_history.append(executed)
        
        self.full_history.append({
            "round": self.round,
            "phase": "execution",
            "executed": executed
        })
    
    def get_state_dict(self) -> Dict[str, Any]:
        """获取状态字典（用于传递给 Agent）"""
        return {
            "round": self.round,
            "phase": self.phase,
            "alive_players": self.alive_players,
            "player_roles": self.roles,
            "last_night_deaths": self.last_night_deaths,
            "discussion_logs": self.discussion_logs[-len(self.alive_players):] if self.discussion_logs else [],
            "execution_history": self.execution_history
        }
    
    def get_full_history(self) -> List[Dict]:
        """获取完整游戏历史"""
        return self.full_history
    
    def copy(self) -> 'GameState':
        """深拷贝游戏状态"""
        return deepcopy(self)

