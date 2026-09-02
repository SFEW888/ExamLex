"""
LLM 供应商管理器
统一管理所有 LLM 供应商的接入
"""

import os
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

from ..config.providers import BUILTIN_PROVIDERS, ProviderConfig

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
        print(f"✅ 已添加自定义供应商: {config.display_name}")

    def get_llm(self,
                provider: Optional[str] = None,
                model: Optional[str] = None,
                temperature: float = 0.7,
                **kwargs) -> Any:
        """
        获取 LLM 实例

        Args:
            provider: 供应商名称，如果为 None 则使用当前配置
            model: 模型名称，如果为 None 则使用默认模型
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            LLM 实例
        """

        # 使用当前配置或默认配置
        provider = provider or self.current_provider or "openai"

        # 获取供应商配置
        config = self.providers.get(provider) or self.custom_providers.get(provider)
        if not config:
            raise ValueError(f"未知供应商: {provider}")

        # 使用指定模型或默认模型
        model = model or self.current_model or config.default_model

        # 获取 API Key
        api_key_env = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(api_key_env)

        if config.requires_api_key and not api_key:
            raise ValueError(f"未找到 API Key: {api_key_env}，请在 .env 文件中配置")

        print(f"🤖 使用供应商: {config.display_name} | 模型: {model}")

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
                base_url=config.api_base.replace("/v1", ""),  # Ollama 不需要 /v1
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
        config = self.get_provider_info(provider)
        if not config:
            raise ValueError(f"供应商不存在: {provider}")

        self.current_provider = provider
        self.current_model = model or config.default_model

        print(f"✅ 已切换到: {config.display_name} - {self.current_model}")

    def list_providers(self) -> list[ProviderConfig]:
        """列出所有可用供应商"""
        return list(self.providers.values()) + list(self.custom_providers.values())

    def get_provider_info(self, provider: str) -> Optional[ProviderConfig]:
        """获取供应商信息"""
        return self.providers.get(provider) or self.custom_providers.get(provider)

    def test_connection(self, provider: str, model: Optional[str] = None) -> bool:
        """测试供应商连接"""
        try:
            llm = self.get_llm(provider, model, temperature=0)
            response = llm.invoke("Hello")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

# 全局实例
provider_manager = ProviderManager()
