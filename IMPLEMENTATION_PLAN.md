# ExamLex 完整实施方案

**目标**：搭建 学习管理系统 + LangGraph AI Agent + 灵活的 LLM 供应商配置

---

## 🎯 整体架构

```
┌────────────────────────────────────────────────────────┐
│                   ExamLex Frontend                     │
│          (HTML/CSS/JS - 已完成实用设计)                 │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│              FastAPI Backend                           │
│                                                        │
│  /api/agent/writing      - 写作 Agent                  │
│  /api/agent/listening    - 听力 Agent                  │
│  /api/agent/vocabulary   - 词汇 Agent                  │
│  /api/providers          - 供应商管理                   │
│  /api/profile            - 学习档案                    │
│  /api/memory/due         - 记忆卡                      │
└────────────────────┬───────────────────────────────────┘
                     │
        ┌────────────┴─────────────┐
        │                          │
        ▼                          ▼
┌──────────────────┐    ┌──────────────────┐
│   LangGraph      │    │  Provider        │
│   Agents         │    │  Manager         │
│                  │    │                  │
│ - Writing        │    │ - Claude         │
│ - Listening      │    │ - DeepSeek       │
│ - Reading        │    │ - Kimi           │
│ - Translation    │    │ - 本地模型       │
│ - Vocabulary     │    │ - 自定义         │
└──────────────────┘    └──────────────────┘
        │
        ▼
┌──────────────────┐
│   RAG System     │
│  (LlamaIndex)    │
│                  │
│ - ChromaDB       │
│ - 真题库         │
│ - 词汇库         │
│ - 语法规则       │
└──────────────────┘
```

---

## 📦 技术栈

### 后端
```python
# 核心框架
fastapi==0.109.0
uvicorn[standard]==0.27.0

# LangGraph + LangChain
langgraph==0.0.25
langchain==0.1.0
langchain-openai==0.0.5
langchain-community==0.0.13

# RAG
llama-index==0.9.48
chromadb==0.4.22

# 数据库
sqlalchemy==2.0.25
alembic==1.13.1

# 工具
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
```

### 前端
```
纯 HTML/CSS/JS（已完成）
无需额外依赖
```

---

## 🔧 供应商管理系统

### 1. 供应商配置文件

```python
# skills/examlex/config/providers.py

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class ProviderType(str, Enum):
    """供应商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    KIMI = "kimi"
    QWEN = "qwen"
    LOCAL = "local"
    CUSTOM = "custom"

class ModelConfig(BaseModel):
    """模型配置"""
    provider: ProviderType
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    
class ProviderConfig(BaseModel):
    """供应商配置"""
    name: str
    display_name: str
    icon: str
    api_base: str
    models: list[str]
    default_model: str
    requires_api_key: bool = True
    
# 预设供应商配置
BUILTIN_PROVIDERS: Dict[ProviderType, ProviderConfig] = {
    ProviderType.OPENAI: ProviderConfig(
        name="openai",
        display_name="OpenAI",
        icon="🤖",
        api_base="https://api.openai.com/v1",
        models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        default_model="gpt-4",
        requires_api_key=True
    ),
    ProviderType.ANTHROPIC: ProviderConfig(
        name="anthropic",
        display_name="Claude Official",
        icon="🧠",
        api_base="https://api.anthropic.com",
        models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        default_model="claude-3-sonnet",
        requires_api_key=True
    ),
    ProviderType.DEEPSEEK: ProviderConfig(
        name="deepseek",
        display_name="DeepSeek",
        icon="🔷",
        api_base="https://api.deepseek.com/v1",
        models=["deepseek-chat", "deepseek-coder"],
        default_model="deepseek-chat",
        requires_api_key=True
    ),
    ProviderType.KIMI: ProviderConfig(
        name="kimi",
        display_name="Kimi",
        icon="🌙",
        api_base="https://api.moonshot.cn/v1",
        models=["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        default_model="moonshot-v1-32k",
        requires_api_key=True
    ),
    ProviderType.QWEN: ProviderConfig(
        name="qwen",
        display_name="通义千问",
        icon="☁️",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        models=["qwen-turbo", "qwen-plus", "qwen-max"],
        default_model="qwen-plus",
        requires_api_key=True
    ),
    ProviderType.LOCAL: ProviderConfig(
        name="local",
        display_name="本地模型",
        icon="💻",
        api_base="http://localhost:11434/v1",
        models=["llama3", "qwen2", "mistral"],
        default_model="llama3",
        requires_api_key=False
    )
}
```

