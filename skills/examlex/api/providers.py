"""
供应商管理 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ..core.provider_manager import provider_manager
from ..config.providers import ProviderConfig

router = APIRouter(prefix="/api/providers", tags=["providers"])

class SetProviderRequest(BaseModel):
    provider: str
    model: Optional[str] = None

class TestConnectionRequest(BaseModel):
    provider: str
    model: Optional[str] = None

@router.get("/")
async def list_providers():
    """列出所有可用供应商"""
    providers = provider_manager.list_providers()

    return {
        "providers": [
            {
                "name": p.name,
                "display_name": p.display_name,
                "icon": p.icon,
                "models": p.models,
                "default_model": p.default_model,
                "requires_api_key": p.requires_api_key,
                "description": p.description,
                "api_base": p.api_base
            }
            for p in providers
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
        "api_base": config.api_base,
        "requires_api_key": config.requires_api_key,
        "description": config.description
    }

@router.post("/set")
async def set_provider(request: SetProviderRequest):
    """设置当前供应商"""
    try:
        provider_manager.set_current(request.provider, request.model)
        return {
            "success": True,
            "provider": request.provider,
            "model": request.model or provider_manager.current_model
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test")
async def test_connection(request: TestConnectionRequest):
    """测试供应商连接"""
    try:
        success = provider_manager.test_connection(request.provider, request.model)
        return {
            "success": success,
            "provider": request.provider,
            "model": request.model,
            "message": "连接成功" if success else "连接失败"
        }
    except Exception as e:
        return {
            "success": False,
            "provider": request.provider,
            "message": str(e)
        }

@router.post("/custom")
async def add_custom_provider(config: ProviderConfig):
    """添加自定义供应商"""
    try:
        provider_manager.add_custom_provider(config)
        return {
            "success": True,
            "provider": config.name,
            "message": "自定义供应商添加成功"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/current/info")
async def get_current_provider():
    """获取当前供应商信息"""
    if not provider_manager.current_provider:
        return {
            "provider": None,
            "model": None,
            "message": "未设置供应商"
        }

    config = provider_manager.get_provider_info(provider_manager.current_provider)
    return {
        "provider": provider_manager.current_provider,
        "model": provider_manager.current_model,
        "config": {
            "display_name": config.display_name,
            "icon": config.icon,
            "description": config.description
        }
    }
