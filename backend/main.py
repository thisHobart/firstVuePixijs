from fastapi import FastAPI                     # FastAPI 主类 (FastAPI main class)
from fastapi.middleware.cors import CORSMiddleware  # 跨域中间件 (CORS middleware)

app = FastAPI()  # 创建 FastAPI 应用 (Create FastAPI app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # 前端 Vite dev server origin (without trailing slash)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

from pydantic import BaseModel
from agent import generate_dialogue

class DialogueRequest(BaseModel):
    character: str
    node: str
    # The 'node' here can be interpreted as the player's last action/choice text
    # or a special node id like 'start'.

@app.post("/api/dialogue")
async def dialogue(request: DialogueRequest):
    print(f"Received request for character: {request.character}, node: {request.node}")
    # For now, we'll create a simple conversation history.
    # In a more advanced setup, the client would send the history.
    conversation_history = [
        {"role": "player", "content": request.node}
    ]

    response = generate_dialogue(request.character, conversation_history)
    return response

# ←↓↓↓↓↓↓↓↓ 添加这段入口入口，Run main.py 时即启动 Uvicorn ↓↓↓↓↓↓↓↓↓↓
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",        # 格式："模块名:FastAPI实例名"
        host="127.0.0.1",   # 监听本机地址
        port =8000,          # 端口
        reload=True        # 热重载
    )