---

### 2. 供应商管理器

```python
# skills/examlex/core/provider_manager.py

import os
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

class ProviderManager:
    """LLM 供应商管理器"""
    
    def __init__(self):
        self.providers: Dict[str, ProviderConfig] = BUILTIN_PROVIDERS.copy()
        self.custom_providers: Dict[str, ProviderConfig] = {}
        self.current_provider: Optional[str] = None
        self.current_model: Optional[str] = None
        
    def add_custom_provider(self, config: ProviderConfig):
        """添加自定义供应商"""
        self.custom_providers[config.name] = config
        
    def get_llm(self, 
                provider: Optional[str] = None, 
                model: Optional[str] = None,
                temperature: float = 0.7,
                **kwargs) -> Any:
        """获取 LLM 实例"""
        
        # 使用当前配置或默认配置
        provider = provider or self.current_provider or "openai"
        
        # 获取供应商配置
        config = self.providers.get(provider) or self.custom_providers.get(provider)
        if not config:
            raise ValueError(f"未知供应商: {provider}")
        
        # 使用指定模型或默认模型
        model = model or config.default_model
        
        # 获取 API Key
        api_key = os.getenv(f"{provider.upper()}_API_KEY")
        
        # 根据供应商类型创建 LLM
        if provider == "openai":
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
                **kwargs
            )
        
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                api_key=api_key,
                **kwargs
            )
        
        elif provider in ["deepseek", "kimi", "qwen"]:
            # 这些供应商兼容 OpenAI API
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
                base_url=config.api_base,
                **kwargs
            )
        
        elif provider == "local":
            # 本地模型（Ollama）
            return ChatOllama(
                model=model,
                temperature=temperature,
                base_url=config.api_base,
                **kwargs
            )
        
        else:
            # 自定义供应商（假设兼容 OpenAI API）
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
                base_url=config.api_base,
                **kwargs
            )
    
    def set_current(self, provider: str, model: Optional[str] = None):
        """设置当前使用的供应商和模型"""
        self.current_provider = provider
        self.current_model = model
    
    def list_providers(self) -> list[ProviderConfig]:
        """列出所有可用供应商"""
        return list(self.providers.values()) + list(self.custom_providers.values())
    
    def get_provider_info(self, provider: str) -> Optional[ProviderConfig]:
        """获取供应商信息"""
        return self.providers.get(provider) or self.custom_providers.get(provider)

# 全局实例
provider_manager = ProviderManager()
```

---

### 3. 配置 API 端点

```python
# skills/examlex/api/providers.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/providers", tags=["providers"])

class SetProviderRequest(BaseModel):
    provider: str
    model: Optional[str] = None

@router.get("/")
async def list_providers():
    """列出所有供应商"""
    return {
        "providers": [
            {
                "name": p.name,
                "display_name": p.display_name,
                "icon": p.icon,
                "models": p.models,
                "default_model": p.default_model,
                "requires_api_key": p.requires_api_key
            }
            for p in provider_manager.list_providers()
        ]
    }

@router.get("/{provider}")
async def get_provider(provider: str):
    """获取供应商详情"""
    config = provider_manager.get_provider_info(provider)
    if not config:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    return {
        "name": config.name,
        "display_name": config.display_name,
        "icon": config.icon,
        "models": config.models,
        "default_model": config.default_model,
        "api_base": config.api_base
    }

@router.post("/set")
async def set_provider(request: SetProviderRequest):
    """设置当前供应商"""
    try:
        provider_manager.set_current(request.provider, request.model)
        return {
            "success": True,
            "provider": request.provider,
            "model": request.model
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/custom")
async def add_custom_provider(config: ProviderConfig):
    """添加自定义供应商"""
    try:
        provider_manager.add_custom_provider(config)
        return {"success": True, "provider": config.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 🤖 LangGraph Agent 实现

### 1. Writing Agent 工作流

```python
# skills/examlex/agents/writing_agent.py

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

