"""Table detector — identifies table structure from aligned cell grid."""

from __future__ import annotations

from visrag.core.fusion import FusionBlock
from visrag.core.sdm import Table, TableCell


def detect_tables(blocks: list[FusionBlock], page_width: int, page_height: int) -> list[Table]:
    """Heuristic table detection from FusionBlocks with table_cell roles."""
    table_cells = [b for b in blocks if b.role == "table_cell"]
    if not table_cells:
        return []

    rows: dict[int, list[FusionBlock]] = {}
    for cell in table_cells:
        row_y = int(cell.bbox[1] // 5) * 5
        rows.setdefault(row_y, []).append(cell)

    sorted_rows = sorted(rows.items())
    tables = []
    current_cells: list[FusionBlock] = []
    prev_y = None

    for y, row_cells in sorted_rows:
        if prev_y is not None and y - prev_y > 40:
            if current_cells:
                table = _build_table(current_cells)
                if table:
                    tables.append(table)
            current_cells = []
        current_cells.extend(row_cells)
        prev_y = y

    if current_cells:
        table = _build_table(current_cells)
        if table:
            tables.append(table)

    return tables


def _build_table(cells: list[FusionBlock]) -> Table | None:
    if len(cells) < 2:
        return None

    rows: dict[int, list[FusionBlock]] = {}
    for cell in cells:
        row_y = int(cell.bbox[1] // 5) * 5
        rows.setdefault(row_y, []).append(cell)

    sorted_rows = sorted(rows.items())
    row_count = len(sorted_rows)
    col_count = max(len(row_cells) for _, row_cells in sorted_rows) if sorted_rows else 0

    if row_count < 2 or col_count < 2:
        return None

    table_cells = []
    for row_idx, (_, row_cells) in enumerate(sorted_rows):
        sorted_cells = sorted(row_cells, key=lambda c: c.bbox[0])
        for col_idx, cell in enumerate(sorted_cells):
            table_cells.append(TableCell(
                text=cell.text,
                bbox=cell.bbox,
                row=row_idx,
                col=col_idx,
                is_header=row_idx == 0,
                provenance=cell.provenance,
            ))

    x1 = min(c.bbox[0] for c in cells)
    y1 = min(c.bbox[1] for c in cells)
    x2 = max(c.bbox[2] for c in cells)
    y2 = max(c.bbox[3] for c in cells)

    return Table(
        cells=table_cells,
        bbox=(x1, y1, x2, y2),
        row_count=row_count,
        col_count=col_count,
    )
