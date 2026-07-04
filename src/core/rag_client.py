"""
RAG (Retrieval-Augmented Generation) Client for PurpleOps

This module provides vector database functionality using ChromaDB to enhance
LLM responses with relevant historical context from:
- CVE database
- Past incidents
- Security policies
- Scan results
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "RAG dependencies not installed. Run: pip install chromadb sentence-transformers"
    )

logger = logging.getLogger(__name__)


class RAGClient:
    """
    RAG Client for vector-based knowledge retrieval
    
    Provides semantic search capabilities across multiple knowledge bases:
    - CVE vulnerabilities
    - Historical incidents
    - Security policies
    - Scan results
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize RAG client with ChromaDB and embedding model
        
        Args:
            persist_directory: Directory to persist vector database
            embedding_model: SentenceTransformer model name
        """
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize collections
        self._init_collections()
        
        logger.info("RAG Client initialized successfully")
    
    def _init_collections(self):
        """Initialize or get existing collections"""
        try:
            self.cve_collection = self.client.get_or_create_collection(
                name="cve_database",
                metadata={"description": "CVE vulnerabilities and details"}
            )
            
            self.incidents_collection = self.client.get_or_create_collection(
                name="incidents",
                metadata={"description": "Historical security incidents"}
            )
            
            self.policies_collection = self.client.get_or_create_collection(
                name="security_policies",
                metadata={"description": "Security policies and guidelines"}
            )
            
            self.scans_collection = self.client.get_or_create_collection(
                name="scan_results",
                metadata={"description": "Historical scan results"}
            )
            
            logger.info("All collections initialized")
            
        except Exception as e:
            logger.error(f"Error initializing collections: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    # ==================== CVE Operations ====================
    
    def add_cve(
        self,
        cve_id: str,
        description: str,
        cvss_score: float,
        severity: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add CVE to knowledge base
        
        Args:
            cve_id: CVE identifier (e.g., CVE-2024-0001)
            description: CVE description
            cvss_score: CVSS score
            severity: Severity level
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            # Create searchable text
            text = f"{cve_id} {description} Severity: {severity} CVSS: {cvss_score}"
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            # Prepare metadata
            meta = {
                "cve_id": cve_id,
                "cvss_score": cvss_score,
                "severity": severity,
                "added_at": datetime.now(timezone.utc).isoformat()
            }
            if metadata:
                meta.update(metadata)
            
            # Add to collection
            self.cve_collection.add(
                ids=[cve_id],
                embeddings=[embedding],
                documents=[description],
                metadatas=[meta]
            )
            
            logger.info(f"Added CVE: {cve_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding CVE {cve_id}: {e}")
            return False
    
    def search_similar_cves(
        self,
        query: str,
        n_results: int = 5,
        severity_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar CVEs using semantic search
        
        Args:
            query: Search query
            n_results: Number of results to return
            severity_filter: Filter by severity (critical, high, medium, low)
            
        Returns:
            List of similar CVEs with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Build where filter
            where = {}
            if severity_filter:
                where["severity"] = severity_filter
            
            # Search
            results = self.cve_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where if where else None
            )
            
            # Format results
            formatted_results = []
            if results and results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "cve_id": results['ids'][0][i],
                        "description": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.info(f"Found {len(formatted_results)} similar CVEs")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching CVEs: {e}")
            return []
    
    # ==================== Incident Operations ====================
    
    def add_incident(
        self,
        incident_id: str,
        description: str,
        severity: str,
        resolution: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add incident to knowledge base
        
        Args:
            incident_id: Incident identifier
            description: Incident description
            severity: Severity level
            resolution: How incident was resolved
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            # Create searchable text
            text = f"{incident_id} {description} Resolution: {resolution}"
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            # Prepare metadata
            meta = {
                "incident_id": incident_id,
                "severity": severity,
                "added_at": datetime.now(timezone.utc).isoformat()
            }
            if metadata:
                meta.update(metadata)
            
            # Add to collection
            self.incidents_collection.add(
                ids=[incident_id],
                embeddings=[embedding],
                documents=[f"{description}\n\nResolution: {resolution}"],
                metadatas=[meta]
            )
            
            logger.info(f"Added incident: {incident_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding incident {incident_id}: {e}")
            return False
    
    def search_similar_incidents(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar incidents
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of similar incidents with resolutions
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Search
            results = self.incidents_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results and results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "incident_id": results['ids'][0][i],
                        "description": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.info(f"Found {len(formatted_results)} similar incidents")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching incidents: {e}")
            return []
    
    # ==================== Policy Operations ====================
    
    def add_policy(
        self,
        policy_id: str,
        title: str,
        content: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add security policy to knowledge base
        
        Args:
            policy_id: Policy identifier
            title: Policy title
            content: Policy content
            category: Policy category
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            # Create searchable text
            text = f"{title} {content}"
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            # Prepare metadata
            meta = {
                "policy_id": policy_id,
                "title": title,
                "category": category,
                "added_at": datetime.now(timezone.utc).isoformat()
            }
            if metadata:
                meta.update(metadata)
            
            # Add to collection
            self.policies_collection.add(
                ids=[policy_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            
            logger.info(f"Added policy: {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding policy {policy_id}: {e}")
            return False
    
    def search_policies(
        self,
        query: str,
        n_results: int = 3,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search security policies
        
        Args:
            query: Search query
            n_results: Number of results to return
            category: Filter by category
            
        Returns:
            List of relevant policies
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Build where filter
            where = {}
            if category:
                where["category"] = category
            
            # Search
            results = self.policies_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where if where else None
            )
            
            # Format results
            formatted_results = []
            if results and results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "policy_id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.info(f"Found {len(formatted_results)} relevant policies")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching policies: {e}")
            return []
    
    # ==================== Scan Results Operations ====================
    
    def add_scan_result(
        self,
        scan_id: str,
        target: str,
        findings: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add scan result to knowledge base
        
        Args:
            scan_id: Scan identifier
            target: Scan target
            findings: Scan findings
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            # Create searchable text
            text = f"Target: {target} Findings: {findings}"
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            # Prepare metadata
            meta = {
                "scan_id": scan_id,
                "target": target,
                "added_at": datetime.now(timezone.utc).isoformat()
            }
            if metadata:
                meta.update(metadata)
            
            # Add to collection
            self.scans_collection.add(
                ids=[scan_id],
                embeddings=[embedding],
                documents=[findings],
                metadatas=[meta]
            )
            
            logger.info(f"Added scan result: {scan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding scan result {scan_id}: {e}")
            return False
    
    def search_scan_results(
        self,
        query: str,
        n_results: int = 5,
        target: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search historical scan results
        
        Args:
            query: Search query
            n_results: Number of results to return
            target: Filter by target
            
        Returns:
            List of relevant scan results
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Build where filter
            where = {}
            if target:
                where["target"] = target
            
            # Search
            results = self.scans_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where if where else None
            )
            
            # Format results
            formatted_results = []
            if results and results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "scan_id": results['ids'][0][i],
                        "findings": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.info(f"Found {len(formatted_results)} relevant scan results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching scan results: {e}")
            return []
    
    # ==================== Utility Methods ====================
    
    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics for all collections
        
        Returns:
            Dictionary with collection counts
        """
        try:
            stats = {
                "cves": self.cve_collection.count(),
                "incidents": self.incidents_collection.count(),
                "policies": self.policies_collection.count(),
                "scans": self.scans_collection.count()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def clear_collection(self, collection_name: str) -> bool:
        """
        Clear all data from a collection
        
        Args:
            collection_name: Name of collection to clear
            
        Returns:
            True if successful
        """
        try:
            self.client.delete_collection(collection_name)
            self._init_collections()
            logger.info(f"Cleared collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection {collection_name}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize RAG client
    rag = RAGClient()
    
    # Add sample CVE
    rag.add_cve(
        cve_id="CVE-2024-0001",
        description="SQL Injection vulnerability in login form",
        cvss_score=9.8,
        severity="critical",
        metadata={"cwe": "CWE-89"}
    )
    
    # Search for similar CVEs
    results = rag.search_similar_cves("SQL injection in authentication")
    logger.info(f"Found {len(results)} similar CVEs")
    
    # Get stats
    stats = rag.get_collection_stats()
    logger.info(f"Collection stats: {stats}")
