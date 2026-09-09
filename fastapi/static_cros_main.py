from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, HTMLResponse
from starlette.staticfiles import StaticFiles

app = FastAPI()

#解决跨域问题，两个服务器之间可以进行交互
#浏览器有同源策略。只要协议、IP、port有至少一个不一致，就是跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],#允许所有来源（生产环境建议指定具体域名）
    allow_credentials=True,
    allow_methods=["*"],#允许所有HTTP方法
    allow_headers=["*"],#允许所有请求头
)

#将某个目录下的静态资源挂载到uvicorn服务器中
#之后就可以通过服务器地址访问静态资源
#app.mount(path="/static",app=StaticFiles(directory="test"))

@app.get("/static/hello.html")
def test_hello():
    html_path = "html页面的绝对路径"
    # return FileResponse(
    #     html_path
    # )
    return HTMLResponse(
        Path(html_path).read_text(encoding="utf-8"),
    )