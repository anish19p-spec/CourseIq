from types import SimpleNamespace

import rag_pipeline


def test_embedding_request_uses_supported_model(monkeypatch):
    requests = []

    def embed_content(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0, 0.0])])

    client = SimpleNamespace(models=SimpleNamespace(embed_content=embed_content))
    monkeypatch.setattr(rag_pipeline, "_get_genai_client", lambda: client)
    assert rag_pipeline._embed_text("Homework details") == [1.0, 0.0]
    assert requests == [{"model": "gemini-embedding-2", "contents": "Homework details"}]