class EssayReviewState(TypedDict):
    """作文批改状态"""
    # 输入
    essay: str
    exam_type: str
    user_id: str
    
    # Agent 结果
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

def orchestrator_node(state: EssayReviewState) -> EssayReviewState:
    """协调者：初始化状态"""
    print("🎯 Orchestrator: 开始分析...")
    state["iteration_count"] = 0
    state["needs_refinement"] = False
    return state

def writing_agent_node(state: EssayReviewState) -> EssayReviewState:
    """写作 Agent：结构分析"""
    print("📝 Writing Agent: 分析结构...")
    
    # 获取 LLM
    llm = provider_manager.get_llm(temperature=0.3)
    
    system_prompt = """你是一位经验丰富的英语写作导师。
请分析作文的结构、论证和逻辑。"""
    
    user_prompt = f"""
考试类型：{state['exam_type']}

作文：
{state['essay']}

请分析：
1. 结构（三段式是否清晰）
2. 论点是否明确
3. 论据是否充分
4. 逻辑连接是否流畅

以 JSON 格式返回：
{{
    "score": 75,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(messages)
    
    # 解析结果（简化版，实际应该用 JSON 解析）
    state["structure_analysis"] = {
        "score": 75,
        "issues": ["论据不够充分", "缺少逻辑连接词"],
        "suggestions": ["添加具体例子", "使用 Furthermore, Moreover"]
    }
    
    return state

def grammar_agent_node(state: EssayReviewState) -> EssayReviewState:
    """语法 Agent：语法检查"""
    print("🔍 Grammar Agent: 检查语法...")
    
    llm = provider_manager.get_llm(temperature=0)
    
    prompt = f"""
检查以下作文的语法错误：

{state['essay']}

找出所有语法错误，包括时态、语态、主谓一致等。
以 JSON 列表格式返回，每个错误包括 location, error, correction。
"""
    
    response = llm.invoke(prompt)
    
    state["grammar_issues"] = [
        {"location": "第1段第2句", "error": "时态错误", "correction": "应该用过去时"},
        {"location": "第2段第1句", "error": "主谓不一致", "correction": "主语复数，动词也应复数"}
    ]
    
    return state

def vocabulary_agent_node(state: EssayReviewState) -> EssayReviewState:
    """词汇 Agent：词汇分析"""
    print("📚 Vocabulary Agent: 分析词汇...")
    
    llm = provider_manager.get_llm(temperature=0.5)
    
    prompt = f"""
分析作文的词汇使用：

{state['essay']}

找出：
1. 重复使用的词汇
2. 可以提升的表达
3. 高分替换词
"""
    
    response = llm.invoke(prompt)
    
    state["vocabulary_suggestions"] = [
        {"original": "very important", "suggestion": "crucial / vital", "reason": "更学术化"},
        {"original": "a lot of", "suggestion": "numerous", "reason": "避免口语化"}
    ]
    
    return state

def synthesize_node(state: EssayReviewState) -> EssayReviewState:
    """综合反馈"""
    print("🔄 Synthesize: 生成综合反馈...")
    
    # 计算分数
    grammar_score = 100 - len(state["grammar_issues"]) * 5
    structure_score = state["structure_analysis"]["score"]
    vocab_score = 100 - len(state["vocabulary_suggestions"]) * 3
    
    state["score"] = int((grammar_score + structure_score + vocab_score) / 3)
    
    # 生成反馈
    state["final_feedback"] = f"""
📊 作文评分：{state['score']}/100

1️⃣ 结构分析（{structure_score}/100）
问题：
{chr(10).join(f"- {issue}" for issue in state['structure_analysis']['issues'])}

建议：
{chr(10).join(f"- {sug}" for sug in state['structure_analysis']['suggestions'])}

2️⃣ 语法问题（{grammar_score}/100）
共 {len(state['grammar_issues'])} 个错误：
{chr(10).join(f"- {issue['location']}: {issue['error']} → {issue['correction']}" for issue in state['grammar_issues'])}

