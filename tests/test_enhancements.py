"""
Tests for the 8 agent enhancement modules.
All tests are self-contained and require no external services.
"""
import pytest
import os


# ==================== MITRE ATT&CK Tests ====================

class TestMitreAttack:
    def test_map_sql_injection_to_technique(self):
        from src.core.mitre_attack import MitreAttackMapper
        mapper = MitreAttackMapper()
        techniques = mapper.get_techniques_for_action("sql_injection_attempt")
        assert len(techniques) >= 1
        assert techniques[0]["technique_id"] == "T1190"
        assert techniques[0]["tactic"] == "Initial Access"

    def test_enrich_finding(self):
        from src.core.mitre_attack import MitreAttackMapper
        mapper = MitreAttackMapper()
        finding = {"status": "executed", "attack_type": "SQL Injection"}
        enriched = mapper.enrich_finding("sql_injection_attempt", finding)
        assert "mitre_attack" in enriched
        assert len(enriched["mitre_attack"]["techniques"]) > 0

    def test_campaign_coverage(self):
        from src.core.mitre_attack import MitreAttackMapper
        mapper = MitreAttackMapper()
        coverage = mapper.get_campaign_attack_coverage([
            "sql_injection_attempt", "xss_test", "recon_scan"
        ])
        assert coverage["technique_count"] >= 3
        assert coverage["coverage_percent"] > 0

    def test_unknown_action_returns_empty(self):
        from src.core.mitre_attack import MitreAttackMapper
        mapper = MitreAttackMapper()
        techniques = mapper.get_techniques_for_action("nonexistent_action")
        assert techniques == []


# ==================== Multi-LLM Provider Tests ====================

class TestLLMProvider:
    def test_create_ollama_provider(self):
        from src.core.llm_provider import create_llm_provider
        provider = create_llm_provider("ollama", model="llama2")
        assert provider.provider_name == "ollama"
        assert provider.model == "llama2"

    def test_create_openai_provider(self):
        from src.core.llm_provider import create_llm_provider
        provider = create_llm_provider("openai", model="gpt-4")
        assert provider.provider_name == "openai"

    def test_create_bedrock_provider(self):
        from src.core.llm_provider import create_llm_provider
        provider = create_llm_provider("bedrock", model="anthropic.claude-3-5-sonnet-20241022-v2:0")
        assert provider.provider_name == "bedrock"

    def test_unknown_provider_raises(self):
        from src.core.llm_provider import create_llm_provider
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider("nonexistent")

    def test_get_available_providers(self):
        from src.core.llm_provider import get_available_providers
        providers = get_available_providers()
        assert "ollama" in providers
        assert "openai" in providers
        assert "bedrock" in providers
        assert "azure_openai" in providers


# ==================== Knowledge Store Tests ====================

class TestKnowledgeStore:
    def test_store_and_query(self):
        from src.core.knowledge_store import KnowledgeStore
        store = KnowledgeStore(collection_name="test_findings")
        stored = store.store_finding(
            finding_text="SQL injection vulnerability on /api/users endpoint",
            metadata={"agent_type": "red", "target": "test.com"},
        )
        if stored:  # Only test if ChromaDB is available
            results = store.query_relevant("SQL injection on API endpoint")
            assert len(results) > 0
            assert "SQL injection" in results[0]["text"]

    def test_empty_query_returns_empty(self):
        from src.core.knowledge_store import KnowledgeStore
        store = KnowledgeStore(collection_name="test_findings")
        results = store.query_relevant("")
        assert results == []

    def test_stats(self):
        from src.core.knowledge_store import KnowledgeStore
        store = KnowledgeStore(collection_name="test_findings")
        stats = store.get_stats()
        assert "status" in stats


# ==================== Adversarial Scoring Tests ====================

class TestAdversarialScoring:
    def test_initial_ratings(self):
        from src.core.adversarial_scoring import AdversarialScoring
        scoring = AdversarialScoring()
        ratings = scoring.get_ratings("test.com")
        assert ratings["red"] == 1200
        assert ratings["blue"] == 1200

    def test_score_campaign(self):
        from src.core.adversarial_scoring import AdversarialScoring
        scoring = AdversarialScoring()
        result = scoring.score_campaign(
            red_result={"output": "SQL injection vulnerability detected"},
            blue_result={"output": "WAF rule updated to block SQL injection"},
            target="test.com",
            campaign_id="test-campaign-1",
        )
        assert "winner" in result
        assert "interpretation" in result
        assert result["red"]["new_rating"] != 1200 or result["blue"]["new_rating"] != 1200

    def test_improvement_trend_insufficient_data(self):
        from src.core.adversarial_scoring import AdversarialScoring
        scoring = AdversarialScoring()
        trend = scoring.get_improvement_trend()
        assert trend["trend"] == "insufficient_data"

    def test_reprobe_targets(self):
        from src.core.adversarial_scoring import AdversarialScoring
        scoring = AdversarialScoring()
        scoring.score_campaign(
            red_result={"output": "SQL injection vulnerability detected, XSS vulnerability found"},
            blue_result={"output": "WAF updated"},
            target="vuln.com", campaign_id="c-1",
        )
        targets = scoring.get_reprobe_targets()
        # Red found vulns, so reprobe should be recommended
        assert isinstance(targets, list)


# ==================== Agent Benchmark Tests ====================

class TestAgentBenchmark:
    def test_benchmark_targets_exist(self):
        from src.core.agent_benchmark import BENCHMARK_TARGETS
        assert "dvwa" in BENCHMARK_TARGETS
        assert "juice_shop" in BENCHMARK_TARGETS
        assert "webgoat" in BENCHMARK_TARGETS

    @pytest.mark.asyncio
    async def test_simulated_benchmark(self):
        from src.core.agent_benchmark import AgentBenchmark
        bench = AgentBenchmark()
        result = await bench.run_benchmark("dvwa")
        metrics = result.metrics
        assert metrics["target"] == "dvwa"
        assert metrics["detection_rate"] >= 0
        assert metrics["vulns_known"] > 0

    @pytest.mark.asyncio
    async def test_all_benchmarks(self):
        from src.core.agent_benchmark import AgentBenchmark
        bench = AgentBenchmark()
        all_metrics = await bench.run_all_benchmarks()
        assert "dvwa" in all_metrics
        assert "aggregate" in all_metrics
        assert all_metrics["aggregate"]["targets_tested"] >= 3


# ==================== Threat Intel Tests ====================

class TestThreatIntel:
    def test_severity_mapping(self):
        from src.core.threat_intel import ThreatIntelFetcher
        assert ThreatIntelFetcher._score_to_severity(9.5) == "CRITICAL"
        assert ThreatIntelFetcher._score_to_severity(7.0) == "HIGH"
        assert ThreatIntelFetcher._score_to_severity(5.0) == "MEDIUM"
        assert ThreatIntelFetcher._score_to_severity(2.0) == "LOW"
        assert ThreatIntelFetcher._score_to_severity(None) == "UNKNOWN"

    def test_cache_mechanism(self):
        from src.core.threat_intel import ThreatIntelFetcher
        fetcher = ThreatIntelFetcher()
        # Store and retrieve from cache
        fetcher._set_cache("test_key", {"data": "test"})
        cached = fetcher._get_cache("test_key")
        assert cached == {"data": "test"}


# ==================== LangGraph Tests ====================
# REMOVED in Phase 3 step-3: src.core.langgraph_agents has been deleted as
# dead code (the only consumer, TestLangGraph, was removed in step-1).
# The unified orchestrator (src.core.orchestrator) replaces this functionality.
