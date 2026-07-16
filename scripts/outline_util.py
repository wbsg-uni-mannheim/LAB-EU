"""Shared helpers for the per-case examination outline (Gliederung) tree.

The outline is stored in rubric.json as a list of nested nodes
{"id": "A.I", "label": "...", "children": [...]}; criteria reference a node
via analysis_tags.outline_id. "Ü" is the reserved id for cross-cutting
criteria (structure, form, citation style).
"""

from __future__ import annotations

from typing import Any

UE_ID = "Ü"
UE_LABEL = "Übergreifend"


def normalize_outline(nodes: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate and clean a model-returned outline tree; drop invalid nodes."""
    warnings: list[str] = []
    seen: set[str] = set()

    def clean(raw_nodes: Any) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        if not isinstance(raw_nodes, list):
            return result
        for raw in raw_nodes:
            if not isinstance(raw, dict):
                warnings.append(f"Dropped non-object outline node: {raw!r}")
                continue
            node_id = str(raw.get("id", "")).strip()
            label = str(raw.get("label", "")).strip()
            if not node_id or not label:
                warnings.append(f"Dropped outline node without id/label: {raw!r}")
                continue
            if node_id in seen:
                warnings.append(f"Dropped outline node with duplicate id {node_id!r}.")
                continue
            seen.add(node_id)
            node: dict[str, Any] = {
                "id": node_id,
                "label": label,
                "children": clean(raw.get("children") or []),
            }
            if raw.get("derived_label"):
                node["derived_label"] = True
            result.append(node)
        return result

    return clean(nodes), warnings


def with_ue_node(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if any(node["id"] == UE_ID for node in walk_ids(nodes)):
        return nodes
    return nodes + [{"id": UE_ID, "label": UE_LABEL, "children": []}]


def walk(
    nodes: list[dict[str, Any]], depth: int = 1, prefix: list[str] | None = None
):
    """Yield (node, depth, path_labels) in document order."""
    prefix = prefix or []
    for node in nodes:
        path = prefix + [node["label"]]
        yield node, depth, path
        yield from walk(node.get("children") or [], depth + 1, path)


def walk_ids(nodes: list[dict[str, Any]]):
    for node, _depth, _path in walk(nodes):
        yield node


def index_outline(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map node id -> {label, depth, path_labels, order}."""
    result: dict[str, dict[str, Any]] = {}
    for order, (node, depth, path) in enumerate(walk(nodes)):
        result[node["id"]] = {
            "label": node["label"],
            "depth": depth,
            "path_labels": path,
            "order": order,
        }
    return result
