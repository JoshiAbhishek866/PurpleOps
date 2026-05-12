"""
ChromaDB-Based Knowledge Store for Sentinel AI

The data flywheel: every scan finding is embedded and stored.
Future scans query this store for relevant context via RAG.
This is the core moat — the system gets smarter with every use.

Fail-graceful: all methods return empty results if ChromaDB is unavailable.
"""

import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Lazy-loaded ChromaDB client
_client = None
_collection = None


def _get_collection(collection_name: str = "security_findings"):
    """Lazy-init ChromaDB collection. Returns None if unavailable."""
    global _client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        # Use persistent local storage (no server needed — cost-optimized)
        _client = chromadb.PersistentClient(path="./data/chromadb")
        _collection = _client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Sentinel AI security findings knowledge base"}
        )
        logger.info(f"✅ ChromaDB collection '{collection_name}' ready ({_collection.count()} documents)")
        return _collection
    except Exception as e:
        logger.warning(f"⚠️ ChromaDB unavailable: {e}. Knowledge store disabled.")
        return None


class KnowledgeStore:
    """
    Embeds and retrieves security findings using ChromaDB.

    Data Flywheel:
    1. After each campaign → store_finding() embeds results
    2. Before next campaign → query_relevant() retrieves similar past findings
    3. Agents get smarter context → better results → step 1 repeats
    """

    def __init__(self, collection_name: str = "security_findings"):
        self.collection_name = collection_name

    def _get_col(self):
        return _get_collection(self.collection_name)

    @staticmethod
    def _make_id(text: str) -> str:
        """Deterministic document ID from content."""
        return hashlib.md5(text.encode()).hexdigest()

    def store_finding(
        self,
        finding_text: str,
        metadata: Optional[Dict] = None,
        finding_id: Optional[str] = None,
    ) -> bool:
        """
        Embed and store a security finding.

        Args:
            finding_text: The textual content to embed (finding summary, attack result, etc.)
            metadata: Structured metadata (agent_type, target, campaign_id, severity, etc.)
            finding_id: Optional explicit ID. Auto-generated from content if not provided.
        """
        col = self._get_col()
        if not col or not finding_text.strip():
            return False

        doc_id = finding_id or self._make_id(finding_text)
        meta = metadata or {}
        meta["stored_at"] = datetime.utcnow().isoformat()

        # Ensure all metadata values are strings (ChromaDB requirement)
        clean_meta = {k: str(v) for k, v in meta.items() if v is not None}

        try:
            col.upsert(
                documents=[finding_text],
                metadatas=[clean_meta],
                ids=[doc_id],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store finding: {e}")
            return False

    def store_campaign_results(
        self,
        campaign_id: str,
        target: str,
        red_result: Dict,
        blue_result: Dict,
    ) -> int:
        """
        Store all results from a campaign (Red + Blue).
        Returns the number of documents stored.
        """
        stored = 0

        # Embed Red Agent findings
        red_text = self._extract_text(red_result, "Red Agent")
        if red_text and self.store_finding(
            finding_text=red_text,
            metadata={
                "campaign_id": campaign_id,
                "target": target,
                "agent_type": "red",
                "category": "attack_finding",
            }
        ):
            stored += 1

        # Embed Blue Agent findings
        blue_text = self._extract_text(blue_result, "Blue Agent")
        if blue_text and self.store_finding(
            finding_text=blue_text,
            metadata={
                "campaign_id": campaign_id,
                "target": target,
                "agent_type": "blue",
                "category": "defense_action",
            }
        ):
            stored += 1

        logger.info(f"Stored {stored} documents from campaign {campaign_id}")
        return stored

    def query_relevant(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Find the most relevant past findings for a given query.

        Args:
            query_text: What you're looking for (e.g., "SQL injection on /api/users")
            n_results: Max results to return
            filter_metadata: Optional ChromaDB where filter (e.g., {"agent_type": "red"})

        Returns:
            List of dicts with 'text', 'metadata', and 'distance' (lower = more relevant)
        """
        col = self._get_col()
        if not col or not query_text.strip():
            return []

        try:
            kwargs = {
                "query_texts": [query_text],
                "n_results": min(n_results, col.count() or 1),
            }
            if filter_metadata:
                kwargs["where"] = filter_metadata

            results = col.query(**kwargs)

            findings = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    findings.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else None,
                    })
            return findings
        except Exception as e:
            logger.error(f"Knowledge query failed: {e}")
            return []

    def build_rag_context(
        self,
        target: str,
        agent_type: str = "red",
        max_context_items: int = 5,
    ) -> Optional[str]:
        """
        Build a RAG context string for an agent's prompt.

        This is the key integration point: call this before running an agent
        and inject the result into the prompt.
        """
        findings = self.query_relevant(
            query_text=f"Security findings for {target}",
            n_results=max_context_items,
        )
        if not findings:
            return None

        lines = [f"=== Relevant Past Findings ({len(findings)} results) ==="]
        for f in findings:
            meta = f["metadata"]
            agent = meta.get("agent_type", "unknown")
            campaign = meta.get("campaign_id", "?")[:8]
            lines.append(f"\n[{agent.upper()} | Campaign {campaign}]")
            lines.append(f["text"][:300])
        lines.append("\n=== Use the above context to inform your strategy ===")

        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """Return knowledge store statistics."""
        col = self._get_col()
        if not col:
            return {"status": "unavailable"}
        return {
            "status": "active",
            "total_documents": col.count(),
            "collection_name": self.collection_name,
        }

    @staticmethod
    def _extract_text(result: Dict, agent_label: str) -> str:
        """Extract meaningful text from an agent result dict."""
        if not result:
            return ""
        parts = [f"{agent_label} Result:"]
        if isinstance(result, dict):
            for key in ["output", "simulated_result", "status", "attack_type", "mitigation"]:
                val = result.get(key)
                if val:
                    parts.append(f"  {key}: {str(val)[:200]}")
        else:
            parts.append(str(result)[:400])
        return "\n".join(parts) if len(parts) > 1 else ""
