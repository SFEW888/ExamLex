"""
Writing Agent - 作文批改 LangGraph 工作流
实现多 Agent 协作批改作文
"""

from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
import json

from ..core.provider_manager import provider_manager

# ===== 状态定义 =====

class EssayReviewState(TypedDict):
    """作文批改状态"""
    # 输入
    essay: str
    exam_type: str
    user_id: str

    # Agent 分析结果
    grammar_issues: List[dict]
    structure_analysis: dict
    vocabulary_suggestions: List[dict]

    # 输出
    final_feedback: str
    revised_essay: Optional[str]
    score: int

    # 控制
    iteration_count: int
    needs_refinement: bool

# ===== Agent 节点 =====

def orchestrator_node(state: EssayReviewState) -> EssayReviewState:
    """协调者：初始化状态"""
    print("=" * 60)
    print("🎯 Orchestrator: 开始作文批改流程...")
    print("=" * 60)
    state["iteration_count"] = 0
    state["needs_refinement"] = False
    return state

def writing_agent_node(state: EssayReviewState) -> EssayReviewState:
    """写作 Agent：结构分析"""
    print("\n📝 Writing Agent: 分析作文结构...")

    llm = provider_manager.get_llm(temperature=0.3)

    system_prompt = """你是一位经验丰富的英语写作导师。
请分析作文的结构、论证和逻辑连贯性。"""

    user_prompt = f"""
考试类型：{state['exam_type']}

作文：
{state['essay']}

请分析：
1. 结构（三段式是否清晰：引言-主体-结论）
2. 论点是否明确
3. 论据是否充分、有说服力
4. 逻辑连接是否流畅

以 JSON 格式返回：
{{
    "score": 75,
    "issues": ["具体问题1", "具体问题2"],
    "suggestions": ["改进建议1", "改进建议2"]
}}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    try:
        response = llm.invoke(messages)
        # 尝试解析 JSON
        try:
            result = json.loads(response.content)
            state["structure_analysis"] = result
        except:
            # 如果解析失败，使用默认结果
            state["structure_analysis"] = {
                "score": 75,
                "issues": ["结构分析失败，请重试"],
                "suggestions": ["确保作文有清晰的三段式结构"]
            }
    except Exception as e:
        print(f"⚠️  Writing Agent 出错: {e}")
        state["structure_analysis"] = {
            "score": 70,
            "issues": [f"分析出错: {str(e)}"],
            "suggestions": ["请检查网络连接和 API 配置"]
        }

    print(f"   结构分数: {state['structure_analysis']['score']}/100")
    return state

def grammar_agent_node(state: EssayReviewState) -> EssayReviewState:
    """语法 Agent：语法检查"""
    print("\n🔍 Grammar Agent: 检查语法错误...")

    llm = provider_manager.get_llm(temperature=0)

    prompt = f"""
请仔细检查以下作文的语法错误：

{state['essay']}

找出所有语法错误，包括：
- 时态错误
- 语态错误
- 主谓一致
- 冠词使用
- 介词使用
- 句子结构

以 JSON 列表格式返回，每个错误包括：
[
    {{"location": "第X段第Y句", "error": "错误类型", "correction": "修正建议"}},
    ...
]
"""

    try:
        response = llm.invoke(prompt)
        try:
            result = json.loads(response.content)
            state["grammar_issues"] = result if isinstance(result, list) else []
        except:
            state["grammar_issues"] = [
                {"location": "整体", "error": "语法检查失败", "correction": "请重试"}
            ]
    except Exception as e:
        print(f"⚠️  Grammar Agent 出错: {e}")
        state["grammar_issues"] = [
            {"location": "N/A", "error": f"检查出错: {str(e)}", "correction": "请检查配置"}
        ]

    print(f"   发现 {len(state['grammar_issues'])} 个语法问题")
    return state

def vocabulary_agent_node(state: EssayReviewState) -> EssayReviewState:
    """词汇 Agent：词汇分析"""
    print("\n📚 Vocabulary Agent: 分析词汇使用...")

    llm = provider_manager.get_llm(temperature=0.5)

    prompt = f"""
请分析以下作文的词汇使用：

{state['essay']}

找出：
1. 重复使用的词汇（需要替换）
2. 口语化表达（需要改为书面语）
3. 可以提升的高分词汇

