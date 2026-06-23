# mimic-visual
===============================================================================
  Mimic-Visual — Visual Document Retrieval & Reconstruction System
===============================================================================

GitHub: https://github.com/danihab1b/mimic-visual

Renders documents (web pages, PDFs, images) to screenshots, extracts text
from both HTML source and OCR, fuses them into a unified model, embeds for
vector search, and can reconstruct the visual page from retrieved chunks.


==============================================================================
  1. PREREQUISITES
==============================================================================

  • Docker Desktop (with docker compose CLI)
    - Windows: https://docs.docker.com/desktop/setup/install/windows-install/
    - macOS:   https://docs.docker.com/desktop/setup/install/mac-install/
    - Linux:   https://docs.docker.com/desktop/setup/install/linux/

  • At least 6 GB free disk space (image: ~4 GB + runtime data)

  • Git (to clone the repo)


==============================================================================
  2. GET THE PROJECT
==============================================================================

    git clone https://github.com/danihab1b/mimic-visual.git
    cd mimic-visual


==============================================================================
  3. QUICK START — FULL PIPELINE IN ONE COMMAND
==============================================================================

  3a. Prepare a list of URLs

      Create a file called urls.txt in the project root:

        echo "https://example.com" > urls.txt

      (one URL per line, or just test with a single URL)

  3b. Run the entire pipeline

        docker compose run --rm pipeline bash -c "
          visrag render /app/pages/urls.txt -o /app/pages &&
          visrag extract /app/pages &&
          visrag chunk /app/pages &&
          visrag embed /app/pages &&
          visrag index build -i /app/pages -o /app/index
        "

      Or use the Make shortcut:

        make pipeline

  3c. Start the API server

        docker compose up -d api

      Check it is alive:

        curl http://localhost:30001/health

      Expected response (HTTP 200):

        {"status":"ok","index_size":...}

  3d. Search

        curl -X POST http://localhost:30001/search \
          -H "Content-Type: application/json" \
          -d '{"query": {"text": "your search term"}, "n_results": 5}'

  3e. Stop the server

        docker compose down


==============================================================================
  4. CONFIGURATION
==============================================================================

  All pipeline settings are in visrag.yaml. The defaults work out of the box:

    render:
      engine: cdp                  # Browser engine (cdp | playwright)
      tile_height: 8192
      viewport_width: 875

    extract:
      ocr:
        engine: surya              # OCR backend (surya | doctr | easyocr)
        language: auto
      alignment:
        method: needleman_wunsch   # HTML ↔ OCR text alignment

    chunk:
      strategy: geometric          # Fixed-height slicing
      chunk_height: 1024

    embed:
      model: text-only
      model_name: BAAI/bge-small-en-v1.5   # Sentence-transformer model
      device: cpu

    index:
      type: faiss                  # Vector index
      metric: cosine

    serve:
      host: 0.0.0.0
      port: 30001

  See the full file at visrag.yaml for all available options.


==============================================================================
  5. DOCKER COMMANDS — QUICK REFERENCE
==============================================================================

  ┌────────────────────────┬────────────────────────────────────────────────┐
  │ Command                │ What it does                                  │
  ├────────────────────────┼────────────────────────────────────────────────┤
  │ make build             │ Build the Docker image                        │
  │ make up                │ Start the API server (detached)               │
  │ make down              │ Stop all containers                           │
  │ make logs              │ Tail server logs                              │
  │ make status            │ Show running containers                       │
  │ make pipeline          │ Full pipeline: render→extract→chunk→embed→idx │
  │ make shell             │ Open a dev shell inside the container         │
  │ make clean             │ Remove containers, volumes, and images        │
  │ make render SOURCE=... │ Run only the render step                      │
  │ make extract           │ Run only the extract step                     │
  │ make chunk             │ Run only the chunk step                       │
  │ make embed             │ Run only the embed step                       │
  │ make index-build       │ Run only the index build step                 │
  │ make index-info        │ Show index statistics                         │
  │ make reconstruct ID=   │ Reconstruct a chunk by its ID                 │
  └────────────────────────┴────────────────────────────────────────────────┘

  If you do not have Make, use the equivalent docker compose commands
  (see docker-compose.yml or the manual steps below).


==============================================================================
  6. MANUAL PIPELINE (STEP BY STEP)
