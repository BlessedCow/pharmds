from __future__ import annotations

import difflib
import re
import sqlite3
import sys
from pathlib import Path

from core.exceptions import UnknownDrugError


def _normalize_drug_lookup_term(value: str) -> str:
    term = (value or "").strip().lower()
    term = re.sub(r"[\s_/\-]+", " ", term)
    return term.strip()


def _parse_drug_tokens(text: str) -> list[str]:
    """Parse drug tokens from free-form text.

    Supports:
    - one drug per line
    - comma-separated lists
    - whitespace-separated lists
    - comments starting with '#'
    """
    out: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        line = line.replace(",", " ")
        out.extend([part for part in line.split() if part])

    return out


def _read_drug_tokens_from_file(path: str) -> list[str]:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise SystemExit(f"--file not found: {p}") from e
    return _parse_drug_tokens(text)


def _read_drug_tokens_from_stdin() -> list[str]:
    return _parse_drug_tokens(sys.stdin.read())


def _collect_drug_inputs(
    positional: list[str] | None,
    file_paths: list[str] | None,
) -> list[str]:
    """Collect drug names from positional args, one/more files, and/or stdin.

    Rules:
    - If --file is provided, read each file ("-" means stdin).
    - Positional args are appended after file inputs.
    - If neither positional nor --file is given, and stdin is not a TTY,
      read from stdin (pipe-friendly default).
    """
    drugs: list[str] = []

    file_paths = file_paths or []
    if file_paths:
        for file_path in file_paths:
            if file_path == "-":
                drugs.extend(_read_drug_tokens_from_stdin())
            else:
                drugs.extend(_read_drug_tokens_from_file(file_path))
    elif not (positional or []) and not sys.stdin.isatty():
        drugs.extend(_read_drug_tokens_from_stdin())

    drugs.extend(positional or [])

    seen: set[str] = set()
    out: list[str] = []
    for drug in drugs:
        cleaned = drug.strip()
        if not cleaned:
            continue

        key = cleaned.lower()
        if key in seen:
            continue

        seen.add(key)
        out.append(cleaned)

    return out


def resolve_drug_ids(conn: sqlite3.Connection, names: list[str]) -> list[str]:
    out: list[str] = []
    unknown: list[str] = []
    lookup = _fetch_drug_lookup(conn)
    seen_drug_ids: set[str] = set()

    for raw in names:
        q = _normalize_drug_lookup_term(raw)
        drug_id = lookup.get(q)
        if drug_id:
            if drug_id in seen_drug_ids:
                continue
            seen_drug_ids.add(drug_id)
            out.append(drug_id)
            continue

        unknown.append(raw)

    if unknown:
        known_terms = _fetch_known_drug_terms(conn)
        suggestion_map = {}
        for token in unknown:
            suggestions = _suggest_drug_terms(token, known_terms, limit=5)
            if suggestions:
                suggestion_map[token] = suggestions
        raise UnknownDrugError(unknown, suggestions=suggestion_map)

    return out


def _fetch_known_drug_terms(conn: sqlite3.Connection) -> list[str]:
    """Return known generic names and aliases users might type."""
    terms: list[str] = []

    rows = conn.execute("SELECT generic_name FROM drug").fetchall()
    for row in rows:
        value = (row["generic_name"] or "").strip().lower()
        if value:
            terms.append(value)

    rows = conn.execute("SELECT alias FROM drug_alias").fetchall()
    for row in rows:
        value = (row["alias"] or "").strip().lower()
        if value:
            terms.append(value)

    seen = set()
    out = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            out.append(term)

    return out


def _fetch_drug_lookup(conn: sqlite3.Connection) -> dict[str, str]:
    lookup: dict[str, str] = {}

    rows = conn.execute("SELECT id, generic_name FROM drug ORDER BY id").fetchall()
    for row in rows:
        for term in (row["id"], row["generic_name"]):
            key = _normalize_drug_lookup_term(term)
            if key:
                lookup.setdefault(key, row["id"])

    rows = conn.execute(
        "SELECT drug_id, alias FROM drug_alias ORDER BY drug_id, alias"
    ).fetchall()
    for row in rows:
        key = _normalize_drug_lookup_term(row["alias"])
        if key:
            lookup.setdefault(key, row["drug_id"])

    return lookup


def _suggest_drug_terms(
    token: str,
    known_terms: list[str],
    limit: int = 5,
) -> tuple[str, ...]:
    """Suggest close matches for a token from known terms."""
    query = _normalize_drug_lookup_term(token)
    if not query:
        return tuple()

    display_by_normalized: dict[str, str] = {}
    for term in known_terms:
        key = _normalize_drug_lookup_term(term)
        if key:
            display_by_normalized.setdefault(key, term)

    matches = difflib.get_close_matches(
        query,
        list(display_by_normalized),
        n=limit,
        cutoff=0.6,
    )
    return tuple(display_by_normalized[match] for match in matches)


def _format_unknown_drug_message(
    token: str,
    suggestions: tuple[str, ...],
) -> str:
    if suggestions:
        return f"Drug '{token}' was not found. Did you mean: {', '.join(suggestions)}?"

    return (
        f"Drug '{token}' was not found. Check the spelling, or try a generic "
        "name or known brand name."
    )