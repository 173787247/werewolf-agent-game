"""
记忆管理器
实现跨轮次的记忆存储和语义记忆召回
"""

from typing import List, Dict, Optional
from .vector_store import VectorStore


class MemoryManager:
    """记忆管理器 - 管理情景记忆和语义记忆"""
    
    def __init__(self, vector_store: VectorStore):
        """
        初始化记忆管理器
        
        Args:
            vector_store: 向量存储实例
        """
        self.vector_store = vector_store
        self.episodic_memory: List[Dict] = []  # 情景记忆（按时间顺序）
    
    def add_episodic_memory(self, event: Dict):
        """
        添加情景记忆
        
        Args:
            event: 事件字典，包含 type, player, round, content 等
        """
        self.episodic_memory.append(event)
        
        # 同时添加到向量存储（语义记忆）
        text = self._format_event_text(event)
        metadata = {
            "type": event.get("type", "unknown"),
            "player": event.get("player", ""),
            "round": event.get("round", 0),
            "phase": event.get("phase", "")
        }
        self.vector_store.add_memory(text, metadata)
    
    def _format_event_text(self, event: Dict) -> str:
        """格式化事件为文本"""
        event_type = event.get("type", "unknown")
        player = event.get("player", "")
        content = event.get("content", "")
        round_num = event.get("round", 0)
        
        if event_type == "speech":
            return f"第{round_num}轮，{player}发言：{content}"
        elif event_type == "vote":
            return f"第{round_num}轮，{player}投票给{content}"
        elif event_type == "action":
            return f"第{round_num}轮，{player}执行行动：{content}"
        else:
            return f"第{round_num}轮，{player}：{content}"
    
    def retrieve_semantic_memory(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        检索语义记忆（使用向量搜索）
        
        Args:
            query: 查询文本
            top_k: 返回前 K 条结果
            
        Returns:
            相关记忆列表
        """
        return self.vector_store.search(query, top_k=top_k)
    
    def get_recent_episodic_memory(self, rounds: int = 3) -> List[Dict]:
        """
        获取最近的情景记忆
        
        Args:
            rounds: 最近几轮
            
        Returns:
            最近的事件列表
        """
        if not self.episodic_memory:
            return []
        
        # 获取最近几轮的事件
        recent_rounds = set()
        for event in reversed(self.episodic_memory):
            round_num = event.get("round", 0)
            recent_rounds.add(round_num)
            if len(recent_rounds) >= rounds:
                break
        
        return [e for e in self.episodic_memory if e.get("round", 0) in recent_rounds]
    
    def get_player_memory(self, player: str, top_k: int = 10) -> List[Dict]:
        """
        获取特定玩家的记忆
        
        Args:
            player: 玩家名称
            top_k: 返回前 K 条
            
        Returns:
            该玩家的记忆列表
        """
        player_memories = [e for e in self.episodic_memory if e.get("player") == player]
        return player_memories[-top_k:] if player_memories else []
    
    def get_all_memory(self) -> List[Dict]:
        """获取所有情景记忆"""
        return self.episodic_memory
    
    def clear(self):
        """清空记忆（新一局游戏）"""
        self.episodic_memory = []
        # 注意：向量存储不会被清空，这样可以跨局游戏检索