==============================================================================

  Each step reads from and writes to directories under /app/pages inside the
  container. The pages/ and index/ directories on your host are mounted into
  the container automatically.

  6a. Render — capture screenshots and HTML from documents

        docker compose run --rm pipeline \
          visrag render /app/pages/urls.txt -o /app/pages

      Input:  urls.txt (list of URLs, one per line)
      Output: pages/page_XXX/  (tiles + HTML + metadata)

  6b. Extract — OCR + HTML fusion → Structured Document Model (SDM)

        docker compose run --rm pipeline \
          visrag extract /app/pages

      Input:  pages/page_XXX/
      Output: pages/page_XXX.extract/sdm.json

      This is the core command: it runs OCR on the rendered tiles, parses
      the HTML source, aligns both text streams with Needleman-Wunsch,
      resolves conflicts by confidence, and produces an SDM.

  6c. Chunk — split SDMs into fixed-height slices

        docker compose run --rm pipeline \
          visrag chunk /app/pages

      Input:  pages/page_XXX.extract/sdm.json
      Output: pages/page_XXX.chunks/chunks.json + chunk_XXXX.json

  6d. Embed — encode chunks into vectors

        docker compose run --rm pipeline \
          visrag embed /app/pages

      Input:  pages/page_XXX.chunks/*.json
      Output: pages/page_XXX.embeddings/embeddings.npz

  6e. Build index — create FAISS index + metadata store

        docker compose run --rm pipeline \
          visrag index build -i /app/pages -o /app/index

      Input:  pages/page_XXX.embeddings/
      Output: index/index.faiss + index/metadata_store/

  6f. Start the API server

        docker compose up -d api

      Then search via:

        curl -X POST http://localhost:30001/search \
          -H "Content-Type: application/json" \
          -d '{"query": {"text": "what you are looking for"}}'

  6g. Reconstruct a chunk

        docker compose run --rm pipeline \
          visrag reconstruct <chunk_id> --index-dir /app/index

      Or via the API:

        curl -X POST http://localhost:30001/reconstruct \
          -H "Content-Type: application/json" \
          -d '{"chunk_ids": ["<chunk_id>"], "format": "html"}'


==============================================================================
  7. API ENDPOINTS
==============================================================================

  GET /health
      Server health and index stats.

  POST /search
      Search by text. Returns ranked chunks with SDM data.
      Body:
        { "query": { "text": "search phrase" }, "n_results": 10 }

  POST /reconstruct
      Rebuild HTML/SVG/text from chunk IDs.
      Body:
        { "chunk_ids": ["id1", "id2"], "format": "html" }


==============================================================================
  8. TROUBLESHOOTING
==============================================================================

  Problem:  docker compose build fails on "pip install torch"
  Fix:      The CPU-only torch is ~800 MB. Ensure stable internet and retry.
            On first build, this step can take 5-10 minutes.

  Problem:  "playwright install" fails
  Fix:      Ensure the system has enough disk space (~300 MB for Chromium).
            Run docker compose build again — it will reuse cached layers.

  Problem:  curl http://localhost:30001/health returns "connection refused"
  Fix:      The container needs ~15 seconds to start. Wait and retry.
            Check logs: docker compose logs api

  Problem:  "visrag extract" takes a long time
  Fix:      First run downloads Surya OCR model weights (~200 MB).
            Subsequent runs use cached models. Lower batch_size in config
            if memory is constrained.

  Problem:  "visrag embed" downloads models every time
  Fix:      Sentence-transformer models are cached. If the container is
            recreated, they download again. Use the dev profile to persist
            the cache: docker compose --profile dev run --rm dev

  Problem:  No URLs processed
  Fix:      Make sure urls.txt exists in the project root and has at least
            one URL per line. Blank lines are skipped.

  Problem:  Pipeline step produces no output
  Fix:      Each step expects the previous step's output. Run steps in order:
            render → extract → chunk → embed → index build.

  Problem:  docker: command not found
  Fix:      Install Docker Desktop from https://www.docker.com/products/docker-desktop/


==============================================================================
  9. PROJECT STRUCTURE (KEY FILES)
==============================================================================

    mimic-visual/
    │
    ├── Dockerfile              # Multi-stage Docker build
    ├── docker-compose.yml      # Services: api, pipeline, dev
    ├── entrypoint.sh           # Container entry point (CLI router)
    ├── Makefile                # Convenience commands
    ├── pyproject.toml          # Python project config + dependencies
    ├── visrag.yaml             # Default pipeline configuration
    ├── urls.txt                # List of URLs to process (create this)
    │
    ├── pages/                  # Runtime: rendered pages + chunks
    ├── index/                  # Runtime: FAISS index + metadata
    │
    └── src/visrag/             # Source code
        ├── core/               # Data types (SDM, FusionBlock, Chunk, …)
        ├── sources/            # Document adapters (web, PDF, local, image)
        ├── render/             # Screenshot capture (Playwright, CDP)
        ├── extract/            # OCR + HTML fusion engine (the core)
        ├── chunk/              # SDM chunking
        ├── embed/              # Vector embedding (text-only, layout-aware)
        ├── index/              # FAISS index + metadata store
        ├── serve/              # FastAPI server (search + reconstruct)
        ├── reconstruct/        # SDM → HTML/SVG/text
        ├── config/             # Configuration loader
        └── cli/                # CLI entry points


==============================================================================
  10. PULLING UPDATES
==============================================================================

    git pull
    docker compose build api      # Rebuild image with latest code
    docker compose up -d api      # Restart server


==============================================================================
  License: MIT
==============================================================================
