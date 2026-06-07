from app.services.embedding_service import HashEmbeddingProvider, build_embedding_provider


def test_hash_embedding_provider_returns_stable_dimensions() -> None:
    provider = HashEmbeddingProvider(dimensions=32)

    vectors = provider.embed_texts(["battery sag", "remaining useful life"])

    assert len(vectors) == 2
    assert len(vectors[0]) == provider.dimensions
    assert vectors[0] == provider.embed_query("battery sag")
    assert all(isinstance(value, float) for value in vectors[0])


def test_build_embedding_provider_supports_hash_for_tests() -> None:
    provider = build_embedding_provider(provider_name="hash", model_name="test", dimensions=16)

    assert provider.name == "hash"
    assert provider.dimensions == 16
