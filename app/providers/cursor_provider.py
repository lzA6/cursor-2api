# 文件路径: app/providers/cursor_provider.py

import json
import time
import logging
import uuid
import asyncio
import re
from typing import Dict, Any, AsyncGenerator, Union, Optional

from fastapi import HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from app.core.config import settings
from app.providers.base_provider import BaseProvider
from app.utils.sse_utils import (
    create_sse_data,
    create_chat_completion_chunk,
    create_non_stream_chat_completion,
    DONE_CHUNK
)

logger = logging.getLogger(__name__)

CONTEXT_REFRESH_THRESHOLD = 0.95

class PlaywrightManager:
    """
    管理一个唯一的、持久化的浏览器会话，并在启动时完成所有必要的函数绑定。
    """
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.queue = asyncio.Queue() # 将队列提升到 Manager 层面

    async def start(self):
        logger.info("正在启动个人专属的持久化 Playwright 会话...")
        self.playwright = await async_playwright().start()
        launch_args = [
            '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas', '--no-first-run', '--no-zygote',
            '--single-process', '--disable-gpu', '--dns-prefetch-disable'
        ]
        self.browser = await self.playwright.chromium.launch(headless=True, args=launch_args)
        
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )
        self.page = await self.context.new_page()

        # --- 核心修复：在启动时一次性注册所有通信函数 ---
        logger.info("正在为持久化页面绑定通信桥梁...")
        await self.page.expose_function("onStreamChunk", self.queue.put_nowait)
        await self.page.expose_function("onStreamError", lambda error: self.queue.put_nowait(Exception(f"Browser-side error: {error}")))
        await self.page.expose_function("onStreamEnd", lambda: self.queue.put_nowait(None))
        logger.info("通信桥梁绑定完成。")
        # --- 修复结束 ---

        stealth_script = "Object.defineProperty(navigator, 'webdriver', { get: () => false });"
        await self.page.add_init_script(stealth_script)
        await self.page.add_init_script(path="app/providers/fetch_override.js")

        await self.page.goto("https://cursor.com/docs", wait_until="networkidle")
        try:
            await self.page.locator('button[title="Expand Chat Sidebar"]').click(timeout=5000)
        except Exception:
            pass

        logger.info("个人专属的持久化会话已初始化并准备就绪。")

    async def stop(self):
        if self.page: await self.page.close()
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        logger.info("持久化 Playwright 会话已关闭。")

