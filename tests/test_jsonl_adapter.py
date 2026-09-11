from __future__ import annotations

from pathlib import Path

import pytest

from evalrepro.adapters.jsonl import jsonl_source
from evalrepro.errors import AdapterError
from evalrepro.manifest import build_manifest


def test_jsonl_adapter_ignores_blank_lines_and_tracks_source(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    path.write_text('{"id":"1","input":"a"}\n\n{"id":"2","input":"b"}\n')

    source = jsonl_source(path, name="demo")
    manifest = build_manifest(source)

    assert manifest["scope"]["identity"]["name"] == "demo"
    assert manifest["coverage"]["processed_count"] == 2
    assert manifest["provenance"]["source_line_numbers"] == [1, 3]
    assert len(manifest["provenance"]["file_sha256"]) == 64


def test_jsonl_adapter_reports_line_number(tmp_path: Path) -> None:
    path = tmp_path / "broken.jsonl"
    path.write_text('{"ok": true}\nnot-json\n')

    with pytest.raises(AdapterError, match=r"broken\.jsonl:2"):
        jsonl_source(path)


def test_jsonl_adapter_reports_missing_source(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"

    with pytest.raises(
        AdapterError,
        match=r"Cannot read JSONL source .*missing\.jsonl",
    ):
        jsonl_source(path)


def test_jsonl_adapter_reports_non_utf8_source(tmp_path: Path) -> None:
    path = tmp_path / "invalid_utf8.jsonl"
    path.write_bytes(b'{"id": "1", "input": "\xff\xfe"}\n')

    with pytest.raises(
        AdapterError,
        match=r"Cannot decode JSONL source .*invalid_utf8\.jsonl as UTF-8",
    ):
        jsonl_source(path)


def test_jsonl_adapter_handles_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text("")

    source = jsonl_source(path, name="empty-test")
    manifest = build_manifest(source)

    assert manifest["scope"]["identity"]["name"] == "empty-test"
    assert manifest["coverage"]["processed_count"] == 0
    assert manifest["provenance"]["source_line_numbers"] == []
    assert len(manifest["provenance"]["file_sha256"]) == 64


def test_jsonl_adapter_handles_whitespace_only_file(tmp_path: Path) -> None:
    path = tmp_path / "whitespace.jsonl"
    path.write_text("   \n\n\t  \n  \n")

    source = jsonl_source(path, name="whitespace-test")
    manifest = build_manifest(source)

    assert manifest["scope"]["identity"]["name"] == "whitespace-test"
    assert manifest["coverage"]["processed_count"] == 0
    assert manifest["provenance"]["source_line_numbers"] == []
    assert len(manifest["provenance"]["file_sha256"]) == 64


def test_jsonl_adapter_accepts_valid_scalar_lines(tmp_path: Path) -> None:
    path = tmp_path / "scalars.jsonl"
    path.write_text(sample string
42
true
3.14159
)

    source = jsonl_source(path, name="scalars-test")
    manifest = build_manifest(source)

    assert manifest["coverage"]["processed_count"] == 4
    assert manifest["provenance"]["source_line_numbers"] == [1, 2, 3, 4]
    assert len(manifest["provenance"]["file_sha256"]) == 64


def test_jsonl_adapter_ignores_blank_lines_around_scalar_records(tmp_path: Path) -> None:
    path = tmp_path / "spaced_scalars.jsonl"
    path.write_text("\n\n\"first_record\"\n\n\n100\n\n")

    source = jsonl_source(path, name="spaced-scalars")
    manifest = build_manifest(source)

    assert manifest["coverage"]["processed_count"] == 2
    assert manifest["provenance"]["source_line_numbers"] == [3, 6]
