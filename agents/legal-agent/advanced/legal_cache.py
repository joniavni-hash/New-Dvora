#!/usr/bin/env python3
"""
Legal Cache — Smart caching and retrieval system for Masha Advanced.
Implements retrieval-first strategy: search before generate.
"""

import json
import hashlib
import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path


CACHE_DIR = Path(os.path.expanduser("~/.openclaw/workspace/agents/legal-agent/cache"))
TEMPLATES_DIR = Path(os.path.expanduser("~/.openclaw/workspace/agents/legal-agent/templates"))
PRECEDENTS_DIR = Path(os.path.expanduser("~/.openclaw/workspace/agents/legal-agent/precedents"))


@dataclass
class CacheEntry:
    """A cached legal analysis result."""
    cache_key: str
    task_type: str
    document_hash: str       # Hash of the input document
    query_hash: str          # Hash of the query/message
    result: Dict             # The full analysis result
    model_tier: str          # Which tier produced this
    cost_usd: float          # What it cost
    created_at: float        # Unix timestamp
    ttl_hours: int = 168     # Default: 1 week
    hit_count: int = 0       # How many times this was retrieved
    tags: List[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.created_at + (self.ttl_hours * 3600)


@dataclass
class TemplateLookup:
    """A matched template for retrieval-first strategy."""
    template_id: str
    template_type: str       # contract_type, clause_type, etc.
    description: str
    content: str
    relevance_score: float   # 0-1
    source: str              # "template" | "precedent" | "playbook"


class LegalCache:
    """
    Manages caching for legal analyses and retrieval of templates/precedents.
    
    Cache hierarchy:
    1. Exact match (same document + same query)
    2. Similar query match (same document, similar query)
    3. Template match (similar document type, relevant template)
    4. Precedent match (similar contract type/clause)
    """

    def __init__(self):
        # Ensure directories exist
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        PRECEDENTS_DIR.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # CACHE OPERATIONS
    # ============================================================

    def get(self, task_type: str, message: str, document_text: Optional[str] = None) -> Optional[CacheEntry]:
        """
        Look up a cached result.
        Returns None if not found or expired.
        """
        cache_key = self._make_cache_key(task_type, message, document_text)
        cache_file = CACHE_DIR / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text())
            entry = CacheEntry(**data)
            if entry.is_expired:
                cache_file.unlink(missing_ok=True)
                return None
            # Update hit count
            entry.hit_count += 1
            cache_file.write_text(json.dumps(asdict(entry), ensure_ascii=False, indent=2))
            return entry
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def put(
        self,
        task_type: str,
        message: str,
        document_text: Optional[str],
        result: Dict,
        model_tier: str,
        cost_usd: float,
        tags: List[str] = None,
        ttl_hours: int = 168,
    ) -> str:
        """
        Store an analysis result in cache.
        Returns the cache key.
        """
        cache_key = self._make_cache_key(task_type, message, document_text)
        doc_hash = self._hash_text(document_text) if document_text else "no_doc"
        query_hash = self._hash_text(message)

        entry = CacheEntry(
            cache_key=cache_key,
            task_type=task_type,
            document_hash=doc_hash,
            query_hash=query_hash,
            result=result,
            model_tier=model_tier,
            cost_usd=cost_usd,
            created_at=time.time(),
            ttl_hours=ttl_hours,
            hit_count=0,
            tags=tags or [],
        )

        cache_file = CACHE_DIR / f"{cache_key}.json"
        cache_file.write_text(json.dumps(asdict(entry), ensure_ascii=False, indent=2))
        return cache_key

    def invalidate(self, cache_key: str) -> bool:
        """Remove a specific cache entry."""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False

    def cleanup_expired(self) -> int:
        """Remove all expired cache entries. Returns count removed."""
        removed = 0
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                data = json.loads(cache_file.read_text())
                entry = CacheEntry(**data)
                if entry.is_expired:
                    cache_file.unlink()
                    removed += 1
            except (json.JSONDecodeError, TypeError, KeyError):
                cache_file.unlink()
                removed += 1
        return removed

    def stats(self) -> Dict:
        """Get cache statistics."""
        entries = list(CACHE_DIR.glob("*.json"))
        total_cost_saved = 0.0
        total_hits = 0
        by_type = {}

        for f in entries:
            try:
                data = json.loads(f.read_text())
                task_type = data.get("task_type", "unknown")
                hits = data.get("hit_count", 0)
                cost = data.get("cost_usd", 0)
                total_hits += hits
                total_cost_saved += cost * hits  # Each hit saves the original cost
                by_type[task_type] = by_type.get(task_type, 0) + 1
            except (json.JSONDecodeError, KeyError):
                pass

        return {
            "total_entries": len(entries),
            "total_hits": total_hits,
            "estimated_cost_saved_usd": round(total_cost_saved, 4),
            "by_task_type": by_type,
        }

    # ============================================================
    # RETRIEVAL-FIRST: Templates & Precedents
    # ============================================================

    def search_templates(self, task_type: str, context_keywords: List[str]) -> List[TemplateLookup]:
        """
        Search for relevant templates based on task type and keywords.
        Used before invoking expensive models.
        """
        results = []

        for template_file in TEMPLATES_DIR.glob("*.md"):
            content = template_file.read_text()
            # Simple keyword matching — in production, use embeddings
            relevance = self._score_relevance(content, context_keywords)
            if relevance > 0.3:
                results.append(TemplateLookup(
                    template_id=template_file.stem,
                    template_type=task_type,
                    description=self._extract_first_line(content),
                    content=content,
                    relevance_score=relevance,
                    source="template",
                ))

        for precedent_file in PRECEDENTS_DIR.glob("*.md"):
            content = precedent_file.read_text()
            relevance = self._score_relevance(content, context_keywords)
            if relevance > 0.3:
                results.append(TemplateLookup(
                    template_id=precedent_file.stem,
                    template_type=task_type,
                    description=self._extract_first_line(content),
                    content=content,
                    relevance_score=relevance,
                    source="precedent",
                ))

        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:5]  # Top 5

    def search_similar_analyses(self, task_type: str, keywords: List[str]) -> List[CacheEntry]:
        """
        Find cached analyses similar to the current request.
        Even if not exact match, can provide context for the model.
        """
        results = []
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                data = json.loads(cache_file.read_text())
                if data.get("task_type") != task_type:
                    continue
                entry = CacheEntry(**data)
                if entry.is_expired:
                    continue
                # Check tag overlap
                tag_overlap = len(set(entry.tags) & set(keywords))
                if tag_overlap > 0:
                    results.append((tag_overlap, entry))
            except (json.JSONDecodeError, TypeError, KeyError):
                continue

        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results[:3]]

    def build_retrieval_context(self, task_type: str, message: str, document_text: Optional[str] = None) -> Dict:
        """
        Build retrieval context to prepend to model prompts.
        This is the key to making Opus a "refiner" instead of "generator from scratch".
        
        Returns:
            {
                "has_context": bool,
                "templates": [...],
                "precedents": [...],
                "similar_analyses": [...],
                "context_summary": str,
            }
        """
        # Extract keywords from message and document
        keywords = self._extract_keywords(message, document_text)

        templates = self.search_templates(task_type, keywords)
        similar = self.search_similar_analyses(task_type, keywords)

        has_context = len(templates) > 0 or len(similar) > 0

        context_parts = []
        if templates:
            context_parts.append(f"Found {len(templates)} relevant template(s)")
        if similar:
            context_parts.append(f"Found {len(similar)} similar prior analysis/analyses")

        return {
            "has_context": has_context,
            "templates": [
                {"id": t.template_id, "description": t.description, "content": t.content[:2000], "source": t.source}
                for t in templates
            ],
            "similar_analyses": [
                {"task_type": s.task_type, "tags": s.tags, "result_summary": self._summarize_result(s.result)}
                for s in similar
            ],
            "context_summary": "; ".join(context_parts) if context_parts else "No prior context found",
        }

    # ============================================================
    # STORE PRECEDENTS
    # ============================================================

    def store_precedent(self, precedent_id: str, content: str, tags: List[str] = None) -> str:
        """Store a new precedent for future retrieval."""
        path = PRECEDENTS_DIR / f"{precedent_id}.md"

        # Add metadata header
        header = f"<!-- tags: {','.join(tags or [])} -->\n<!-- stored: {time.strftime('%Y-%m-%d')} -->\n\n"
        path.write_text(header + content)
        return str(path)

    def store_template(self, template_id: str, content: str) -> str:
        """Store a new template for future retrieval."""
        path = TEMPLATES_DIR / f"{template_id}.md"
        path.write_text(content)
        return str(path)

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    def _make_cache_key(self, task_type: str, message: str, document_text: Optional[str]) -> str:
        """Create a cache key from task type + message + document."""
        combined = f"{task_type}:{message}:{document_text or ''}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _hash_text(self, text: str) -> str:
        """Hash text content."""
        return hashlib.sha256(text.encode()).hexdigest()[:12]

    def _score_relevance(self, content: str, keywords: List[str]) -> float:
        """Simple keyword-based relevance scoring."""
        if not keywords:
            return 0.0
        content_lower = content.lower()
        matches = sum(1 for kw in keywords if kw.lower() in content_lower)
        return matches / len(keywords)

    def _extract_first_line(self, content: str) -> str:
        """Extract first non-empty, non-comment line as description."""
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("<!--") and not line.startswith("#"):
                return line[:100]
            if line.startswith("# "):
                return line[2:100]
        return "Untitled"

    def _extract_keywords(self, message: str, document_text: Optional[str]) -> List[str]:
        """Extract keywords for search."""
        import re
        combined = f"{message} {(document_text or '')[:500]}"
        # Simple: split on non-word chars, filter short words
        words = re.findall(r'[\w\u0590-\u05FF]{3,}', combined)
        # Deduplicate preserving order
        seen = set()
        keywords = []
        for w in words:
            w_lower = w.lower()
            if w_lower not in seen:
                seen.add(w_lower)
                keywords.append(w_lower)
        return keywords[:20]

    def _summarize_result(self, result: Dict) -> str:
        """Create a brief summary of a cached result."""
        draft = result.get("draft", {})
        content = draft.get("content", "")
        if content:
            # First 200 chars
            return content[:200] + "..."
        return str(result.get("decision", "unknown"))


def test_cache():
    """Test cache operations."""
    cache = LegalCache()

    # Store a result
    key = cache.put(
        task_type="contract_review",
        message="תסכמי חוזה",
        document_text="This is a test contract with liability clauses.",
        result={"decision": "analysis", "draft": {"type": "contract_review", "content": "Test analysis"}},
        model_tier="tier1",
        cost_usd=0.05,
        tags=["contract", "liability", "test"],
    )
    print(f"Stored cache key: {key}")

    # Retrieve
    entry = cache.get("contract_review", "תסכמי חוזה", "This is a test contract with liability clauses.")
    print(f"Retrieved: {entry is not None}")
    if entry:
        print(f"  Hit count: {entry.hit_count}")
        print(f"  Tier: {entry.model_tier}")

    # Stats
    stats = cache.stats()
    print(f"\nCache stats: {json.dumps(stats, indent=2)}")

    # Build retrieval context
    ctx = cache.build_retrieval_context("contract_review", "תסכמי חוזה")
    print(f"\nRetrieval context: has_context={ctx['has_context']}")
    print(f"  Summary: {ctx['context_summary']}")


if __name__ == "__main__":
    test_cache()