class CursorProvider(BaseProvider):
    """
    采用“终极单体”架构，具备上下文监控和自动回收能力。
    """
    def __init__(self, playwright_manager: PlaywrightManager):
        self.pm = playwright_manager
        self._lock = asyncio.Lock()

    async def chat_completion(self, request_data: Dict[str, Any]) -> Union[StreamingResponse, JSONResponse]:
        async with self._lock:
            try:
                is_stream = request_data.get("stream", False)
                if not is_stream:
                    raise NotImplementedError("Non-streamed responses are not implemented.")

                return StreamingResponse(
                    self._execute_and_stream(request_data),
                    media_type="text/event-stream"
                )
            except Exception as e:
                logger.error(f"处理 chat_completion 时发生顶层错误: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

    async def _check_and_handle_context_limit(self, page: Page, request_id: str, model_name: str) -> AsyncGenerator[bytes, None]:
        """检查上下文Token使用情况，如果超限则刷新并发送通知。"""
        try:
            context_element_selector = "div.flex-shrink-0.border-border.border-t"
            element = page.locator(context_element_selector).filter(has_text="上下文")
            
            if await element.count() > 0:
                text_content = await element.inner_text()
                current_tokens, max_tokens = self._parse_context_tokens(text_content)
                
                if current_tokens is not None and max_tokens is not None and max_tokens > 0:
                    usage_ratio = current_tokens / max_tokens
                    logger.info(f"当前上下文使用率: {usage_ratio:.2%} ({current_tokens}/{max_tokens})")
                    
                    if usage_ratio >= CONTEXT_REFRESH_THRESHOLD:
                        logger.warning(f"上下文使用率达到阈值，将自动刷新会话。")
                        notification_chunk = create_chat_completion_chunk(
                            request_id, model_name, "[系统提示：检测到上下文已满，已为您自动开启新对话。]\n\n"
                        )
                        yield create_sse_data(notification_chunk)
                        
                        await page.reload(wait_until="networkidle")
                        await page.locator('button[title="Expand Chat Sidebar"]').click(timeout=5000)
                        logger.info("页面已刷新，上下文已清空。")
        except Exception as e:
            logger.error(f"检查上下文限制时出错: {e}", exc_info=True)

    def _parse_context_tokens(self, text: str) -> (Optional[float], Optional[float]):
        match = re.search(r'上下文：\s*([\d\.]+)k\s*/\s*([\d\.]+)k', text, re.IGNORECASE)
        if match:
            try:
                current_k = float(match.group(1))
                max_k = float(match.group(2))
                return current_k * 1000, max_k * 1000
            except (ValueError, IndexError):
                return None, None
        return None, None

    async def _execute_and_stream(self, request_data: Dict[str, Any]) -> AsyncGenerator[bytes, None]:
        page = self.pm.page
        queue = self.pm.queue # 使用共享的队列
        if not page:
            raise RuntimeError("持久化页面未初始化。")

        request_id = f"chatcmpl-{uuid.uuid4()}"
        model_name = request_data.get("model", "anthropic/claude-3.5-sonnet")

        try:
            # --- 核心修复：不再重复注册函数 ---

            async for notification in self._check_and_handle_context_limit(page, request_id, model_name):
                yield notification

            payload = self._prepare_payload(request_data)
            last_user_prompt = self._get_last_user_prompt(request_data)
            if not last_user_prompt:
                raise ValueError("请求中不包含有效的用户消息。")

            await page.evaluate("(payload) => { window.chatPayload = payload; }", payload)
            
            await page.locator('textarea[placeholder*="Ask"]').fill(last_user_prompt)
            
            logger.info("点击发送按钮，触发被代理的 fetch...")
            await page.locator('button[type="submit"]').click()

            logger.info("等待并实时转换流数据...")
            buffer = ""
            while True:
                item = await asyncio.wait_for(queue.get(), timeout=120)
                if item is None:
                    logger.info("流结束。")
                    break
                if isinstance(item, Exception):
                    raise item
                
                buffer += item
                while "\n\n" in buffer:
                    raw_event, buffer = buffer.split("\n\n", 1)
                    if raw_event.startswith("data:"):
                        try:
                            data_str = raw_event[5:].strip()
                            if not data_str or data_str == "[DONE]":
                                continue
                            
                            cursor_data = json.loads(data_str)
                            if cursor_data.get("type") == "text-delta":
                                delta_content = cursor_data.get("delta", "")
                                if delta_content:
                                    openai_chunk = create_chat_completion_chunk(request_id, model_name, delta_content)
                                    yield create_sse_data(openai_chunk)
                        except json.JSONDecodeError:
                            logger.warning(f"无法解析 Cursor 流数据块: {raw_event}")
                            continue
        
        except Exception as e:
            logger.error(f"流编排失败: {e}", exc_info=True)
            error_chunk = create_chat_completion_chunk(request_id, model_name, f"Orchestration error: {str(e)}", "error")
            yield create_sse_data(error_chunk)

        finally:
            yield DONE_CHUNK

    def _prepare_payload(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        user_string = request_data.get("user", "")
        file_path = "/docs/"
        if "@" in user_string:
            parts = user_string.split("@", 1)
            if len(parts) == 2 and parts[1].startswith("/"):
                file_path = parts[1]
                logger.info(f"检测到上下文路径: {file_path}")

        context = [{"type": "file", "content": "", "filePath": file_path}]

        cursor_messages = []
        for msg in request_data.get("messages", []):
            role = msg.get("role")
            content = msg.get("content")
            
            if role and content:
                cursor_messages.append({
                    "role": role,
                    "parts": [{"type": "text", "text": content}],
                    "id": f"msg_{uuid.uuid4().hex[:16]}"
                })

        return {
            "context": context,
            "model": request_data.get("model", "anthropic/claude-3.5-sonnet"),
            "id": f"req_{uuid.uuid4().hex[:16]}",
            "messages": cursor_messages,
            "trigger": "submit-message"
        }

    def _get_last_user_prompt(self, request_data: Dict[str, Any]) -> str:
        user_messages = [msg for msg in request_data.get("messages", []) if msg.get("role") == "user"]
        if not user_messages: return ""
        
        last_message_content = user_messages[-1].get("content", "")
        if isinstance(last_message_content, list):
            return " ".join(p.get("text", "") for p in last_message_content if p.get("type") == "text")
        return last_message_content
    
    async def get_models(self) -> JSONResponse:
        model_data = {
            "object": "list",
            "data": [{"id": name, "object": "model", "created": int(time.time()), "owned_by": "lzA6"} for name in settings.KNOWN_MODELS]
        }
        return JSONResponse(content=model_data)
