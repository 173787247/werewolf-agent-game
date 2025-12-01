"""
玩家 Agent 实现
"""

import json
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks import get_openai_callback

from .role_templates import Role, Personality, RoleTemplate
from ..utils.cost_tracker import CostTracker


class PlayerAgent:
    """玩家 Agent"""
    
    def __init__(
        self,
        name: str,
        role: Role,
        personality: Personality,
        llm: Optional[ChatOpenAI] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cost_tracker: Optional[CostTracker] = None
    ):
        """
        初始化玩家 Agent
        
        Args:
            name: 玩家名称
            role: 角色类型
            personality: 性格类型
            llm: LLM 实例（可选）
            api_key: API Key（如果未提供 llm）
            base_url: API Base URL（用于 DeepSeek 等）
            cost_tracker: 成本追踪器
        """
        self.name = name
        self.role = role
        self.personality = personality
        self.cost_tracker = cost_tracker or CostTracker()
        
        # 初始化 LLM
        if llm is None:
            if base_url:
                self.llm = ChatOpenAI(
                    model="deepseek-chat",
                    api_key=api_key,
                    base_url=base_url,
                    temperature=0.7
                )
            else:
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    api_key=api_key,
                    temperature=0.7
                )
        else:
            self.llm = llm
        
        # 获取角色提示词
        self.system_prompt = RoleTemplate.get_role_prompt(role, personality, name)
        
        # 记忆存储
        self.memory: List[Dict] = []
        self.thoughts: List[Dict] = []
    
    def add_memory(self, event: Dict):
        """添加记忆"""
        self.memory.append(event)
    
    def get_memory_summary(self) -> str:
        """获取记忆摘要"""
        if not self.memory:
            return "暂无记忆"
        
        summary = "历史记忆：\n"
        for i, mem in enumerate(self.memory[-10:], 1):  # 最近10条记忆
            summary += f"{i}. {mem.get('content', '')}\n"
        
        return summary
    
    def night_action(self, game_state: Dict) -> Dict[str, Any]:
        """
        夜晚行动（仅狼人）
        
        Args:
            game_state: 当前游戏状态
            
        Returns:
            行动结果
        """
        if self.role != Role.WEREWOLF:
            return {"action": "sleep", "target": None}
        
        prompt = RoleTemplate.get_night_action_prompt(self.role, game_state)
        
        # 记录思考过程
        thought = {
            "phase": "night_action",
            "player": self.name,
            "thought": f"作为{self.role.value}，我需要选择夜晚的目标"
        }
        self.thoughts.append(thought)
        
        # 调用 LLM
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        with get_openai_callback() as cb:
            response = self.llm.invoke(messages)
            
            # 记录成本
            if self.cost_tracker:
                self.cost_tracker.record_call(
                    model=self.llm.model_name,
                    tokens=cb.total_tokens,
                    prompt_tokens=cb.prompt_tokens,
                    completion_tokens=cb.completion_tokens
                )
        
        # 解析响应
        try:
            content = response.content
            # 尝试提取 JSON
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                action_result = json.loads(json_str)
            else:
                # 如果无法解析 JSON，使用默认值
                action_result = {"target": None, "reasoning": content}
        except Exception as e:
            action_result = {"target": None, "reasoning": f"解析错误: {str(e)}"}
        
        # 记录观察
        observation = {
            "phase": "night_action",
            "player": self.name,
            "action": "kill",
            "target": action_result.get("target"),
            "reasoning": action_result.get("reasoning", "")
        }
        self.thoughts.append(observation)
        
        return {
            "action": "kill",
            "target": action_result.get("target"),
            "reasoning": action_result.get("reasoning", ""),
            "thought": thought,
            "observation": observation
        }
    
    def discuss(self, game_state: Dict, rag_context: Optional[str] = None) -> Dict[str, Any]:
        """
        发言环节
        
        Args:
            game_state: 当前游戏状态
            rag_context: RAG 检索到的相关历史发言
            
        Returns:
            发言结果
        """
        prompt = RoleTemplate.get_discussion_prompt(self.role, game_state, rag_context or "")
        
        # 添加记忆上下文
        memory_summary = self.get_memory_summary()
        if memory_summary:
            prompt = f"{memory_summary}\n\n{prompt}"
        
        # 记录思考过程
        thought = {
            "phase": "discussion",
            "player": self.name,
            "thought": f"分析当前局势，准备发言"
        }
        self.thoughts.append(thought)
        
        # 调用 LLM
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        with get_openai_callback() as cb:
            response = self.llm.invoke(messages)
            
            # 记录成本
            if self.cost_tracker:
                self.cost_tracker.record_call(
                    model=self.llm.model_name,
                    tokens=cb.total_tokens,
                    prompt_tokens=cb.prompt_tokens,
                    completion_tokens=cb.completion_tokens
                )
        
        # 解析响应
        try:
            content = response.content
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                speech_result = json.loads(json_str)
            else:
                speech_result = {
                    "speech": content,
                    "suspicion": None,
                    "reasoning": ""
                }
        except Exception as e:
            speech_result = {
                "speech": content,
                "suspicion": None,
                "reasoning": f"解析错误: {str(e)}"
            }
        
        # 记录观察
        observation = {
            "phase": "discussion",
            "player": self.name,
            "speech": speech_result.get("speech", ""),
            "suspicion": speech_result.get("suspicion"),
            "reasoning": speech_result.get("reasoning", "")
        }
        self.thoughts.append(observation)
        
        # 添加到记忆
        self.add_memory({
            "type": "speech",
            "content": f"我发言：{speech_result.get('speech', '')}",
            "round": game_state.get("round", 0)
        })
        
        return {
            "speech": speech_result.get("speech", ""),
            "suspicion": speech_result.get("suspicion"),
            "reasoning": speech_result.get("reasoning", ""),
            "thought": thought,
            "observation": observation
        }
    
    def vote(self, game_state: Dict) -> Dict[str, Any]:
        """
        投票环节
        
        Args:
            game_state: 当前游戏状态
            
        Returns:
            投票结果
        """
        prompt = RoleTemplate.get_voting_prompt(self.role, game_state)
        
        # 添加记忆上下文
        memory_summary = self.get_memory_summary()
        if memory_summary:
            prompt = f"{memory_summary}\n\n{prompt}"
        
        # 记录思考过程
        thought = {
            "phase": "voting",
            "player": self.name,
            "thought": f"分析发言，决定投票目标"
        }
        self.thoughts.append(thought)
        
        # 调用 LLM
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        with get_openai_callback() as cb:
            response = self.llm.invoke(messages)
            
            # 记录成本
            if self.cost_tracker:
                self.cost_tracker.record_call(
                    model=self.llm.model_name,
                    tokens=cb.total_tokens,
                    prompt_tokens=cb.prompt_tokens,
                    completion_tokens=cb.completion_tokens
                )
        
        # 解析响应
        try:
            content = response.content
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                vote_result = json.loads(json_str)
            else:
                vote_result = {"vote": None, "reasoning": content}
        except Exception as e:
            vote_result = {"vote": None, "reasoning": f"解析错误: {str(e)}"}
        
        # 记录观察
        observation = {
            "phase": "voting",
            "player": self.name,
            "vote": vote_result.get("vote"),
            "reasoning": vote_result.get("reasoning", "")
        }
        self.thoughts.append(observation)
        
        return {
            "vote": vote_result.get("vote"),
            "reasoning": vote_result.get("reasoning", ""),
            "thought": thought,
            "observation": observation
        }
    
    def get_thoughts(self) -> List[Dict]:
        """获取思考链"""
        return self.thoughts
    
    def reset_thoughts(self):
        """重置思考链（新一局游戏）"""
        self.thoughts = []

