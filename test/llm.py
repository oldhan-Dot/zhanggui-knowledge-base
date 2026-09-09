# from langchain_openai import ChatOpenAI
#
# llm = ChatOpenAI(
#     model_name="gpt-4o-mini"
# )
# res = llm.invoke("你好")
# print(res)
# try:
#     import torch
#     print(f"✅ PyTorch 加载成功！版本：{torch.__version__}")
#     print(f"✅ CUDA 状态：{torch.cuda.is_available()}（CPU版显示False正常）")
#     print(f"✅ CUDA 设备数：{torch.cuda.device_count()}")
#     print(f"✅ CUDA 设备名称：{torch.cuda.get_device_name(0)}")
# except Exception as e:
#     print(f"❌ PyTorch 加载失败：{e}")


# 临时测试文件（跑完可删）
from dotenv import load_dotenv
load_dotenv(override=True)
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
print("端点:", os.getenv("OPENAI_BASE_URL"))
print("模型:", os.getenv("VL_MODEL"))

# 只发一条最简文本请求，验证模型名是否被接受
resp = client.chat.completions.create(
    model=os.getenv("VL_MODEL"),
    messages=[{"role": "user", "content": "你好"}],
)
print("成功:", resp.choices[0].message.content)
