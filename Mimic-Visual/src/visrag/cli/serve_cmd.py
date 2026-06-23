"""visrag serve — start the search API server."""

from __future__ import annotations

from rich.console import Console

console = Console()


def run_serve(index_dir: str, host: str | None, port: int | None, config_path: str):
    from visrag.config.settings import VisRAGConfig
    config = VisRAGConfig.from_yaml(config_path)

    host = host or config.serve.host
    port = port or config.serve.port

    from visrag.embed.base import AbstractEmbedder
    from visrag.serve.api import create_app

    embedder = AbstractEmbedder.create(config.embed.model, model_name=config.embed.model_name)
    app = create_app(
        index_dir=index_dir,
        embedder=embedder,
        max_results=config.serve.max_results,
        cors_origins=config.serve.cors_origins,
    )

    import uvicorn
    console.print(f"[bold]Starting server on {host}:{port}[/]")
    uvicorn.run(app, host=host, port=port)
