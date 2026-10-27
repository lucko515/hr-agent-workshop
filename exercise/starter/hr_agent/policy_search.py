"""Tiny keyword search over the policy folder. No embeddings, no vector store.

For 9 short documents this is enough, and every result can be explained.
Each hit carries the title, version and effective date so the agent can cite it,
and so a human can see when two documents disagree.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

POLICY_DIR = Path(__file__).resolve().parent.parent / "policies"
STOPWORDS = set("a an and are as at be by do does for from how i in is it many much my of on or the to what when who with can".split())


@dataclass
class Section:
    doc_id: str
    title: str
    owner: str
    version: str
    effective: str
    heading: str
    text: str


def load_sections(policy_dir: Path = POLICY_DIR) -> list[Section]:
    sections: list[Section] = []
    for path in sorted(policy_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta: dict[str, str] = {}
        body = raw
        if raw.startswith("---"):
            _, front, body = raw.split("---", 2)
            for line in front.strip().splitlines():
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
        for chunk in re.split(r"\n(?=## )", body):
            chunk = chunk.strip()
            if not chunk.startswith("## "):
                continue
            heading, _, text = chunk.partition("\n")
            sections.append(Section(
                doc_id=path.stem, title=meta.get("title", path.stem), owner=meta.get("owner", "unknown"),
                version=meta.get("version", "?"), effective=meta.get("effective", "?"),
                heading=heading.removeprefix("## ").strip(), text=text.strip(),
            ))
    return sections


def _tokens(s: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", s.lower())
    return [w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words if w not in STOPWORDS]


def search(query: str, limit: int = 4, policy_dir: Path = POLICY_DIR) -> list[Section]:
    q = set(_tokens(query))
    scored = []
    for s in load_sections(policy_dir):
        body = _tokens(s.text)
        head = set(_tokens(f"{s.title} {s.heading}"))
        score = sum(min(body.count(t), 2) for t in q) + 3 * len(q & head)   # cap repeats so long sections do not win by volume
        if score:
            scored.append((score, s))
    scored.sort(key=lambda pair: -pair[0])
    return [s for _, s in scored[:limit]]
