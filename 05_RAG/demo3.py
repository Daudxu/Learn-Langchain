from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize embeddings
base_url = os.getenv("EB_BASE_URL")
model_api_key = os.getenv("EB_API_KEY")
model_name = os.getenv("EB_MODEL_NAME")

embeddings = OpenAIEmbeddings(
    model=model_name,
    api_key=model_api_key,
    base_url=base_url,
)

# Sample game-related FAQs
texts = [
    "如何充值游戏币？",
    "如何联系客服？",
    "游戏中如何组队？",
    "如何提升角色等级？",
    "游戏支持哪些支付方式？"
]

# Create and save vector store
vectorstore = FAISS.from_texts(texts, embeddings)
vectorstore.save_local("faiss_game_faq")

# Load vector store and set up RetrievalQA
loaded_vectorstore = FAISS.load_local("faiss_game_faq", embeddings)
retriever = loaded_vectorstore.as_retriever()

qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(model_name=model_name, api_key=model_api_key, base_url=base_url),
    retriever=retriever
)

# Example user queries
queries = [
    "怎么充值？",
    "如何快速升级？",
    "游戏支持哪些支付方式？"
]

print("游戏智能客服 RAG 示例:")
for query in queries:
    response = qa_chain.run(query)
    print(f"用户问题: {query}")
    print(f"智能客服回答: {response}\n")

