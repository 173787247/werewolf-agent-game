"""
游戏核心逻辑
实现夜晚行动、发言、投票等核心游戏机制
"""

from typing import Dict, List, Optional
import random
from ..agents.player_agent import PlayerAgent
from ..agents.role_templates import Role


class GameLogic:
    """游戏核心逻辑"""
    
    @staticmethod
    def assign_roles(players: List[str], num_werewolves: int = 2) -> Dict[str, str]:
        """
        随机分配角色
        
        Args:
            players: 玩家列表
            num_werewolves: 狼人数量
            
        Returns:
            角色分配字典 {player: role}
        """
        roles = {}
        werewolves = random.sample(players, num_werewolves)
        
        for player in players:
            if player in werewolves:
                roles[player] = "werewolf"
            else:
                roles[player] = "villager"
        
        return roles
    
    @staticmethod
    def process_night_actions(
        werewolf_agents: List[PlayerAgent],
        game_state: Dict
    ) -> Optional[str]:
        """
        处理夜晚行动
        
        Args:
            werewolf_agents: 狼人 Agent 列表
            game_state: 游戏状态
            
        Returns:
            被杀死的玩家名称，如果无则返回 None
        """
        if not werewolf_agents:
            return None
        
        # 收集所有狼人的目标
        targets = []
        for agent in werewolf_agents:
            action = agent.night_action(game_state)
            target = action.get("target")
            if target:
                targets.append(target)
        
        # 如果所有狼人选择同一目标，则杀死该玩家
        if targets:
            # 统计投票
            target_counts = {}
            for target in targets:
                target_counts[target] = target_counts.get(target, 0) + 1
            
            # 选择得票最多的目标
            if target_counts:
                killed = max(target_counts.items(), key=lambda x: x[1])[0]
                return killed
        
        return None
    
    @staticmethod
    def process_voting(
        agents: Dict[str, PlayerAgent],
        game_state: Dict
    ) -> tuple[Optional[str], Dict[str, int]]:
        """
        处理投票环节
        
        Args:
            agents: Agent 字典 {player_name: agent}
            game_state: 游戏状态
            
        Returns:
            (被处决的玩家, 投票统计)
        """
        alive_players = game_state.get("alive_players", [])
        votes = {}
        
        # 收集所有玩家的投票
        for player in alive_players:
            if player in agents:
                agent = agents[player]
                vote_result = agent.vote(game_state)
                vote_target = vote_result.get("vote")
                if vote_target and vote_target in alive_players:
                    votes[player] = vote_target
        
        # 统计投票
        vote_counts: Dict[str, int] = {}
        for voter, target in votes.items():
            vote_counts[target] = vote_counts.get(target, 0) + 1
        
        if not vote_counts:
            return None, {}
        
        # 找出得票最多的玩家
        max_votes = max(vote_counts.values())
        candidates = [p for p, v in vote_counts.items() if v == max_votes]
        
        # 如果平票，随机选择（或根据规则处理）
        if len(candidates) > 1:
            executed = random.choice(candidates)
        else:
            executed = candidates[0]
        
        return executed, vote_counts
    
    @staticmethod
    def check_win_condition(game_state: Dict) -> tuple[bool, str, str]:
        """
        检查胜利条件
        
        Args:
            game_state: 游戏状态
            
        Returns:
            (游戏是否结束, 获胜方, 原因)
        """
        alive_players = game_state.get("alive_players", [])
        player_roles = game_state.get("player_roles", {})
        
        # 统计存活角色
        alive_werewolves = sum(
            1 for p in alive_players
            if player_roles.get(p) == "werewolf"
        )
        alive_villagers = sum(
            1 for p in alive_players
            if player_roles.get(p) == "villager"
        )
        
        # 检查胜利条件
        if alive_werewolves == 0:
            return True, "村民", "所有狼人已被处决"
        elif alive_werewolves >= alive_villagers:
            return True, "狼人", "狼人数量大于等于村民数量"
        elif len(alive_players) <= 2:
            if alive_werewolves > 0:
                return True, "狼人", "存活玩家过少，狼人获胜"
            else:
                return True, "村民", "存活玩家过少，但无狼人，村民获胜"
        
        return False, "", ""

