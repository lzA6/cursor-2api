from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from fastapi.responses import StreamingResponse, JSONResponse

class BaseProvider(ABC):
    """
    定义所有 Provider 必须遵循的抽象基类。
    """
    @abstractmethod
    async def chat_completion(
        self,
        request_data: Dict[str, Any]
    ) -> Union[StreamingResponse, JSONResponse]:
        """处理聊天补全请求"""
        pass

    @abstractmethod
    async def get_models(self) -> JSONResponse:
        """获取模型列表"""
        pass
