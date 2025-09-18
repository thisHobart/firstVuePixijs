from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from fastapi import HTTPException
from agent import generate_dialogue
import json as _json
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

    # Pydantic -> dict
    conversation_history_dict = [msg.model_dump() for msg in request.history]

    try:
        # ✅ 直接 await 异步的 generate_dialogue
        response = await generate_dialogue(request.character, conversation_history_dict)

        # 调试输出
        try:
            print("Response to frontend:", _json.dumps(response, ensure_ascii=False))
        except Exception:
            pass

        return response

    except Exception as e:
        # 统一兜底（你 generate_dialogue 内部已有 try/except，这里二次保险）
        print("dialogue error:", repr(e))
        raise HTTPException(status_code=500, detail=f"dialogue failed: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
