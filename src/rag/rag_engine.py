"""
RAG 增强推理引擎
在发言阶段，Agent 可检索历史发言记录进行反驳或佐证
"""

from typing import List, Dict, Optional
from ..memory.memory_manager import MemoryManager


class RAGEngine:
    """RAG 增强推理引擎"""
    
    def __init__(self, memory_manager: MemoryManager):
        """
        初始化 RAG 引擎
        
        Args:
            memory_manager: 记忆管理器实例
        """
        self.memory_manager = memory_manager
    
    def retrieve_relevant_speeches(
        self,
        query: str,
        current_player: str,
        current_round: int,
        top_k: int = 5
    ) -> str:
        """
        检索相关的历史发言
        
        Args:
            query: 查询文本（当前发言的上下文）
            current_player: 当前玩家
            current_round: 当前轮次
            top_k: 返回前 K 条
            
        Returns:
            格式化的相关发言上下文
        """
        # 构建查询
        search_query = f"{query} 历史发言 怀疑 证据"
        
        # 检索语义记忆
        relevant_memories = self.memory_manager.retrieve_semantic_memory(
            search_query,
            top_k=top_k
        )
        
        # 过滤掉当前玩家的发言和当前轮次的发言
        filtered_memories = [
            m for m in relevant_memories
            if m.get("metadata", {}).get("player") != current_player
            and m.get("metadata", {}).get("round", 0) < current_round
        ]
        
        if not filtered_memories:
            return "暂无相关历史发言。"
        
        # 格式化输出
        context = "相关历史发言：\n"
        for i, memory in enumerate(filtered_memories[:top_k], 1):
            metadata = memory.get("metadata", {})
            player = metadata.get("player", "未知")
            round_num = metadata.get("round", 0)
            text = memory.get("text", "")
            similarity = memory.get("similarity", 0)
            
            context += f"{i}. [第{round_num}轮] {player}: {text} (相似度: {similarity:.2f})\n"
        
        return context
    
    def get_contradiction_evidence(
        self,
        player_name: str,
        current_round: int
    ) -> str:
        """
        获取特定玩家的矛盾证据
        
        Args:
            player_name: 玩家名称
            current_round: 当前轮次
            
        Returns:
            矛盾证据文本
        """
        # 获取该玩家的所有记忆
        player_memories = self.memory_manager.get_player_memory(player_name, top_k=20)
        
        if len(player_memories) < 2:
            return f"{player_name} 的历史记录较少，暂无明显矛盾。"
        
        # 查找可能的矛盾（简单实现：比较不同轮次的发言）
        contradictions = []
        for i, mem1 in enumerate(player_memories):
            for mem2 in player_memories[i+1:]:
                if mem1.get("type") == "speech" and mem2.get("type") == "speech":
                    # 这里可以添加更复杂的矛盾检测逻辑
                    # 目前只是简单展示不同轮次的发言
                    contradictions.append({
                        "round1": mem1.get("round", 0),
                        "content1": mem1.get("content", ""),
                        "round2": mem2.get("round", 0),
                        "content2": mem2.get("content", "")
                    })
        
        if not contradictions:
            return f"{player_name} 的发言逻辑一致。"
        
        # 格式化输出
        evidence = f"{player_name} 的历史发言记录：\n"
        for i, cont in enumerate(contradictions[:3], 1):  # 最多显示3条
            evidence += f"{i}. 第{cont['round1']}轮: {cont['content1'][:50]}...\n"
            evidence += f"   第{cont['round2']}轮: {cont['content2'][:50]}...\n"
        
        return evidence
    
    def get_supporting_evidence(
        self,
        suspicion: str,
        current_round: int
    ) -> str:
        """
        获取支持某个怀疑的证据
        
        Args:
            suspicion: 怀疑内容
            current_round: 当前轮次
            
        Returns:
            支持证据文本
        """
        # 检索相关记忆
        relevant_memories = self.memory_manager.retrieve_semantic_memory(
            suspicion,
            top_k=5
        )
        
        if not relevant_memories:
            return "暂无相关证据支持此怀疑。"
        
        evidence = "支持证据：\n"
        for i, memory in enumerate(relevant_memories, 1):
            metadata = memory.get("metadata", {})
            player = metadata.get("player", "未知")
            round_num = metadata.get("round", 0)
            text = memory.get("text", "")
            
            evidence += f"{i}. [第{round_num}轮] {player}: {text}\n"
        
        return evidence