3️⃣ 词汇建议（{vocab_score}/100）
{chr(10).join(f"- {sug['original']} → {sug['suggestion']} ({sug['reason']})" for sug in state['vocabulary_suggestions'])}
"""
    
    return state

def should_refine(state: EssayReviewState) -> str:
    """判断是否需要优化"""
    state["iteration_count"] += 1
    
    if state["score"] < 80 and state["iteration_count"] < 2:
        print(f"♻️  分数 {state['score']} < 80，进行第 {state['iteration_count']} 轮优化")
        return "refine"
    else:
        print(f"✅ 分析完成，最终分数：{state['score']}")
        return "end"

def refine_essay_node(state: EssayReviewState) -> EssayReviewState:
    """优化作文"""
    print("✨ Refine: 优化作文...")
    
    llm = provider_manager.get_llm(temperature=0.7)
    
    prompt = f"""
根据反馈优化作文：

原作文：
{state['essay']}

反馈：
{state['final_feedback']}

请输出优化后的作文。
"""
    
    response = llm.invoke(prompt)
    
    state["revised_essay"] = response.content
    state["essay"] = response.content  # 更新作文供下一轮分析
    
    return state

# 构建工作流
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
    
    # 添加边
    workflow.add_edge("orchestrator", "writing_agent")
    workflow.add_edge("writing_agent", "grammar_agent")
    workflow.add_edge("grammar_agent", "vocabulary_agent")
    workflow.add_edge("vocabulary_agent", "synthesize")
    
    # 条件边
    workflow.add_conditional_edges(
        "synthesize",
        should_refine,
        {
            "refine": "refine",
            "end": END
        }
    )
    
    # 优化后循环
    workflow.add_edge("refine", "writing_agent")
    
    return workflow.compile()

# 全局工作流实例
writing_workflow = create_writing_workflow()
```

---

### 2. API 端点

```python
# skills/examlex/api/agents.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/agent", tags=["agents"])

class EssayReviewRequest(BaseModel):
    essay: str
    exam_type: str
    user_id: str

@router.post("/writing")
async def review_essay(request: EssayReviewRequest):
    """作文批改 API"""
    try:
        # 执行工作流
        result = writing_workflow.invoke({
            "essay": request.essay,
            "exam_type": request.exam_type,
            "user_id": request.user_id
        })
        
        return {
            "success": True,
            "score": result["score"],
            "feedback": result["final_feedback"],
            "revised_essay": result.get("revised_essay"),
            "details": {
                "structure": result["structure_analysis"],
                "grammar": result["grammar_issues"],
                "vocabulary": result["vocabulary_suggestions"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🚀 完整的项目结构

```
ExamLex/
├── skills/
│   └── examlex/
│       ├── __init__.py
│       ├── cli.py                    # 现有 CLI
│       ├── config/
│       │   ├── __init__.py
│       │   └── providers.py          # 供应商配置
│       ├── core/
│       │   ├── __init__.py
│       │   ├── provider_manager.py   # 供应商管理器
│       │   └── profile.py            # 学习档案
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── writing_agent.py      # 写作 Agent
│       │   ├── listening_agent.py    # 听力 Agent
│       │   ├── reading_agent.py      # 阅读 Agent
│       │   ├── vocabulary_agent.py   # 词汇 Agent
│       │   └── orchestrator.py       # 协调 Agent
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py               # FastAPI 主入口
│       │   ├── providers.py          # 供应商 API
│       │   ├── agents.py             # Agent API
│       │   └── profile.py            # 档案 API
│       ├── assets/
│       │   └── web/
│       │       ├── index.html        # 前端（已完成）
│       │       ├── styles.css
│       │       ├── components.css
│       │       └── app.js
│       └── scripts/
│           └── web_app.py            # Web 服务器
├── requirements.txt
└── README.md
```

---

## 📝 下一步实施计划

### Week 1: 供应商管理系统
- Day 1-2: 实现 ProviderManager
- Day 3-4: API 端点和测试
- Day 5: 前端供应商选择UI

### Week 2: Writing Agent
- Day 1-3: LangGraph 工作流
- Day 4-5: API 集成和测试

### Week 3-4: 其他 Agent
- Listening, Reading, Vocabulary, Translation

### Week 5: RAG 知识库
- 真题库、词汇库、语法规则

---

准备好开始了吗？我们从哪个部分开始？🚀
