"""
游戏流程控制（使用 LangGraph）
主持人 Agent 协调阶段流转，确保顺序正确
"""

import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from ..agents.player_agent import PlayerAgent
from ..agents.moderator_agent import ModeratorAgent
from ..agents.role_templates import Role, Personality
from ..game.game_state import GameState
from ..game.game_logic import GameLogic
from ..memory.memory_manager import MemoryManager
from ..memory.vector_store import VectorStore
from ..rag.rag_engine import RAGEngine
from ..utils.cost_tracker import CostTracker
from ..utils.helpers import save_game_log

# 加载环境变量
load_dotenv()


class GameFlow:
    """游戏流程控制器（使用 LangGraph）"""
    
    def __init__(
        self,
        players: List[str],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        use_rag: bool = True,
        use_memory: bool = True
    ):
        """
        初始化游戏流程
        
        Args:
            players: 玩家名称列表
            api_key: API Key
            base_url: API Base URL（用于 DeepSeek 等）
            use_rag: 是否使用 RAG
            use_memory: 是否使用记忆管理
        """
        self.players = players
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        # 初始化成本追踪
        self.cost_tracker = CostTracker()
        
        # 初始化记忆管理
        if use_memory:
            vector_store = VectorStore(
                store_type="faiss",
                embedding_model="text-embedding-ada-002",
                api_key=self.api_key
            )
            self.memory_manager = MemoryManager(vector_store)
        else:
            self.memory_manager = None
        
        # 初始化 RAG 引擎
        if use_rag and self.memory_manager:
            self.rag_engine = RAGEngine(self.memory_manager)
        else:
            self.rag_engine = None
        
        # 分配角色
        self.roles = GameLogic.assign_roles(players, num_werewolves=2)
        
        # 初始化游戏状态
        self.game_state = GameState(players, self.roles)
        
        # 初始化主持人
        self.moderator = ModeratorAgent()
        
        # 初始化玩家 Agent
        self.agents: Dict[str, PlayerAgent] = {}
        personality_map = {
            "werewolf": [Personality.AGGRESSIVE, Personality.CAUTIOUS],
            "villager": [Personality.ANALYTICAL, Personality.CAUTIOUS, Personality.OBSERVANT]
        }
        
        for i, player in enumerate(players):
            role = Role.WEREWOLF if self.roles[player] == "werewolf" else Role.VILLAGER
            personalities = personality_map[self.roles[player]]
            personality = personalities[i % len(personalities)]
            
            agent = PlayerAgent(
                name=player,
                role=role,
                personality=personality,
                api_key=self.api_key,
                base_url=self.base_url,
                cost_tracker=self.cost_tracker
            )
            self.agents[player] = agent
        
        # 构建 LangGraph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 状态图"""
        workflow = StateGraph(Dict)
        
        # 添加节点
        workflow.add_node("night_action", self._night_action_node)
        workflow.add_node("day_announce", self._day_announce_node)
        workflow.add_node("discussion", self._discussion_node)
        workflow.add_node("voting", self._voting_node)
        workflow.add_node("check_end", self._check_end_node)
        
        # 设置入口
        workflow.set_entry_point("night_action")
        
        # 添加边
        workflow.add_edge("night_action", "day_announce")
        workflow.add_edge("day_announce", "discussion")
        workflow.add_edge("discussion", "voting")
        workflow.add_edge("voting", "check_end")
        
        # 条件边：检查游戏是否结束
        workflow.add_conditional_edges(
            "check_end",
            self._should_continue,
            {
                "continue": "night_action",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _night_action_node(self, state: Dict) -> Dict:
        """夜晚行动节点"""
        self.game_state.start_new_round()
        self.game_state.set_phase("night_action")
        
        announcement = self.moderator.announce_night(self.game_state.round)
        print(f"\n{announcement}")
        
        # 获取狼人 Agent
        werewolf_agents = [
            agent for name, agent in self.agents.items()
            if self.roles[name] == "werewolf" and name in self.game_state.alive_players
        ]
        
        # 处理夜晚行动
        killed = GameLogic.process_night_actions(werewolf_agents, self.game_state.get_state_dict())
        
        if killed:
            # 记录行动
            for agent in werewolf_agents:
                action = agent.night_action(self.game_state.get_state_dict())
                self.game_state.record_night_action(agent.name, action)
            
            state["killed"] = killed
        else:
            state["killed"] = None
        
        return state
    
    def _day_announce_node(self, state: Dict) -> Dict:
        """天亮公布节点"""
        self.game_state.set_phase("day_announce")
        
        killed = state.get("killed")
        deaths = [killed] if killed else []
        
        self.game_state.record_deaths(deaths)
        
        announcement = self.moderator.announce_day(self.game_state.round, deaths)
        print(f"\n{announcement}")
        
        # 记录到记忆
        if self.memory_manager and deaths:
            for death in deaths:
                self.memory_manager.add_episodic_memory({
                    "type": "death",
                    "player": death,
                    "round": self.game_state.round,
                    "phase": "day_announce",
                    "content": f"玩家 {death} 在夜晚被杀死"
                })
        
        return state
    
    def _discussion_node(self, state: Dict) -> Dict:
        """发言环节节点"""
        self.game_state.set_phase("discussion")
        
        announcement = self.moderator.announce_discussion(
            self.game_state.round,
            self.game_state.alive_players
        )
        print(f"\n{announcement}")
        
        # 每个存活玩家发言
        for player in self.game_state.alive_players:
            if player not in self.agents:
                continue
            
            agent = self.agents[player]
            
            # 使用 RAG 检索相关历史发言
            rag_context = None
            if self.rag_engine:
                # 构建查询（基于当前游戏状态）
                query = f"第{self.game_state.round}轮发言，分析局势，找出可疑玩家"
                rag_context = self.rag_engine.retrieve_relevant_speeches(
                    query,
                    player,
                    self.game_state.round
                )
            
            # 玩家发言
            speech_result = agent.discuss(
                self.game_state.get_state_dict(),
                rag_context
            )
            
            self.game_state.record_discussion(player, speech_result)
            
            print(f"\n[{player}] {speech_result.get('speech', '')}")
            
            # 记录到记忆
            if self.memory_manager:
                self.memory_manager.add_episodic_memory({
                    "type": "speech",
                    "player": player,
                    "round": self.game_state.round,
                    "phase": "discussion",
                    "content": speech_result.get("speech", "")
                })
        
        return state
    
    def _voting_node(self, state: Dict) -> Dict:
        """投票环节节点"""
        self.game_state.set_phase("voting")
        
        announcement = self.moderator.announce_voting(
            self.game_state.round,
            self.game_state.alive_players
        )
        print(f"\n{announcement}")
        
        # 收集投票
        votes = {}
        for player in self.game_state.alive_players:
            if player not in self.agents:
                continue
            
            agent = self.agents[player]
            vote_result = agent.vote(self.game_state.get_state_dict())
            vote_target = vote_result.get("vote")
            
            if vote_target:
                votes[player] = vote_target
                print(f"[{player}] 投票给: {vote_target}")
        
        # 处理投票
        self.game_state.record_voting(votes)
        executed, vote_counts = GameLogic.process_voting(
            self.agents,
            self.game_state.get_state_dict()
        )
        
        if executed:
            self.game_state.record_execution(executed)
            announcement = self.moderator.announce_voting_result(vote_counts, executed)
            print(f"\n{announcement}")
            
            # 记录到记忆
            if self.memory_manager:
                self.memory_manager.add_episodic_memory({
                    "type": "execution",
                    "player": executed,
                    "round": self.game_state.round,
                    "phase": "voting",
                    "content": f"玩家 {executed} 被投票处决"
                })
        
        state["executed"] = executed
        return state
    
    def _check_end_node(self, state: Dict) -> Dict:
        """检查游戏结束节点"""
        is_end, winner, reason = GameLogic.check_win_condition(
            self.game_state.get_state_dict()
        )
        
        state["is_end"] = is_end
        state["winner"] = winner
        state["reason"] = reason
        
        if is_end:
            announcement = self.moderator.announce_game_end(winner, reason)
            print(f"\n{announcement}")
        
        return state
    
    def _should_continue(self, state: Dict) -> str:
        """判断是否继续游戏"""
        if state.get("is_end", False):
            return "end"
        return "continue"
    
    def run(self, max_rounds: int = 10, save_log: bool = True) -> Dict:
        """
        运行游戏
        
        Args:
            max_rounds: 最大轮数
            save_log: 是否保存日志
            
        Returns:
            游戏结果
        """
        print("=" * 50)
        print("游戏开始！")
        print("=" * 50)
        print(f"\n玩家列表: {', '.join(self.players)}")
        print(f"角色分配: {self.roles}")
        print("\n" + "=" * 50 + "\n")
        
        # 运行游戏
        state = {}
        round_count = 0
        
        try:
            while round_count < max_rounds:
                state = self.graph.invoke(state)
                round_count += 1
                
                if state.get("is_end", False):
                    break
        except Exception as e:
            print(f"\n游戏运行出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 获取结果
        winner = state.get("winner", "未知")
        reason = state.get("reason", "")
        
        print("\n" + "=" * 50)
        print("游戏结束！")
        print("=" * 50)
        
        # 保存日志
        if save_log:
            cost_summary = self.cost_tracker.get_summary()
            save_game_log(
                self.game_state.get_full_history(),
                cost_summary,
                output_dir="./logs"
            )
        
        return {
            "winner": winner,
            "reason": reason,
            "rounds": round_count,
            "game_history": self.game_state.get_full_history(),
            "cost_summary": self.cost_tracker.get_summary(),
            "player_thoughts": {
                name: agent.get_thoughts()
                for name, agent in self.agents.items()
            }
        }


if __name__ == "__main__":
    # 示例运行
    players = ["Alice", "Bob", "Charlie", "David", "Eve"]
    
    game = GameFlow(
        players=players,
        use_rag=True,
        use_memory=True
    )
    
    result = game.run(max_rounds=10)
    print(f"\n获胜方: {result['winner']}")
    print(f"原因: {result['reason']}")

