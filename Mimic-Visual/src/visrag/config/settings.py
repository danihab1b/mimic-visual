"""Pydantic settings for visrag."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    type: str = "web"
    urls: str = "./urls.txt"
    pdf_path: str | None = None
    local_path: str | None = None


class RenderConfig(BaseModel):
    engine: str = "cdp"
    tile_height: int = 8192
    viewport_width: int = 875
    wait_strategy: str = "network_idle"
    timeout_seconds: int = 30


class OCRConfig(BaseModel):
    engine: str = "surya"
    language: str = "auto"
    batch_size: int = 4


class AlignmentConfig(BaseModel):
    method: str = "needleman_wunsch"
    gap_penalty: int = -1
    match_bonus: int = 2
    mismatch_penalty: int = -1
    html_confidence_bonus: float = 0.1


class ExtractConfig(BaseModel):
    ocr: OCRConfig = OCRConfig()
    alignment: AlignmentConfig = AlignmentConfig()
    table_detection: bool = True
    layout_analysis: bool = True


class ChunkConfig(BaseModel):
    strategy: str = "geometric"
    chunk_height: int = 1024
    overlap_px: int = 0


class EmbedConfig(BaseModel):
    model: str = "text-only"
    model_name: str = "BAAI/bge-small-en-v1.5"
    device: str = "cpu"
    batch_size: int = 32
    max_seq_length: int = 512


class IndexConfig(BaseModel):
    type: str = "faiss"
    metric: str = "cosine"
    nlist: int = 128
    nprobe: int = 128
    pq: bool = False
    pq_m: int = 64


class ServeConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 30001
    reconstruct: bool = True
    max_results: int = 20
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class ReconstructConfig(BaseModel):
    default_format: str = "html"
    include_metadata: bool = True
    inline_styles: bool = True


class VisRAGConfig(BaseModel):
    source: SourceConfig = SourceConfig()
    render: RenderConfig = RenderConfig()
    extract: ExtractConfig = ExtractConfig()
    chunk: ChunkConfig = ChunkConfig()
    embed: EmbedConfig = EmbedConfig()
    index: IndexConfig = IndexConfig()
    serve: ServeConfig = ServeConfig()
    reconstruct: ReconstructConfig = ReconstructConfig()

    @classmethod
    def from_yaml(cls, path: str | Path) -> VisRAGConfig:
        p = Path(path)
        if not p.exists():
            return cls()
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)
