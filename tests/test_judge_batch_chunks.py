"""Batch input files: one model each, and small enough to upload.

Both constraints come from real rejections. The API refuses a file that mixes
models ("Each batch must contain requests for a single model"), and our lines
interleave committee members criterion by criterion, so every file mixed them.
Separately, judge prompts embed the full answer under review (~30 KB), so
21,664 votes came to 656 MB in a single file.
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import judge_committee_batch as batch  # noqa: E402


def line(model: str, filler: int = 10) -> dict:
    return {"custom_id": f"c-{filler}", "method": "POST", "url": "/v1/responses",
            "body": {"model": model, "input": "x" * filler}}


def models_in(path: pathlib.Path) -> set[str]:
    return {json.loads(l)["body"]["model"] for l in path.read_text().splitlines()}


def test_each_chunk_holds_exactly_one_model(tmp_path):
    # interleaved exactly as collect_jobs emits them: judge by judge, per criterion
    lines = [line(m) for _ in range(50) for m in ("gpt-5.6-luna", "gpt-5.6-terra")]
    chunks = batch.write_chunks(lines, tmp_path)

    assert chunks, "no chunk written"
    for chunk in chunks:
        assert len(models_in(chunk)) == 1, f"{chunk.name} mixes models"
    assert {m for c in chunks for m in models_in(c)} == {"gpt-5.6-luna", "gpt-5.6-terra"}
    total = sum(len(c.read_text().splitlines()) for c in chunks)
    assert total == len(lines), "lines lost while chunking"


def test_chunks_respect_the_size_ceiling(tmp_path, monkeypatch):
    monkeypatch.setattr(batch, "MAX_CHUNK_BYTES", 4096)
    chunks = batch.write_chunks([line("m", filler=1000) for _ in range(20)], tmp_path)

    assert len(chunks) > 1, "oversized input was not split"
    for chunk in chunks:
        assert chunk.stat().st_size <= 4096 + 1200  # one line may straddle the mark


def test_chunk_filenames_stay_unique_across_models(tmp_path):
    lines = [line(m) for m in ("a", "b", "c") for _ in range(5)]
    chunks = batch.write_chunks(lines, tmp_path)
    assert len({c.name for c in chunks}) == len(chunks)
