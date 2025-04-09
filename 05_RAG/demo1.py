from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("EB_BASE_URL")
model_api_key = os.getenv("EB_API_KEY")
model_name = os.getenv("EB_MODEL_NAME")

embeddings_model = OpenAIEmbeddings(
    model=model_name,
    api_key=model_api_key,
    base_url=base_url,
)
embedding = embeddings_model.embed_documents(
    {
        "床前明月光，",
        "疑是地上霜。",
        "举头望明月，",
        "低头思故乡。"
    }
)
# len(embedding), len(embedding[0])

print(len(embedding))

print(len(embedding[0]))