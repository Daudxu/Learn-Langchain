# import os
# import pytest
# import requests
# import socket

# def get_embedding_provider():
#     provider = os.getenv("EMBEDDINGS_PROVIDER", "openai")
#     if provider == "ollama":
#         base_url = os.getenv("OLLAMA_BASE_URL")
#         model = os.getenv("OLLAMA_MODEL")
#         if not base_url or not model:
#             raise ValueError("Error in sub-node ‘Embeddings Ollama’")
#     return provider
    

# def get_ollama_base_url():
#     # 优先用环境变量
#     url = os.getenv("OLLAMA_BASE_URL")
#     if url:
#         return url
#     # 自动检测是否在 Docker 容器内
#     try:
#         socket.gethostbyname("host.docker.internal")
#         # 能解析，说明在容器内
#         return "http://host.docker.internal:11434"
#     except socket.error:
#         # 不能解析，说明在本机
#         return "http://localhost:11434"

# OLLAMA_BASE_URL = get_ollama_base_url()

# def get_bge_m3_embedding(text):
#     url = "http://localhost:11434/api/embeddings"
#     data = {
#         "model": "bge-m3:latest",
#         "prompt": text
#     }
#     response = requests.post(url, json=data)
#     response.raise_for_status()
#     return response.json()

# def test_ollama_embedding_error(monkeypatch):
#     # 模拟未配置 base_url 和 model
#     monkeypatch.setenv("EMBEDDINGS_PROVIDER", "ollama")
#     monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
#     monkeypatch.delenv("OLLAMA_MODEL", raising=False)
#     with pytest.raises(ValueError, match="Error in sub-node ‘Embeddings Ollama’"):
#         get_embedding_provider()

# def test_ollama_embedding_success(monkeypatch):
#     # 模拟已正确配置 base_url 和 model
#     monkeypatch.setenv("EMBEDDINGS_PROVIDER", "ollama")
#     monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
#     monkeypatch.setenv("OLLAMA_MODEL", "bge-m3:latest")
#     assert get_embedding_provider() == "ollama"

# def test_bge_m3_embedding():
#     result = get_bge_m3_embedding("你好，世界")
#     assert "embedding" in result
#     assert isinstance(result["embedding"], list)
#     print("Embedding length:", len(result["embedding"]))

# if __name__ == "__main__":
#     test_bge_m3_embedding()
