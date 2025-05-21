from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import uvicorn
import logging
import sys
import os
from .AddDoc import DocumentProcessor


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("server")

# 创建FastAPI应用实例
app = FastAPI(title="文档处理API", description="用于添加URL到知识库的API")

# 创建DocumentProcessor实例
doc_processor = DocumentProcessor(persist_directory=os.getenv("PERSIST_DIR","./vector_store"))

# 定义请求模型
class UrlRequest(BaseModel):
    urls: List[str]

@app.post("/add_urls")
async def add_urls(request: UrlRequest):
    """
    添加URL到知识库
    
    接收URL列表并处理为向量存储
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="URL列表不能为空")
    
    try:
        logger.info(f"收到请求处理 {len(request.urls)} 个URL")
        result = await doc_processor.add_urls(request.urls)
        
        if "error" in result:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": result["error"]}
            )
        
        return result
    
    except Exception as e:
        logger.error(f"处理URL时出错: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
# 确保当脚本直接运行时也能执行main函数
if __name__ == "__main__":
    main()