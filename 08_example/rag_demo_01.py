import json
import gradio as gr

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.vectorstores.utils import filter_complex_metadata
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser



# 从模板创建提示
promptTemplate = """尽可能精确地使用提供的上下文回答问题。如果答案不在上下文中，请回答"上下文中没有可用的答案" \n\n
    Context: {context}
    Question: {question}
    Answer:

     """
modelSel = ""
# 将PDF文件加载到ChromaDB
def loadDataFromPDFFile(filePath):
    # 使用PyPDFLoader加载PDF文件
    loader = PyPDFLoader(filePath)
    # 加载并分割页面
    pages = loader.load_and_split()
    # 过滤复杂元数据
    chunks = filter_complex_metadata(pages)
    # 创建向量存储
    vector_store = Chroma.from_documents(documents=chunks, embedding=FastEmbedEmbeddings())
    return vector_store



def modelResponse(message , history):
    # 创建LLM模型实例
    llm = ChatOllama(model = conf["model"])

    # 创建提示模板
    prompt = PromptTemplate(template=promptTemplate , input_variables=["context","question"])

    # 初始化检索器
    dbLoaded = loadDataFromPDFFile("~/Desktop/hp/HP1.pdf")
    # 配置检索参数
    retriever = dbLoaded.as_retriever(search_type="similarity_score_threshold" , search_kwargs = {
        "k": 5,  # 返回前5个最相似的文档
        "score_threshold": 0.2  # 相似度阈值
    })
    # 构建RAG链
    hpChain = (
            {"context": retriever , "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )
    return hpChain.invoke(message)


if __name__ == "__main__":

    # 读取配置文件
    conf = {}
    with open("config.json" , "r") as confFile:
        conf = json.load(confFile)
        print(conf["model"])

    # 创建Gradio聊天界面
    chatUI = gr.ChatInterface(fn=modelResponse , title="Harry Potter Story Q&A")
    # 启动聊天界面
    chatUI.launch()


# {
# "model": "llama2"
# }