from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize embeddings (same as demo1.py)
base_url = os.getenv("EB_BASE_URL")
model_api_key = os.getenv("EB_API_KEY")
model_name = os.getenv("EB_MODEL_NAME")

embeddings = OpenAIEmbeddings(
    model=model_name,
    api_key=model_api_key,
    base_url=base_url,
)

# Sample Chinese texts to embed and store
texts = [
    "床前明月光，疑是地上霜。",
    "举头望明月，低头思故乡。",
    "春眠不觉晓，处处闻啼鸟。",
    "夜来风雨声，花落知多少。"
]

# Create and save vector store
vectorstore = FAISS.from_texts(texts, embeddings)
vectorstore.save_local("faiss_chinese_poetry")

# Load vector store and perform similarity search
loaded_vectorstore = FAISS.load_local("faiss_chinese_poetry", embeddings)
results = loaded_vectorstore.similarity_search("月亮")

print("Similar poems about moon:")
for doc in results:
    print(doc.page_content)
