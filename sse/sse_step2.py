import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# 1. 初始化+跨域（最基础配置）
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 仅测试用
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/stream/{sessionId}")
async def simple_stream(sessionId : str):
    async def generate_data():
        for i in range(5):
            yield f"data:hello ,{sessionId}，{i}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(generate_data(),media_type="text/event-stream")





if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
