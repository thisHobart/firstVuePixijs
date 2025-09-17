from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from fastapi.concurrency import run_in_threadpool  # 导入线程池工具

from agent import generate_dialogue

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 重新设计 API 请求体，使其更具扩展性 ---
class Message(BaseModel):
    role: str
    content: str


class DialogueRequest(BaseModel):
    character: str
    # 接收完整的对话历史
    history: List[Message] = Field(..., min_items=1)


@app.post("/api/dialogue", response_model=List[Dict[str, Any]])
async def dialogue(request: DialogueRequest):
    print(f"Received request for character: {request.character}")
    print(f"Conversation history: {request.history}")

    # 将 Pydantic 模型转换为 agent 函数需要的字典列表
    conversation_history_dict = [msg.model_dump() for msg in request.history]

    # --- 使用线程池异步执行耗时的AI调用，防止阻塞 ---
    response = await run_in_threadpool(
        generate_dialogue,
        request.character,
        conversation_history_dict
    )
    try:
        # 调试用：直观展示将要返回给前端的数据
        import json as _json
        print("Response to frontend:", _json.dumps(response, ensure_ascii=False))
    except Exception:
        pass

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