以 JSON 列表格式返回：
[
    {{"original": "原词汇", "suggestion": "建议替换词", "reason": "原因"}},
    ...
]
"""

    try:
        response = llm.invoke(prompt)
        try:
            result = json.loads(response.content)
            state["vocabulary_suggestions"] = result if isinstance(result, list) else []
        except:
            state["vocabulary_suggestions"] = [
                {"original": "N/A", "suggestion": "词汇分析失败", "reason": "请重试"}
            ]
    except Exception as e:
        print(f"⚠️  Vocabulary Agent 出错: {e}")
        state["vocabulary_suggestions"] = [
            {"original": "N/A", "suggestion": "分析出错", "reason": str(e)}
        ]

    print(f"   提供 {len(state['vocabulary_suggestions'])} 个词汇建议")
    return state

def synthesize_node(state: EssayReviewState) -> EssayReviewState:
    """综合反馈节点"""
    print("\n🔄 Synthesize: 生成综合反馈...")

    # 计算分数
    grammar_score = max(0, 100 - len(state["grammar_issues"]) * 5)
    structure_score = state["structure_analysis"].get("score", 70)
    vocab_score = max(0, 100 - len(state["vocabulary_suggestions"]) * 3)

    state["score"] = int((grammar_score + structure_score + vocab_score) / 3)

    # 生成综合反馈
    feedback_parts = []

    feedback_parts.append(f"📊 作文总评：{state['score']}/100\n")

    feedback_parts.append(f"\n1️⃣ 结构分析（{structure_score}/100）")
    feedback_parts.append("问题：")
    for issue in state['structure_analysis'].get('issues', []):
        feedback_parts.append(f"  • {issue}")
    feedback_parts.append("建议：")
    for sug in state['structure_analysis'].get('suggestions', []):
        feedback_parts.append(f"  • {sug}")

    feedback_parts.append(f"\n2️⃣ 语法检查（{grammar_score}/100）")
    feedback_parts.append(f"共发现 {len(state['grammar_issues'])} 个语法问题：")
    for issue in state['grammar_issues'][:5]:  # 只显示前5个
        feedback_parts.append(f"  • {issue.get('location', 'N/A')}: {issue.get('error', 'N/A')}")
        feedback_parts.append(f"    → {issue.get('correction', 'N/A')}")

    feedback_parts.append(f"\n3️⃣ 词汇建议（{vocab_score}/100）")
    for sug in state['vocabulary_suggestions'][:5]:  # 只显示前5个
        feedback_parts.append(f"  • {sug.get('original', 'N/A')} → {sug.get('suggestion', 'N/A')}")
        feedback_parts.append(f"    原因：{sug.get('reason', 'N/A')}")

    state["final_feedback"] = "\n".join(feedback_parts)

    print(f"   综合分数: {state['score']}/100")
    return state

def should_refine(state: EssayReviewState) -> str:
    """判断是否需要优化"""
    state["iteration_count"] += 1

    # 如果分数低于 75 且迭代次数少于 2 次，进行优化
    if state["score"] < 75 and state["iteration_count"] < 2:
        print(f"\n♻️  分数 {state['score']} < 75，进行第 {state['iteration_count']} 轮优化...")
        return "refine"
    else:
        print(f"\n✅ 分析完成！最终分数：{state['score']}/100")
        return "end"

def refine_essay_node(state: EssayReviewState) -> EssayReviewState:
    """优化作文节点"""
    print("\n✨ Refine: 根据反馈优化作文...")

    llm = provider_manager.get_llm(temperature=0.7)

    prompt = f"""
请根据以下反馈优化作文：

原作文：
{state['essay']}

详细反馈：
{state['final_feedback']}

请输出优化后的完整作文，要求：
1. 修正所有语法错误
2. 改善结构和逻辑
3. 使用更高级的词汇
4. 保持原意不变
"""

    try:
        response = llm.invoke(prompt)
        state["revised_essay"] = response.content
        state["essay"] = response.content  # 更新作文供下一轮分析
        print("   ✅ 作文优化完成")
    except Exception as e:
        print(f"   ⚠️  优化失败: {e}")
        state["revised_essay"] = state["essay"]

    return state

# ===== 构建工作流 =====

def create_writing_workflow():
    """创建写作 Agent 工作流"""
    workflow = StateGraph(EssayReviewState)

    # 添加节点
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("writing_agent", writing_agent_node)
    workflow.add_node("grammar_agent", grammar_agent_node)
    workflow.add_node("vocabulary_agent", vocabulary_agent_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("refine", refine_essay_node)

    # 设置入口
    workflow.set_entry_point("orchestrator")

    # 添加边（定义流程）
    workflow.add_edge("orchestrator", "writing_agent")
    workflow.add_edge("writing_agent", "grammar_agent")
    workflow.add_edge("grammar_agent", "vocabulary_agent")
    workflow.add_edge("vocabulary_agent", "synthesize")

    # 添加条件边（根据分数决定是否优化）
    workflow.add_conditional_edges(
        "synthesize",
        should_refine,
        {
            "refine": "refine",
            "end": END
        }
    )

    # 优化后循环回 writing_agent
    workflow.add_edge("refine", "writing_agent")

    return workflow.compile()

# 全局工作流实例
writing_workflow = create_writing_workflow()
