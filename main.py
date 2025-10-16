# 文件路径: main.py

import logging
from contextlib import asynccontextmanager
from typing import Optional
import nest_asyncio

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.providers.cursor_provider import CursorProvider, PlaywrightManager

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

playwright_manager = PlaywrightManager()
provider = CursorProvider(playwright_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理，初始化并维护一个持久化的、具备上下文感知能力的浏览器会话。"""
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION} (创世协议)")
    
    await playwright_manager.start()

    logger.info("战略核心: 'Playwright' 已激活，持久化个人会话准备就绪。")
    logger.info(f"服务监听于: http://localhost:{settings.NGINX_PORT}")
    
    yield
    
    logger.info("应用关闭中...")
    await playwright_manager.stop()
    logger.info("Playwright 实例已关闭。")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="一个功能完备、支持动态模型和上下文选择的 cursor.com 代理。",
    lifespan=lifespan
)

async def verify_api_key(authorization: Optional[str] = Header(None)):
    if settings.API_MASTER_KEY and settings.API_MASTER_KEY not in ["1", ""]:
        if not authorization or "bearer" not in authorization.lower():
            raise HTTPException(status_code=401, detail="需要 Bearer Token 认证。")
        token = authorization.split(" ")[-1]
        if token != settings.API_MASTER_KEY:
            raise HTTPException(status_code=403, detail="无效的 API Key。")

@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(request: Request):
    try:
        request_data = await request.json()
        return await provider.chat_completion(request_data)
    except Exception as e:
        logger.error(f"处理聊天请求时发生顶层错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

@app.get("/v1/models", dependencies=[Depends(verify_api_key)], response_class=JSONResponse)
async def list_models():
    return await provider.get_models()

@app.get("/", summary="根路径", include_in_schema=False)
def root():
    """根路径，提供服务状态信息"""
    return {
        "message": f"欢迎来到 {settings.APP_NAME} v{settings.APP_VERSION}",
        "status": "ok",
        "protocol": "Genesis Protocol · G (Final Ultimate Pro Max) - Dynamic & Aware"
    }
