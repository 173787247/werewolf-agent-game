"""
Streamlit 可视化界面
展示游戏执行流、思考链、成本分析等
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.game.game_flow import GameFlow
from src.visualization.visualizer import GameVisualizer
from src.utils.helpers import format_game_log


st.set_page_config(
    page_title="狼人杀游戏系统",
    page_icon="🐺",
    layout="wide"
)


def main():
    st.title("🐺 基于智能体协作的狼人杀游戏系统")
    st.markdown("---")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 游戏配置")
        
        # API 配置
        st.subheader("API 配置")
        api_type = st.selectbox("选择 API", ["DeepSeek", "OpenAI"])
        
        if api_type == "DeepSeek":
            api_key = st.text_input("DeepSeek API Key", type="password")
            base_url = st.text_input("Base URL", value="https://api.deepseek.com/v1")
        else:
            api_key = st.text_input("OpenAI API Key", type="password")
            base_url = None
        
        # 游戏设置
        st.subheader("游戏设置")
        use_rag = st.checkbox("启用 RAG 增强推理", value=True)
        use_memory = st.checkbox("启用记忆管理", value=True)
        max_rounds = st.slider("最大轮数", 1, 20, 10)
        
        # 玩家设置
        st.subheader("玩家设置")
        default_players = ["Alice", "Bob", "Charlie", "David", "Eve"]
        player_input = st.text_area(
            "玩家名称（每行一个）",
            value="\n".join(default_players),
            height=100
        )
        players = [p.strip() for p in player_input.split("\n") if p.strip()]
    
    # 主界面
    tab1, tab2, tab3, tab4 = st.tabs(["🎮 运行游戏", "📊 游戏日志", "💭 思考链追踪", "💰 成本分析"])
    
    with tab1:
        st.header("运行新游戏")
        
        if st.button("🚀 开始游戏", type="primary"):
            if not api_key:
                st.error("请先输入 API Key！")
                return
            
            if len(players) < 5:
                st.error("至少需要 5 名玩家！")
                return
            
            # 运行游戏
            with st.spinner("游戏进行中..."):
                try:
                    game = GameFlow(
                        players=players[:5],  # 只取前5个
                        api_key=api_key,
                        base_url=base_url if api_type == "DeepSeek" else None,
                        use_rag=use_rag,
                        use_memory=use_memory
                    )
                    
                    result = game.run(max_rounds=max_rounds, save_log=True)
                    
                    # 保存结果到 session state
                    st.session_state.game_result = result
                    st.session_state.game_history = result.get("game_history", [])
                    st.session_state.player_thoughts = result.get("player_thoughts", {})
                    st.session_state.cost_summary = result.get("cost_summary", {})
                    
                    st.success(f"游戏结束！获胜方: {result['winner']}")
                    st.info(f"原因: {result['reason']}")
                    
                except Exception as e:
                    st.error(f"游戏运行出错: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    with tab2:
        st.header("游戏日志")
        
        if "game_history" in st.session_state:
            game_history = st.session_state.game_history
            
            # 显示格式化日志
            formatted_log = format_game_log(game_history)
            st.text_area("游戏日志", formatted_log, height=600)
            
            # 下载按钮
            log_json = json.dumps(game_history, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 下载 JSON 日志",
                log_json,
                file_name="game_log.json",
                mime="application/json"
            )
        else:
            st.info("请先运行游戏")
    
    with tab3:
        st.header("思考链追踪")
        
        if "player_thoughts" in st.session_state:
            player_thoughts = st.session_state.player_thoughts
            
            # 选择玩家
            selected_player = st.selectbox("选择玩家", list(player_thoughts.keys()))
            
            if selected_player:
                thoughts = player_thoughts[selected_player]
                
                st.subheader(f"玩家: {selected_player}")
                
                for i, thought_data in enumerate(thoughts, 1):
                    with st.expander(f"步骤 {i} - {thought_data.get('phase', 'unknown')}"):
                        if "thought" in thought_data:
                            st.markdown(f"**思考 (Thought):** {thought_data['thought']}")
                        
                        if "action" in thought_data:
                            st.markdown(f"**动作 (Action):** {thought_data['action']}")
                        
                        if "observation" in thought_data:
                            st.markdown(f"**观察 (Observation):** {thought_data['observation']}")
                
                # 格式化输出
                visualizer = GameVisualizer()
                formatted = visualizer.format_thought_chain({selected_player: thoughts})
                st.code(formatted, language="text")
        else:
            st.info("请先运行游戏")
    
    with tab4:
        st.header("成本与复杂度分析")
        
        if "cost_summary" in st.session_state:
            cost_summary = st.session_state.cost_summary
            
            # 总体统计
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总调用次数", cost_summary.get("total_calls", 0))
            
            with col2:
                st.metric("总 Token 数", f"{cost_summary.get('total_tokens', 0):,}")
            
            with col3:
                st.metric("平均延迟", f"{cost_summary.get('average_latency', 0):.2f}s")
            
            with col4:
                st.metric("总运行时间", f"{cost_summary.get('total_time', 0):.2f}s")
            
            # Token 统计
            st.subheader("Token 统计")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Prompt Tokens", f"{cost_summary.get('prompt_tokens', 0):,}")
            
            with col2:
                st.metric("Completion Tokens", f"{cost_summary.get('completion_tokens', 0):,}")
            
            # 模型使用统计
            st.subheader("模型使用统计")
            model_usage = cost_summary.get("model_usage", {})
            
            if model_usage:
                for model, stats in model_usage.items():
                    with st.expander(f"模型: {model}"):
                        st.json(stats)
            
            # GPU 资源估算
            st.subheader("GPU 资源估算")
            gpu_estimate = cost_summary.get("gpu_estimate", {})
            if gpu_estimate:
                st.json(gpu_estimate)
            
            # 下载报告
            report_json = json.dumps(cost_summary, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 下载成本报告",
                report_json,
                file_name="cost_report.json",
                mime="application/json"
            )
        else:
            st.info("请先运行游戏")


if __name__ == "__main__":
    main()

