from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import yaml
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.models.schemas import DocumentIngestResponse, EvidenceItem
from app.services.domain_ids import safe_domain_dir
from app.services.embedding_service import EmbeddingProvider, HashEmbeddingProvider

TOKEN_RE = re.compile(r"[a-zA-Z0-9-]+")
# Default section windowing stays coarse enough to keep local embeddings cheap
# while still splitting long technical sections. Overlap intentionally repeats
# some text across adjacent chunks; later API/UI layers may dedupe near-duplicate
# evidence when that becomes user-visible.
SECTION_CHUNK_CHARS = 1200
SECTION_CHUNK_OVERLAP_CHARS = 200


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    domain_id: str
    source_path: str
    title: str
    section_title: str
    text: str
    vector: list[float]
    embedding_provider: str
    embedding_model: str
    source_label: str | None
    source_url: str | None
    source_urls: list[str]
    source_type: str | None
    source_authority: str | None


@dataclass(frozen=True)
class SearchResult:
    matches: list[EvidenceItem]


class VectorStore(Protocol):
    def upsert(self, chunks: list[DocumentChunk]) -> None: ...
    def search(self, domain_id: str, query: str, vector: list[float], limit: int) -> list[EvidenceItem]: ...


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []

    def upsert(self, chunks: list[DocumentChunk]) -> None:
        ids = {chunk.id for chunk in chunks}
        self._chunks = [chunk for chunk in self._chunks if chunk.id not in ids]
        self._chunks.extend(chunks)

    def search(self, domain_id: str, query: str, vector: list[float], limit: int) -> list[EvidenceItem]:
        query_terms = set(_tokens(query))
        scored = []
        for chunk in self._chunks:
            if chunk.domain_id != domain_id:
                continue
            term_overlap = len(query_terms & set(_tokens(chunk.text)))
            score = _cosine(vector, chunk.vector) + term_overlap
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            EvidenceItem(
                chunk_id=chunk.id,
                source_path=chunk.source_path,
                title=chunk.title,
                text=chunk.text,
                score=round(float(score), 4),
                section_title=chunk.section_title,
                source_label=chunk.source_label,
                source_url=chunk.source_url,
                source_urls=list(chunk.source_urls),
                source_type=chunk.source_type,
                source_authority=chunk.source_authority,
                retrieval_rank=index,
                embedding_provider=chunk.embedding_provider,
            )
            for index, (score, chunk) in enumerate(scored[:limit], start=1)
            if score > 0
        ]


class QdrantVectorStore:
    def __init__(
        self,
        url: str,
        collection: str,
        vector_size: int = 64,
        embedding_provider_name: str = "hash",
        embedding_model_name: str = "hash-64",
    ) -> None:
        self.client = QdrantClient(url=url)
        collection_suffix = _safe_collection_suffix(
            f"{embedding_provider_name}_{embedding_model_name}_{vector_size}"
        )
        self.collection = f"{collection}_{collection_suffix}"
        self.embedding_provider_name = embedding_provider_name
        self.embedding_model_name = embedding_model_name
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def upsert(self, chunks: list[DocumentChunk]) -> None:
        self.client.upsert(
            collection_name=self.collection,
            points=[
                PointStruct(
                    id=chunk.id,
                    vector=chunk.vector,
                    payload={
                        "domain_id": chunk.domain_id,
                        "source_path": chunk.source_path,
                        "title": chunk.title,
                        "section_title": chunk.section_title,
                        "text": chunk.text,
                        "embedding_provider": chunk.embedding_provider,
                        "embedding_model": chunk.embedding_model,
                        "source_label": chunk.source_label,
                        "source_url": chunk.source_url,
                        "source_urls": chunk.source_urls,
                        "source_type": chunk.source_type,
                        "source_authority": chunk.source_authority,
                    },
                )
                for chunk in chunks
            ],
        )

    def search(self, domain_id: str, query: str, vector: list[float], limit: int) -> list[EvidenceItem]:
        _ = query
        hits = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            limit=limit,
            query_filter=Filter(
                must=[FieldCondition(key="domain_id", match=MatchValue(value=domain_id))]
            ),
        ).points
        return [
            EvidenceItem(
                chunk_id=str(hit.id),
                source_path=str(hit.payload["source_path"]),
                title=str(hit.payload["title"]),
                text=str(hit.payload["text"]),
                score=round(float(hit.score), 4),
                section_title=str(hit.payload.get("section_title", hit.payload["title"])),
                source_label=_optional_string(hit.payload.get("source_label")),
                source_url=_optional_string(hit.payload.get("source_url")),
                source_urls=_coerce_string_list(hit.payload.get("source_urls")),
                source_type=_optional_string(hit.payload.get("source_type")),
                source_authority=_optional_string(hit.payload.get("source_authority")),
                retrieval_rank=index,
                embedding_provider=str(
                    hit.payload.get("embedding_provider", self.embedding_provider_name)
                ),
            )
            for index, hit in enumerate(hits, start=1)
            if hit.payload
        ]


