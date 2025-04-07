import os
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredExcelLoader
# 修正导入模块名
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.chain_extract import LLMChainExtractor
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("BASE_URL")
model_api_key = os.getenv("MODEL_API_KEY")
model_name = os.getenv("MODEL_NAME")

embeddings_model = OpenAIEmbeddings(
    model="BAAI/nge-m3",
    api_key=model_api_key, #type: ignore
    base_url=base_url,
)   

llm = ChatOpenAI(
    base_url=base_url,
    api_key=model_api_key,  # 确保这个密钥是有效的
    model=model_name,  # type: ignore
    temperature=0.1,   # type: ignore
    max_tokens=1000,  # type: ignore
    streaming=True
)


class ChatDocHelper:
    def __init__(self):
        self.doc = None
        self.splitText = []    # List to store split text
        self.template = [
            ("system", "你是一个处理文件的助手，你可以帮助用户查找文件中的内容。你会根据下面的文件内容，回答用户的问题。\n 上下文：\n {context} \n "),
            ("human", "你好"),
            ("ai", "你好"),
            ("human", "{query}")
        ]
        self.prompt = ChatPromptTemplate.from_messages(self.template)
    
    def getFile(self):
        doc = self.doc
        loaders = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".doc": Docx2txtLoader,
            ".xls": UnstructuredExcelLoader,
            ".xlsx": UnstructuredExcelLoader,
        }
        # 检查 doc 是否为 None
        file_extension = doc.split(".")[-1]  #type: ignore
        print(f"File extension: {file_extension}")
        loader_class = loaders.get('.'+file_extension)
        print(f"Loader class: {loader_class}")  # 添加调试信息    
        if loader_class:
            print(f"Using loader: {loader_class.__name__}")  # 添加调试信息
            try:
                loader = loader_class(doc)
                text = loader.load()
                print(f"Loaded text===: {text}")  # 添加调试信息
                return text
            except Exception as e:
                print(f"Error loading file: {e}")
        else:
            print(f"Unsupported file format: {file_extension}")
            return None
    
     #处理文件文档
    def spliSentences(self):
         full_text = self.getFile()
         if full_text !=None:
            text_split = CharacterTextSplitter(
                chunk_size=150,  # Adjust chunk size as needed
                chunk_overlap=20,  # Adjust overlap as needed
            )
            texts = text_split.split_documents(full_text)
            self.splitText = texts
    
    # 向量化存储
    def embeddingAndVectorStore(self):
        db = Chroma.from_documents( #type: ignore
            self.splitText, 
            embedding=embeddings_model  #type: ignore
        )
        return db

    # 检索
    # def askAndFindFiles(self,query):
    #     db = self.embeddingAndVectorStore()
    #     retriever = db.as_retriever()
    #     results = retriever.invoke(query)
    #     return results

    # 多查询检索器
    # def askAndFindFiles(self,query):
    #     db = self.embeddingAndVectorStore()
    #     retriever_from_llm = MultiQueryRetriever.from_llm(
    #         retriever=db.as_retriever(), 
    #         llm=llm  #type: ignore
    #     )
    #     return retriever_from_llm.invoke(query)

     # 上下文压缩
    # def askAndFindFiles(self,query):
    #     db = self.embeddingAndVectorStore()
    #     retriever = db.as_retriever()
    #     compress = LLMChainExtractor.from_llm(
    #         llm=llm  #type: ignore
    #     )
    #     compress_retriever = ContextualCompressionRetriever(
    #         base_compressor=compress,
    #         base_retriever=retriever,
    #     )
    #     return compress_retriever.invoke(query)
 
    # 语义相似度 MMR 检索器
    def askAndFindFiles(self,query):
        db = self.embeddingAndVectorStore()
        retriever = db.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": 10, "score_threshold":.2})  # 调整 k 值以获取更多相关结果
        results = retriever.invoke(query)
        return results
    
    def chatWithFiles(self,query):
        _content = ""
        conset = self.askAndFindFiles(query)
        for i in conset:
            _content += i.page_content
        message = self.prompt.format_messages(context=_content, question=query) 
        strOut = ""
        for chunk in llm.stream(message):  #type: ignore
            strOut += chunk.content #type: ignore
            print(strOut)
    def getDocFile(self):
        loader = Docx2txtLoader("D:/devSpace/Learn-Langchain/serverless-core.docx")   
        text = loader.load()
        return text

    def getPdfFile(self):
        try:
            loader = PyPDFLoader("D:/devSpace/Learn-Langchain/serverless-core.pdf")
            text = loader.load()
            return text
        except Exception as e:
            print(f"Error loading PDF file: {e}")
            return None    


    def getXlstFile(self):
        try:
            loader = UnstructuredExcelLoader("D:/devSpace/Learn-Langchain/serverless-core.xls", mode="elements")
            text = loader.load()
            return text
        except Exception as e:
            print(f"Error loading PDF file: {e}")
            return None
        pass

chat_doc_helper = ChatDocHelper()
# 原代码尝试直接给doc属性赋值字符串，根据错误信息推测可能是类型不兼容
# 此处保留赋值操作，确保赋值类型与类中属性定义一致
chat_doc_helper.doc = "D:/devSpace/Learn-Langchain/serverless-core.pdf" #type: ignore
chat_doc_helper.spliSentences()
print(chat_doc_helper.splitText)
import logging
logging.basicConfig(level=logging.INFO)  # 设置日志级别为DEBUG
logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)  # 设置多查询检索器的日志级别为DEBUG
unique_doc = chat_doc_helper.askAndFindFiles("如何使用LangChain进行多查询检索？")
print(unique_doc)

