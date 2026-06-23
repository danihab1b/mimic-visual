"""Main CLI dispatcher — visrag <command>."""

from __future__ import annotations

import click

from visrag import __version__


@click.group()
@click.version_option(version=__version__, prog_name="visrag")
@click.option("--config", "-c", default="visrag.yaml", help="Config YAML path")
@click.pass_context
def cli(ctx, config: str):
    """Mimic-Visual: visual document retrieval and reconstruction."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


@cli.command("render")
@click.argument("source")
@click.option("--output", "-o", default="./pages", help="Output directory")
@click.option("--engine", default=None, help="Render engine (cdp|playwright)")
@click.option("--viewport-width", default=875, help="Viewport width in pixels")
@click.option("--tile-height", default=8192, help="Tile height in pixels")
@click.pass_context
def render_cmd(ctx, source: str, output: str, engine: str | None, viewport_width: int, tile_height: int):
    """Render documents to screenshot tiles + HTML."""
    from visrag.cli.render_cmd import run_render
    run_render(source, output, engine, viewport_width, tile_height, ctx.obj["config_path"])


@cli.command("extract")
@click.argument("pages_dir")
@click.option("--ocr-engine", default=None, help="OCR engine (surya|doctr|easyocr)")
@click.option("--language", default=None, help="OCR language")
@click.pass_context
def extract_cmd(ctx, pages_dir: str, ocr_engine: str | None, language: str | None):
    """Extract text via OCR -> align -> fuse -> build SDM."""
    from visrag.cli.extract_cmd import run_extract
    run_extract(pages_dir, ocr_engine, language, ctx.obj["config_path"])


@cli.command("chunk")
@click.argument("pages_dir")
@click.option("--height", default=1024, help="Chunk height in pixels")
@click.option("--overlap", default=0, help="Overlap in pixels")
@click.pass_context
def chunk_cmd(ctx, pages_dir: str, height: int, overlap: int):
    """Split SDMs into fixed-height chunks."""
    from visrag.cli.chunk_cmd import run_chunk
    run_chunk(pages_dir, height, overlap, ctx.obj["config_path"])


@cli.command("embed")
@click.argument("pages_dir")
@click.option("--model", default=None, help="Embedding model (text-only|layout-aware|hybrid)")
@click.option("--model-name", default=None, help="Model name")
@click.pass_context
def embed_cmd(ctx, pages_dir: str, model: str | None, model_name: str | None):
    """Encode chunks into vectors."""
    from visrag.cli.embed_cmd import run_embed
    run_embed(pages_dir, model, model_name, ctx.obj["config_path"])


@cli.group("index")
def index_group():
    """Build and inspect vector indexes."""
    pass


@index_group.command("build")
@click.option("--input", "-i", "input_dir", default="./pages", help="Pages directory")
@click.option("--output", "-o", default="./index", help="Index output directory")
@click.pass_context
def index_build_cmd(ctx, input_dir: str, output_dir: str):
    """Build FAISS index + metadata store."""
    from visrag.cli.index_cmd import run_index_build
    run_index_build(input_dir, output_dir, ctx.obj["config_path"])


@index_group.command("info")
@click.option("--index-dir", default="./index", help="Index directory")
def index_info_cmd(index_dir: str):
    """Show index statistics."""
    from visrag.cli.index_cmd import run_index_info
    run_index_info(index_dir)


@cli.command("serve")
@click.option("--index-dir", default="./index", help="Index directory")
@click.option("--host", default=None, help="Host")
@click.option("--port", default=None, type=int, help="Port")
@click.pass_context
def serve_cmd(ctx, index_dir: str, host: str | None, port: int | None):
    """Start the search API server."""
    from visrag.cli.serve_cmd import run_serve
    run_serve(index_dir, host, port, ctx.obj["config_path"])


@cli.command("reconstruct")
@click.argument("chunk_id")
@click.option("--format", "-f", "output_format", default="html", help="Output format (html|svg|text)")
@click.option("--index-dir", default="./index", help="Index directory")
@click.option("--output", "-o", default=None, help="Output file path")
def recon_cmd(chunk_id: str, output_format: str, index_dir: str, output: str | None):
    """Reconstruct HTML/SVG from a chunk ID."""
    from visrag.cli.recon_cmd import run_reconstruct
    run_reconstruct(chunk_id, output_format, index_dir, output)


if __name__ == "__main__":
    cli()
