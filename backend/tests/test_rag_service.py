from pathlib import Path

from app.services import rag_service
from app.services.rag_service import (
    InMemoryVectorStore,
    QdrantVectorStore,
    RagService,
    _chunk_markdown_sections,
)


def test_retrieves_relevant_manual_chunks_for_error_code() -> None:
    rag = RagService(
        domains_root=Path("app/domains"),
        vector_store=InMemoryVectorStore(),
    )
    report = rag.ingest_domain("drone_inspection")

    result = rag.search("drone_inspection", "What does E-204 mean?", limit=2)

    assert report.documents_indexed >= 2
    assert result.matches
    assert result.matches[0].score > 0
    assert "E-204" in result.matches[0].text
    assert result.matches[0].source_path.endswith(".md")


def test_search_returns_ranked_auditable_evidence() -> None:
    rag = RagService(
        domains_root=Path("app/domains"),
        vector_store=InMemoryVectorStore(),
    )
    rag.ingest_domain("nasa_cmapss_turbofan")

    result = rag.search("nasa_cmapss_turbofan", "RUL expected failure cycle", limit=2)

    assert [item.retrieval_rank for item in result.matches] == [1, 2]
    assert result.matches[0].chunk_id
    assert result.matches[0].embedding_provider == "hash"


def test_long_nasa_documents_are_split_into_multiple_chunks() -> None:
    rag = RagService(
        domains_root=Path("app/domains"),
        vector_store=InMemoryVectorStore(),
    )

    report = rag.ingest_domain("nasa_cmapss_turbofan")

    # Calibrated to current NASA fixtures so regressions away from meaningful
    # long-document chunking fail even before provenance/chunking work lands.
    assert report.chunks_indexed >= 16


def test_long_sections_are_split_with_section_titles_preserved(tmp_path) -> None:
    domains_root = tmp_path / "domains"
    document_dir = domains_root / "synthetic_long_section" / "documents"
    document_dir.mkdir(parents=True)
    repeated_phrase = "compressor stall warning signature"
    long_body = "\n".join(
        f"{repeated_phrase} cycle note {index} explains why overlap matters for retrieval."
        for index in range(80)
    )
    markdown_body = "\n".join(
        [
            "# Synthetic Long Section Manual",
            "",
            "## Long Section",
            long_body,
        ]
    )
    section_text = "\n".join(["## Long Section", long_body])
    chunk_chars = 400
    overlap_chars = 80
    (document_dir / "long_section.md").write_text(
        "\n".join(
            [
                "---",
                "title: Synthetic Long Section Manual",
                "source_label: Synthetic Test Source",
                "source_url: https://example.com/synthetic-long-section",
                "source_type: nasa",
                "---",
                markdown_body,
            ]
        ),
        encoding="utf-8",
    )
    rag = RagService(
        domains_root=domains_root,
        vector_store=InMemoryVectorStore(),
    )

    chunked_sections = [
        section
        for section in _chunk_markdown_sections(
            markdown_body,
            "Synthetic Long Section Manual",
            chunk_chars=chunk_chars,
            overlap_chars=overlap_chars,
        )
        if repeated_phrase in section.text.lower()
    ]
    report = rag.ingest_domain("synthetic_long_section")
    result = rag.search("synthetic_long_section", repeated_phrase, limit=4)

    assert report.documents_indexed == 1
    assert report.chunks_indexed >= 3
    assert len(chunked_sections) >= 2
    assert {section.section_title for section in chunked_sections} == {"Long Section"}
    assert all(section.text.strip() for section in chunked_sections)
    assert all(len(section.text) <= chunk_chars for section in chunked_sections)

    chunk_positions = [section_text.find(section.text) for section in chunked_sections]
    assert all(position >= 0 for position in chunk_positions)
    assert all(left < right for left, right in zip(chunk_positions, chunk_positions[1:]))

    edge_overlaps = []
    for left, right in zip(chunked_sections, chunked_sections[1:]):
        max_overlap = min(overlap_chars, len(left.text), len(right.text))
        overlap = 0
        for size in range(max_overlap, 0, -1):
            if left.text[-size:] == right.text[:size]:
                overlap = size
                break
        edge_overlaps.append(overlap)
    assert any(0 < overlap <= overlap_chars for overlap in edge_overlaps)

    assert result.matches
    assert any(
        item.section_title == "Long Section" and repeated_phrase in item.text.lower()
        for item in result.matches
    )


def test_chunk_markdown_sections_rejects_invalid_window_params() -> None:
    text = "## Long Section\ncompressor stall warning signature\n"

    for chunk_chars, overlap_chars in ((0, 0), (100, -1), (100, 100), (100, 120)):
        try:
            _chunk_markdown_sections(text, "Synthetic Long Section Manual", chunk_chars=chunk_chars, overlap_chars=overlap_chars)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Expected ValueError for chunk_chars={chunk_chars}, overlap_chars={overlap_chars}"
            )


def test_search_returns_source_backed_nasa_evidence_metadata() -> None:
    rag = RagService(
        domains_root=Path("app/domains"),
        vector_store=InMemoryVectorStore(),
    )
    rag.ingest_domain("nasa_cmapss_turbofan")

    result = rag.search(
        "nasa_cmapss_turbofan",
        "What does remaining useful life mean in FD001?",
        limit=2,
    )

    assert result.matches
    assert any(
        item.source_label
        and item.source_url.startswith("http")
        and item.source_type in {"nasa", "ntrs", "dataset"}
        and "remaining useful life" in item.text.lower()
        for item in result.matches
    )


def test_qdrant_collection_name_includes_vector_dimensions(monkeypatch) -> None:
    created_collections: list[str] = []

    class FakeQdrantClient:
        def __init__(self, url: str) -> None:
            self.url = url

        def collection_exists(self, collection_name: str) -> bool:
            return False

        def create_collection(self, collection_name: str, vectors_config) -> None:
            _ = vectors_config
            created_collections.append(collection_name)

    monkeypatch.setattr(rag_service, "QdrantClient", FakeQdrantClient)

    store = QdrantVectorStore(
        url="http://qdrant:6333",
        collection="physical_system_docs",
        vector_size=384,
        embedding_provider_name="fastembed",
        embedding_model_name="BAAI/bge-small-en-v1.5",
    )

    assert store.collection == "physical_system_docs_fastembed_baai_bge_small_en_v1_5_384"
    assert created_collections == ["physical_system_docs_fastembed_baai_bge_small_en_v1_5_384"]
