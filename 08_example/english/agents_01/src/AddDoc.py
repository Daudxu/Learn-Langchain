import tempfile
import os
import logging
from typing import List, Union, Optional
import uuid
from dotenv import load_dotenv as _load_dotenv
_load_dotenv()


from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http import models as rest

class DocumentProcessor:
    """用于处理和向量化不同类型文档的类"""
    
    def __init__(self, 
                 collection_name: str = os.getenv("COLLECTION_NAME", "xiaolang_documents"),
                 embedding_model: str = os.getenv("EMBEDDING_MODEL", "Pro/BAAI/bge-m3"),
                 chunk_size: int = 800, 
                 chunk_overlap: int = 50,
                 persist_directory: Optional[str] = None) -> None:
        """
        初始化文档处理器
        
        Args:
            collection_name: Qdrant集合名称
            embedding_model: OpenAI嵌入模型名称
            chunk_size: 文档分片大小
            chunk_overlap: 文档分片重叠大小
            persist_directory: 永久存储目录，None则使用临时目录
        """
        # 配置日志
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("DocumentProcessor")
        
        # 初始化嵌入模型
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            api_key=os.getenv("EMBEDDING_API_KEY"),
            base_url=os.getenv("EMBEDDING_API_BASE")
            )
        
        # 配置文本分割器
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        
        # 设置向量存储目录
        self.is_temp_dir = persist_directory is None
        self.storage_dir = persist_directory or tempfile.mkdtemp(prefix="qdrant_")
        self.logger.info(f"使用存储目录: {self.storage_dir}")
        
        # 初始化Qdrant客户端和集合
        self.collection_name = collection_name
        self.client = QdrantClient(path=self.storage_dir)
        
        # 检查并创建集合
        self._ensure_collection_exists()
        
        # 初始化向量存储
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
    
    def _ensure_collection_exists(self) -> None:
        """确保Qdrant集合存在，不存在则创建"""
        try:
            collections = self.client.get_collections().collections
            if not any(collection.name == self.collection_name for collection in collections):
                self.logger.info(f"创建新集合: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                    optimizers_config=rest.OptimizersConfigDiff(
                        indexing_threshold=10000,  # 优化索引阈值
                    ),
                    hnsw_config=rest.HnswConfigDiff(
                        m=16,  # 提高检索精度的HNSW图参数
                        ef_construct=128,  # 提高构建质量
                    )
                )
            else:
                self.logger.info(f"使用已有集合: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"创建集合时出错: {e}")
            raise
    
    async def add_urls(self, urls: List[str]) -> dict:
        """
        从URL加载文档并添加到向量存储
        
        Args:
            urls: 要加载的URL列表
            
        Returns:
            包含状态信息的字典
        """
        try:
            self.logger.info(f"正在加载URLs: {urls}")
            loader = WebBaseLoader(urls)
            docs = loader.load()
            print("-----------docs------------")
            print(docs)
            self.logger.info(f"已加载 {len(docs)} 个文档")
            return await self._process_documents(docs)
        except Exception as e:
            self.logger.error(f"处理URL时出错: {e}")
            return {"error": str(e)}
    
    
    async def _process_documents(self, docs: List[Document]) -> dict:
        """
        处理文档并添加到向量存储
        
        Args:
            docs: 文档列表
            
        Returns:
            包含状态信息的字典
        """
        if not docs:
            return {"status": "warning", "message": "没有文档需要处理"}
            
        try:
            # 分割文档
            print("-----------docs------------")
            print(docs)
            chunks = self.splitter.split_documents(docs)
            print("-----------chunks------------")
            print(chunks)
            self.logger.info(f"文档已分割为 {len(chunks)} 个块")
            
            # 生成 UUID 格式的 ID
            ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
            self.vector_store.add_documents(documents=chunks, ids=ids)
            
            return {
                "status": "success", 
                "message": f"成功添加 {len(chunks)} 个文档块",
                "document_count": len(docs),
                "chunk_count": len(chunks)
            }
        except Exception as e:
            self.logger.error(f"处理文档时出错: {e}")
            return {"error": str(e)}
    
    def __del__(self):
        """析构函数，清理临时资源"""
        if hasattr(self, 'is_temp_dir') and self.is_temp_dir and hasattr(self, 'storage_dir'):
            try:
                import shutil
                shutil.rmtree(self.storage_dir, ignore_errors=True)
                self.logger.info(f"已清理临时目录: {self.storage_dir}")
            except Exception as e:
                self.logger.error(f"清理临时目录时出错: {e}")