class RagService:
    def __init__(
        self,
        domains_root: Path,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.domains_root = domains_root
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()

    def ingest_domain(self, domain_id: str) -> DocumentIngestResponse:
        domain_dir = safe_domain_dir(self.domains_root, domain_id)
        documents = sorted((domain_dir / "documents").glob("*.md"))
        chunks = [chunk for document in documents for chunk in self._chunks_for(domain_id, document)]
        self.vector_store.upsert(chunks)
        return DocumentIngestResponse(
            domain_id=domain_id,
            documents_indexed=len(documents),
            chunks_indexed=len(chunks),
        )

    def search(self, domain_id: str, query: str, limit: int = 4) -> SearchResult:
        safe_domain_dir(self.domains_root, domain_id)
        matches = self.vector_store.search(
            domain_id,
            query,
            self.embedding_provider.embed_query(query),
            limit,
        )
        return SearchResult(matches=matches)

    def _chunks_for(self, domain_id: str, path: Path) -> list[DocumentChunk]:
        domain_dir = safe_domain_dir(self.domains_root, domain_id)
        text = path.read_text(encoding="utf-8")
        metadata, markdown_body = _parse_markdown_document(text)
        title = str(
            metadata.get("title") or _title_from_markdown(markdown_body) or path.stem.replace("_", " ").title()
        )
        sections = _chunk_markdown_sections(markdown_body, title)
        chunks = []
        vectors = self.embedding_provider.embed_texts([section.text for section in sections])
        source_url = _optional_string(metadata.get("source_url"))
        source_urls = _expanded_source_urls(source_url, metadata.get("source_urls"))
        source_type = _normalize_source_type(
            _optional_string(metadata.get("source_type")),
            source_url,
            _optional_string(metadata.get("source_authority")),
        )
        for index, (section, vector) in enumerate(zip(sections, vectors, strict=True)):
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{domain_id}:{path}:{index}"))
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    domain_id=domain_id,
                    source_path=str(path.resolve().relative_to(domain_dir)),
                    title=title,
                    section_title=section.section_title,
                    text=section.text,
                    vector=vector,
                    embedding_provider=self.embedding_provider.name,
                    embedding_model=self.embedding_provider.model_name,
                    source_label=_optional_string(metadata.get("source_label")),
                    source_url=source_url,
                    source_urls=source_urls,
                    source_type=source_type,
                    source_authority=_optional_string(metadata.get("source_authority")),
                )
            )
        return chunks


def _title_from_markdown(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


@dataclass(frozen=True)
class MarkdownSection:
    section_title: str
    text: str


def _parse_markdown_document(text: str) -> tuple[dict[str, object], str]:
    stripped_text = text.lstrip("\ufeff\r\n\t ")
    if not stripped_text.startswith("---"):
        return {}, text
    lines = stripped_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            header_text = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :]).lstrip()
            try:
                parsed = yaml.safe_load(header_text) or {}
            except yaml.YAMLError:
                return {}, text
            if isinstance(parsed, dict):
                return parsed, body
            return {}, body
    return {}, text


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _safe_collection_suffix(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_").lower()


def _coerce_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _expanded_source_urls(source_url: str | None, value: object) -> list[str]:
    urls = _coerce_string_list(value)
    if source_url:
        return [url for url in urls if url != source_url]
    return urls


def _normalize_source_type(
    declared_type: str | None,
    source_url: str | None,
    source_authority: str | None,
) -> str | None:
    normalized_declared = (declared_type or "").strip().lower()
    if normalized_declared in {"nasa", "ntrs", "dataset"}:
        return normalized_declared

    primary_url = (source_url or "").lower()
    if "ntrs.nasa.gov" in primary_url:
        return "ntrs"
    if "dashlink" in primary_url or "nasa.gov" in primary_url:
        return "nasa"
    if normalized_declared == "curated_reference" and (source_authority or "").strip().lower().startswith("nasa"):
        return "nasa"
    return normalized_declared or None


def _chunk_markdown_sections(
    text: str,
    fallback_title: str,
    *,
    chunk_chars: int = SECTION_CHUNK_CHARS,
    overlap_chars: int = SECTION_CHUNK_OVERLAP_CHARS,
) -> list[MarkdownSection]:
    _validate_chunk_window(chunk_chars=chunk_chars, overlap_chars=overlap_chars)
    chunks: list[MarkdownSection] = []
    for section in _split_markdown_sections(text, fallback_title):
        chunks.extend(_split_section_with_overlap(section, chunk_chars=chunk_chars, overlap_chars=overlap_chars))
    return chunks


def _split_markdown_sections(text: str, fallback_title: str) -> list[MarkdownSection]:
    raw_sections = [section.strip() for section in re.split(r"\n(?=##\s+)", text) if section.strip()]
    sections: list[MarkdownSection] = []
    for section in raw_sections:
        section_title = fallback_title
        lines = section.splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                section_title = stripped[3:].strip() or fallback_title
                break
        sections.append(MarkdownSection(section_title=section_title, text=section))
    return sections


def _split_section_with_overlap(
    section: MarkdownSection,
    *,
    chunk_chars: int,
    overlap_chars: int,
) -> list[MarkdownSection]:
    if len(section.text) <= chunk_chars:
        return [section]

    chunks: list[MarkdownSection] = []
    start = 0
    text_length = len(section.text)
    while start < text_length:
        end = min(text_length, start + chunk_chars)
        if end < text_length:
            boundary = section.text.rfind("\n", start + 1, end)
            if boundary <= start:
                boundary = section.text.rfind(" ", start + 1, end)
            if boundary > start:
                end = boundary

        window = section.text[start:end].strip()
        if window:
            chunks.append(MarkdownSection(section_title=section.section_title, text=window))

        if end >= text_length:
            break

        next_start = max(end - overlap_chars, start + 1)
        while next_start < text_length and section.text[next_start].isspace():
            next_start += 1
        start = next_start

    return chunks


def _validate_chunk_window(*, chunk_chars: int, overlap_chars: int) -> None:
    if chunk_chars <= 0:
        raise ValueError("chunk_chars must be greater than 0")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be greater than or equal to 0")
    if overlap_chars >= chunk_chars:
        raise ValueError("overlap_chars must be smaller than chunk_chars")
