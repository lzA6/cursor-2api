import json
import time
from typing import Dict, Any, Optional

# SSE 'data: [DONE]' 结束标志
DONE_CHUNK = b"data: [DONE]\n\n"

def create_sse_data(data: Dict[str, Any]) -> bytes:
    """将字典转换为 SSE 格式的字节串"""
    return f"data: {json.dumps(data)}\n\n".encode('utf-8')

def create_chat_completion_chunk(
    request_id: str,
    model: str,
    content: str,
    finish_reason: Optional[str] = None
) -> Dict[str, Any]:
    """创建 OpenAI 格式的流式聊天补全块"""
    return {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"content": content},
                "finish_reason": finish_reason,
                "logprobs": None
            }
        ],
    }

def create_non_stream_chat_completion(
    request_id: str,
    model: str,
    content: str,
    finish_reason: str = "stop"
) -> Dict[str, Any]:
    """创建 OpenAI 格式的非流式聊天补全响应"""
    created_time = int(time.time())
    return {
        "id": request_id,
        "object": "chat.completion",
        "created": created_time,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": -1,  # 无法精确计算，设为-1
            "completion_tokens": len(content),
            "total_tokens": -1,
        },
    }
