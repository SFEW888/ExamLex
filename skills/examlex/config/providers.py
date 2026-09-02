"""
ExamLex 供应商配置
定义所有支持的 LLM 供应商
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
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

class ProviderConfig(BaseModel):
    """供应商配置"""
    name: str
    display_name: str
    icon: str
    api_base: str
    models: List[str]
    default_model: str
    requires_api_key: bool = True
    description: str = ""

# 预设供应商配置
BUILTIN_PROVIDERS: Dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        name="openai",
        display_name="OpenAI",
        icon="🤖",
        api_base="https://api.openai.com/v1",
        models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        default_model="gpt-4",
        requires_api_key=True,
        description="OpenAI GPT系列模型"
    ),
    "anthropic": ProviderConfig(
        name="anthropic",
        display_name="Claude Official",
        icon="🧠",
        api_base="https://api.anthropic.com",
        models=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        default_model="claude-3-sonnet-20240229",
        requires_api_key=True,
        description="Anthropic Claude系列模型"
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        display_name="DeepSeek",
        icon="🔷",
        api_base="https://api.deepseek.com/v1",
        models=["deepseek-chat", "deepseek-coder"],
        default_model="deepseek-chat",
        requires_api_key=True,
        description="DeepSeek 对话和编程模型"
    ),
    "kimi": ProviderConfig(
        name="kimi",
        display_name="Kimi",
        icon="🌙",
        api_base="https://api.moonshot.cn/v1",
        models=["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        default_model="moonshot-v1-32k",
        requires_api_key=True,
        description="Moonshot Kimi 长文本模型"
    ),
    "qwen": ProviderConfig(
        name="qwen",
        display_name="通义千问",
        icon="☁️",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        models=["qwen-turbo", "qwen-plus", "qwen-max"],
        default_model="qwen-plus",
        requires_api_key=True,
        description="阿里云通义千问系列模型"
    ),
    "local": ProviderConfig(
        name="local",
        display_name="本地模型",
        icon="💻",
        api_base="http://localhost:11434/v1",
        models=["llama3", "qwen2", "mistral", "phi3"],
        default_model="llama3",
        requires_api_key=False,
        description="通过 Ollama 运行的本地模型"
    )
}
