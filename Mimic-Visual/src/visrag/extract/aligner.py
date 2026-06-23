"""Needleman-Wunsch character-level alignment."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class AlignmentResult:
    aligned_html: str
    aligned_ocr: str
    match_count: int
    mismatch_count: int
    gap_count: int
    score: float
    html_indices: list[int | None]  # maps alignment pos -> HTML char index (or None for gap)
    ocr_indices: list[int | None]   # maps alignment pos -> OCR char index (or None for gap)


def needleman_wunsch_align(
    html_text: str,
    ocr_text: str,
    match_bonus: int = 2,
    mismatch_penalty: int = -1,
    gap_penalty: int = -1,
) -> AlignmentResult:
    """Character-level global alignment between HTML and OCR text."""
    n = len(html_text)
    m = len(ocr_text)

    dp = np.zeros((n + 1, m + 1), dtype=np.int32)
    trace = np.zeros((n + 1, m + 1), dtype=np.int8)  # 0=diag, 1=up, 2=left

    for i in range(1, n + 1):
        dp[i][0] = i * gap_penalty
        trace[i][0] = 1
    for j in range(1, m + 1):
        dp[0][j] = j * gap_penalty
        trace[0][j] = 2

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if html_text[i - 1].lower() == ocr_text[j - 1].lower():
                diag = dp[i - 1][j - 1] + match_bonus
            else:
                diag = dp[i - 1][j - 1] + mismatch_penalty

            up = dp[i - 1][j] + gap_penalty
            left = dp[i][j - 1] + gap_penalty

            if diag >= up and diag >= left:
                dp[i][j] = diag
                trace[i][j] = 0
            elif up >= left:
                dp[i][j] = up
                trace[i][j] = 1
            else:
                dp[i][j] = left
                trace[i][j] = 2

    aligned_html_chars = []
    aligned_ocr_chars = []
    html_idx_list: list[int | None] = []
    ocr_idx_list: list[int | None] = []

    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and trace[i][j] == 0:
            aligned_html_chars.append(html_text[i - 1])
            aligned_ocr_chars.append(ocr_text[j - 1])
            html_idx_list.append(i - 1)
            ocr_idx_list.append(j - 1)
            i -= 1
            j -= 1
        elif i > 0 and trace[i][j] == 1:
            aligned_html_chars.append(html_text[i - 1])
            aligned_ocr_chars.append("-")
            html_idx_list.append(i - 1)
            ocr_idx_list.append(None)
            i -= 1
        else:
            aligned_html_chars.append("-")
            aligned_ocr_chars.append(ocr_text[j - 1])
            html_idx_list.append(None)
            ocr_idx_list.append(j - 1)
            j -= 1

    aligned_html_chars.reverse()
    aligned_ocr_chars.reverse()
    html_idx_list.reverse()
    ocr_idx_list.reverse()

    match_count = sum(1 for h, o in zip(aligned_html_chars, aligned_ocr_chars) if h == o and h != "-")
    mismatch_count = sum(1 for h, o in zip(aligned_html_chars, aligned_ocr_chars) if h != o and h != "-" and o != "-")
    gap_count = sum(1 for h, o in zip(aligned_html_chars, aligned_ocr_chars) if h == "-" or o == "-")

    return AlignmentResult(
        aligned_html="".join(aligned_html_chars),
        aligned_ocr="".join(aligned_ocr_chars),
        match_count=match_count,
        mismatch_count=mismatch_count,
        gap_count=gap_count,
        score=float(dp[n][m]),
        html_indices=html_idx_list,
        ocr_indices=ocr_idx_list,
    )


def alignment_quality(result: AlignmentResult) -> float:
    """Return alignment quality as a 0-1 score."""
    total = result.match_count + result.mismatch_count + result.gap_count
    if total == 0:
        return 0.0
    return result.match_count / total
