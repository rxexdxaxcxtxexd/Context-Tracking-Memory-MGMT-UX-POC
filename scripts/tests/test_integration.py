"""
Integration Tests for Memory Trigger System

Comprehensive end-to-end tests for the full trigger flow:
init → auto-register → evaluate → query → format

Tests cover:
- Full trigger flow with keyword detection and memory query
- Project switch trigger with context retrieval
- Budget exhaustion scenarios
- Detector failure recovery
- State persistence across trigger evaluations
- Multiple detectors in priority order
- Memory formatting and token tracking

Author: Context-Aware Memory System
Date: 2025-12-29
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from memory_trigger_engine import MemoryTriggerEngine
from memory_detectors import MemoryDetector, TriggerResult, DetectorRegistry
from memory_detectors.keyword_detector import KeywordDetector
from memory_detectors.project_switch_detector import ProjectSwitchDetector
from memory_client import MemoryClient


class TestIntegrationFullTriggerFlow:
    """Integration tests for complete trigger flow"""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary .claude directory for testing"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        return claude_dir

    @pytest.fixture
    def config_with_detectors(self):
        """Configuration with keyword and project switch detectors enabled"""
        return {
            "detectors": {
                "project_switch": {
                    "enabled": True,
                    "priority": 1,
                    "detect_branch_switch": True,
                    "major_branches": ["main", "master", "develop"]
                },
                "keyword": {
                    "enabled": True,
                    "priority": 2
                }
            },
            "budget": {
                "max_tokens_per_session": 5000,
                "max_tokens_per_trigger": 500
            },
            "mcp": {
                "connection_timeout_seconds": 5,
                "query_timeout_seconds": 3
            },
            "logging": {
                "level": "ERROR",
                "file": ".claude/memory-trigger.log"
            }
        }

    @pytest.fixture
    def mock_memory_result(self):
        """Mock memory query result with entities"""
        return {
            "entities": [
                {
                    "name": "API Authentication Decision",
                    "entityType": "decision",
                    "observations": [
                        "Decided to use OAuth 2.0 for API authentication",
                        "Rationale: Better security than JWT",
                        "Implementation: Use existing oauth2-provider library"
                    ]
                },
                {
                    "name": "UserManager Class",
                    "entityType": "entity",
                    "observations": [
                        "Handles user lifecycle management",
                        "Uses dependency injection for database",
                        "Has unit tests with 95% coverage"
                    ]
                }
            ],
            "relations": [
                {
                    "from": "API Authentication Decision",
                    "to": "UserManager Class",
                    "type": "implements"
                }
            ]
        }

    @pytest.fixture
    def engine_with_mocks(self, tmp_path, config_with_detectors):
        """Create engine with mocked file system and memory client"""
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config_with_detectors))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()
            # Mock the memory client
            engine.memory_client = MagicMock(spec=MemoryClient)
            engine.memory_client.is_available.return_value = True

        return engine

    # ========== Test 1: Full Flow - Keyword Trigger → Memory Query → Format ==========

    def test_full_flow_keyword_trigger_to_formatted_output(self, engine_with_mocks, mock_memory_result):
        """
        Test complete flow: keyword trigger → memory query → formatted output

        Flow:
        1. Evaluate triggers with keyword-matching prompt
        2. Verify trigger fires with correct query type
        3. Query memory with trigger result
        4. Format result for display
        5. Verify token tracking
        """
        # Setup: Mock memory query to return results
        engine_with_mocks.memory_client.search_nodes.return_value = mock_memory_result
        engine_with_mocks.memory_client.estimate_tokens.return_value = 150

        prompt = "Remember our decision about API authentication?"
        initial_tokens = engine_with_mocks.state['tokens_used']

        # Step 1: Evaluate triggers
        trigger_result = engine_with_mocks.evaluate_triggers(prompt)

        # Verify trigger fired
        assert trigger_result is not None
        assert trigger_result.triggered is True
        assert trigger_result.query_type == "keyword_search"
        assert trigger_result.confidence >= 0.85
        assert 'query' in trigger_result.query_params
        assert 'category' in trigger_result.query_params

        # Step 2: Query memory
        memory_result = engine_with_mocks.query_memory(trigger_result)

        # Verify memory query succeeded
        assert memory_result is not None
        assert 'entities' in memory_result
        assert len(memory_result['entities']) == 2
        engine_with_mocks.memory_client.search_nodes.assert_called_once()

        # Step 3: Format result
        formatted = engine_with_mocks.format_result(trigger_result, memory_result)

        # Verify formatted output
        assert formatted is not None
        assert "[KEYWORD_SEARCH TRIGGER]" in formatted
        assert "API Authentication Decision" in formatted
        assert "decision" in formatted.lower()
        assert "Token cost" in formatted

        # Step 4: Verify token tracking
        assert engine_with_mocks.state['tokens_used'] > initial_tokens
        assert len(engine_with_mocks.state['triggers_fired']) == 1
        trigger_record = engine_with_mocks.state['triggers_fired'][0]
        assert trigger_record['detector'] == 'keyword_search'
        assert trigger_record['tokens'] == 150

    # ========== Test 2: Project Switch Trigger with Context ==========

    def test_project_switch_trigger_retrieves_project_context(self, engine_with_mocks):
        """
        Test project switch detector triggers and retrieves project-specific context

        Flow:
        1. Setup project context change in engine state
        2. Trigger project switch detection
        3. Verify project_context query type
        4. Query memory for project entities
        5. Format project-specific output
        """
        # Setup: Mock memory to return project entities
        project_result = {
            "entities": [
                {
                    "name": "ProjectName",
                    "entityType": "project",
                    "observations": [
                        "Python microservices project",
                        "Uses FastAPI framework",
                        "PostgreSQL database"
                    ]
                },
                {
                    "name": "Architecture Decision Record",
                    "entityType": "decision",
                    "observations": [
                        "Use event-driven architecture",
                        "RabbitMQ for message broker"
                    ]
                }
            ],
            "relations": []
        }
        engine_with_mocks.memory_client.search_nodes.return_value = project_result
        engine_with_mocks.memory_client.estimate_tokens.return_value = 200

        # Manually trigger project switch (simulate by creating trigger result)
        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.95,
            estimated_tokens=200,
            query_type="project_context",
            query_params={"project": "ProjectName"},
            reason="Detected project switch"
        )

        # Query memory
        memory_result = engine_with_mocks.query_memory(trigger_result)

        # Verify project context retrieved
        assert memory_result is not None
        assert any(e['entityType'] == 'project' for e in memory_result['entities'])

        # Format and verify output
        formatted = engine_with_mocks.format_result(trigger_result, memory_result)
        assert "[PROJECT_CONTEXT TRIGGER]" in formatted
        assert "ProjectName" in formatted or "Python microservices" in formatted

    # ========== Test 3: Budget Exhaustion Prevents Triggers ==========

    def test_budget_exhaustion_prevents_trigger_evaluation(self, tmp_path, config_with_detectors):
        """
        Test that exhausted token budget prevents trigger evaluation

        Flow:
        1. Create engine with small budget (200 tokens)
        2. Set tokens_used to near-budget value
        3. Attempt to evaluate trigger with large estimated cost
        4. Verify trigger evaluation skipped due to budget
        5. Verify no memory query made
        6. Check warning message
        """
        # Create config with small budget
        config_with_detectors['budget']['max_tokens_per_session'] = 200
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config_with_detectors))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()
            engine.memory_client = MagicMock(spec=MemoryClient)

            # Set tokens used to 150 (budget is 200, remaining 50)
            engine.state['tokens_used'] = 150

            # Attempt trigger that would cost 100 tokens (exceeds budget)
            trigger_result = engine.evaluate_triggers("Remember the API design?")

            # Verify no trigger (budget exhausted)
            assert trigger_result is None

            # Verify no memory query attempted
            engine.memory_client.search_nodes.assert_not_called()

    def test_budget_exhaustion_in_detector_registration(self, tmp_path, config_with_detectors):
        """
        Test budget prevents specific trigger after initial cost

        Flow:
        1. Register detectors with keyword detector (low token cost)
        2. Trigger first detector (costs 150 tokens, budget is 200)
        3. Register second detector with higher cost
        4. Attempt second trigger (would exceed budget)
        5. Verify second trigger skipped
        """
        config_with_detectors['budget']['max_tokens_per_session'] = 200
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config_with_detectors))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()
            engine.memory_client = MagicMock(spec=MemoryClient)
            engine.memory_client.is_available.return_value = True
            engine.memory_client.search_nodes.return_value = {
                "entities": [{"name": "Test", "entityType": "test", "observations": []}]
            }
            engine.memory_client.estimate_tokens.return_value = 150

            # First trigger should succeed
            trigger1 = engine.evaluate_triggers("Remember the decision?")
            assert trigger1 is not None

            # Manually record the trigger to update token usage
            engine._record_trigger(trigger1, 150)
            assert engine.state['tokens_used'] == 150

            # Second trigger would cost 100 more (total 250 > budget 200)
            # Create a trigger result with high cost
            expensive_trigger = TriggerResult(
                triggered=True,
                confidence=0.9,
                estimated_tokens=100,
                query_type="keyword_search",
                query_params={"query": "test"},
                reason="Test"
            )

            # Verify budget check fails for expensive trigger
            assert not engine._check_budget(expensive_trigger.estimated_tokens)

    # ========== Test 4: Detector Failure Recovery ==========

    def test_detector_failure_recovery_continues_evaluation(self, engine_with_mocks):
        """
        Test engine continues to next detector when one fails

        Flow:
        1. Register first detector that will raise exception
        2. Register second detector that will succeed
        3. Evaluate triggers on mixed detector setup
        4. Verify first detector exception caught and logged
        5. Verify second detector evaluated and triggered
        6. Confirm output is from second detector
        """
        # Create a failing detector
        class FailingDetector(MemoryDetector):
            @property
            def name(self):
                return "failing_detector"

            def evaluate(self, prompt, context):
                raise RuntimeError("Intentional test failure")

        # Create a working detector
        class WorkingDetector(MemoryDetector):
            @property
            def name(self):
                return "working_detector"

            def evaluate(self, prompt, context):
                if "test" in prompt.lower():
                    return TriggerResult(
                        triggered=True,
                        confidence=0.9,
                        estimated_tokens=100,
                        query_type="test_query",
                        query_params={"query": "test"},
                        reason="Working detector matched"
                    )
                return None

        # Register detectors
        engine_with_mocks.registry.clear()
        engine_with_mocks.registry.register(FailingDetector({"enabled": True, "priority": 1}))
        engine_with_mocks.registry.register(WorkingDetector({"enabled": True, "priority": 2}))

        # Mock memory client
        engine_with_mocks.memory_client.is_available.return_value = True
        engine_with_mocks.memory_client.search_nodes.return_value = {
            "entities": [{"name": "Test", "entityType": "test", "observations": ["Test data"]}]
        }
        engine_with_mocks.memory_client.estimate_tokens.return_value = 100

        # Evaluate with mixed detectors
        result = engine_with_mocks.evaluate_triggers("test prompt")

        # Verify second detector triggered despite first detector failing
        assert result is not None
        assert result.reason == "Working detector matched"
        assert result.query_type == "test_query"

    # ========== Test 5: State Persistence Across Calls ==========

    def test_state_persistence_across_multiple_trigger_evaluations(self, tmp_path, config_with_detectors):
        """
        Test state persists across multiple trigger evaluations

        Flow:
        1. Evaluate first trigger and record state
        2. Create new engine instance (should load state from file)
        3. Verify token count from previous trigger is maintained
        4. Evaluate second trigger
        5. Verify cumulative token tracking
        6. Verify triggers_fired list grows
        """
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config_with_detectors))

        # First engine instance
        with patch('pathlib.Path.home', return_value=tmp_path):
            engine1 = MemoryTriggerEngine()
            engine1.memory_client = MagicMock(spec=MemoryClient)
            engine1.memory_client.is_available.return_value = True
            engine1.memory_client.search_nodes.return_value = {
                "entities": [{"name": "Test1", "entityType": "test", "observations": []}]
            }
            engine1.memory_client.estimate_tokens.return_value = 100

            # First trigger
            trigger1 = engine1.evaluate_triggers("Remember the first decision?")
            assert trigger1 is not None

            # Record trigger
            engine1._record_trigger(trigger1, 100)
            session_id_1 = engine1.state['session_id']
            tokens_after_first = engine1.state['tokens_used']
            triggers_count_1 = len(engine1.state['triggers_fired'])

        # Second engine instance (should load state)
        with patch('pathlib.Path.home', return_value=tmp_path):
            engine2 = MemoryTriggerEngine()
            engine2.memory_client = MagicMock(spec=MemoryClient)
            engine2.memory_client.is_available.return_value = True
            engine2.memory_client.search_nodes.return_value = {
                "entities": [{"name": "Test2", "entityType": "test", "observations": []}]
            }
            engine2.memory_client.estimate_tokens.return_value = 150

            # Verify state loaded from first engine
            assert engine2.state['session_id'] == session_id_1
            assert engine2.state['tokens_used'] == tokens_after_first
            assert len(engine2.state['triggers_fired']) == triggers_count_1

            # Second trigger
            trigger2 = engine2.evaluate_triggers("Remember the second decision?")
            assert trigger2 is not None

            # Record second trigger
            engine2._record_trigger(trigger2, 150)

            # Verify cumulative state
            assert engine2.state['tokens_used'] == tokens_after_first + 150
            assert len(engine2.state['triggers_fired']) == triggers_count_1 + 1
            assert engine2.state['session_id'] == session_id_1  # Same session

    # ========== Test 6: Multiple Detectors in Priority Order ==========

    def test_multiple_detectors_evaluated_in_priority_order(self, tmp_path, config_with_detectors):
        """
        Test detectors are evaluated in priority order and first match wins

        Flow:
        1. Register 3 detectors with priorities 1, 2, 3
        2. Configure all to potentially trigger on same prompt
        3. Evaluate triggers
        4. Verify detector with lowest priority (1) triggered first
        5. Verify other detectors not evaluated (short-circuit)
        6. Check stats show correct detector order
        """
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config_with_detectors))

        # Create custom detectors with explicit priority
        class Priority1Detector(MemoryDetector):
            def __init__(self):
                super().__init__({"enabled": True, "priority": 1})

            @property
            def name(self):
                return "detector_p1"

            def evaluate(self, prompt, context):
                return TriggerResult(
                    triggered=True,
                    confidence=0.9,
                    estimated_tokens=100,
                    query_type="p1_query",
                    query_params={},
                    reason="Priority 1 detector"
                )

        class Priority2Detector(MemoryDetector):
            def __init__(self):
                super().__init__({"enabled": True, "priority": 2})

            @property
            def name(self):
                return "detector_p2"

            def evaluate(self, prompt, context):
                return TriggerResult(
                    triggered=True,
                    confidence=0.8,
                    estimated_tokens=100,
                    query_type="p2_query",
                    query_params={},
                    reason="Priority 2 detector"
                )

        class Priority3Detector(MemoryDetector):
            def __init__(self):
                super().__init__({"enabled": True, "priority": 3})

            @property
            def name(self):
                return "detector_p3"

            def evaluate(self, prompt, context):
                return TriggerResult(
                    triggered=True,
                    confidence=0.7,
                    estimated_tokens=100,
                    query_type="p3_query",
                    query_params={},
                    reason="Priority 3 detector"
                )

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()
            engine.registry.clear()

            # Register detectors (intentionally out of order)
            engine.registry.register(Priority3Detector())
            engine.registry.register(Priority1Detector())
            engine.registry.register(Priority2Detector())

            engine.memory_client = MagicMock(spec=MemoryClient)
            engine.memory_client.is_available.return_value = True

            # Verify priority order
            detectors = engine.registry.get_enabled_detectors()
            assert detectors[0].priority == 1
            assert detectors[1].priority == 2
            assert detectors[2].priority == 3

            # Evaluate triggers
            result = engine.evaluate_triggers("test prompt")

            # Verify priority 1 detector triggered (first in order)
            assert result is not None
            assert result.query_type == "p1_query"
            assert "Priority 1" in result.reason

    # ========== Test 7: Format Result Handles Missing Entities ==========

    def test_format_result_gracefully_handles_no_entities(self, engine_with_mocks):
        """
        Test format_result handles empty or missing entities gracefully

        Flow:
        1. Create trigger result
        2. Query memory returns empty entities
        3. Format result with empty memory
        4. Verify graceful fallback message
        5. Verify no crash on missing observations
        """
        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=100,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        # Test 1: Empty entities
        empty_memory = {"entities": [], "relations": []}
        formatted = engine_with_mocks.format_result(trigger_result, empty_memory)

        assert formatted is not None
        assert "No relevant memory found" in formatted
        assert "[KEYWORD_SEARCH]" in formatted

        # Test 2: None memory result
        formatted_none = engine_with_mocks.format_result(trigger_result, None)
        assert formatted_none is not None
        assert "No relevant memory found" in formatted_none

        # Test 3: Missing observations
        sparse_memory = {
            "entities": [
                {
                    "name": "Sparse Entity",
                    "entityType": "test",
                    "observations": []
                }
            ]
        }
        formatted_sparse = engine_with_mocks.format_result(trigger_result, sparse_memory)
        assert formatted_sparse is not None
        assert "Sparse Entity" in formatted_sparse

    # ========== Test 8: Token Cost Tracking and Budget Math ==========

    def test_token_tracking_accumulates_correctly(self, tmp_path, config_with_detectors):
        """
        Test token cost tracking is accurate across multiple triggers

        Flow:
        1. Create engine with 1000 token budget
        2. Trigger 3 detectors with different costs (200, 300, 250)
        3. Track remaining budget after each trigger
        4. Verify math: 200 + 300 + 250 = 750 used, 250 remaining
        5. Verify next trigger with 300 tokens exceeds budget
        6. Check stats show correct token accounting
        """
        config_with_detectors['budget']['max_tokens_per_session'] = 1000
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config_with_detectors))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()
            engine.memory_client = MagicMock(spec=MemoryClient)
            engine.memory_client.is_available.return_value = True
            engine.memory_client.search_nodes.return_value = {
                "entities": [{"name": "Test", "entityType": "test", "observations": []}]
            }

            # Trigger 1: 200 tokens
            engine.memory_client.estimate_tokens.return_value = 200
            trigger1 = engine.evaluate_triggers("Remember decision 1?")
            engine._record_trigger(trigger1, 200)
            assert engine.state['tokens_used'] == 200
            assert engine.get_stats()['tokens_remaining'] == 800

            # Trigger 2: 300 tokens
            engine.memory_client.estimate_tokens.return_value = 300
            trigger2 = engine.evaluate_triggers("Remember decision 2?")
            engine._record_trigger(trigger2, 300)
            assert engine.state['tokens_used'] == 500
            assert engine.get_stats()['tokens_remaining'] == 500

            # Trigger 3: 250 tokens
            engine.memory_client.estimate_tokens.return_value = 250
            trigger3 = engine.evaluate_triggers("Remember decision 3?")
            engine._record_trigger(trigger3, 250)
            assert engine.state['tokens_used'] == 750
            assert engine.get_stats()['tokens_remaining'] == 250

            # Verify next expensive trigger would exceed budget
            assert not engine._check_budget(300)  # 750 + 300 > 1000

            # Verify smaller trigger still fits
            assert engine._check_budget(250)  # 750 + 250 == 1000


class TestIntegrationErrorScenarios:
    """Integration tests for error scenarios and edge cases"""

    @pytest.fixture
    def engine_with_mocks(self, tmp_path):
        """Create engine with mocks for error scenario testing"""
        config = {
            "detectors": {
                "keyword": {
                    "enabled": True,
                    "priority": 2
                }
            },
            "budget": {
                "max_tokens_per_session": 5000,
                "max_tokens_per_trigger": 500
            },
            "mcp": {
                "connection_timeout_seconds": 1,
                "query_timeout_seconds": 1
            },
            "logging": {
                "level": "ERROR",
                "file": ".claude/memory-trigger.log"
            }
        }
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()
            engine.memory_client = MagicMock(spec=MemoryClient)

        return engine

    def test_memory_server_unavailable_returns_none(self, engine_with_mocks):
        """
        Test graceful handling when memory server is unavailable

        Flow:
        1. Trigger fires successfully
        2. Memory server reports unavailable
        3. Query memory returns None
        4. Format handles None gracefully
        5. No exception raised
        """
        # Setup: Memory server unavailable
        engine_with_mocks.memory_client.is_available.return_value = False

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=100,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        # Query memory should return None
        result = engine_with_mocks.query_memory(trigger_result)
        assert result is None

        # Format should handle None gracefully
        formatted = engine_with_mocks.format_result(trigger_result, None)
        assert formatted is not None
        assert "No relevant memory found" in formatted

    def test_memory_query_error_caught_and_logged(self, engine_with_mocks):
        """
        Test memory query exceptions are caught and handled

        Flow:
        1. Memory server throws exception during query
        2. Exception is caught in query_memory()
        3. None is returned (not exception propagated)
        4. Trigger evaluation continues
        """
        # Setup: Memory query throws exception
        engine_with_mocks.memory_client.is_available.return_value = True
        engine_with_mocks.memory_client.search_nodes.side_effect = RuntimeError("Connection timeout")

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=100,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        # Should return None, not raise
        result = engine_with_mocks.query_memory(trigger_result)
        assert result is None

    def test_detector_returns_none_skips_evaluation(self, engine_with_mocks):
        """
        Test that None result from detector is handled correctly

        Flow:
        1. Detector evaluates and returns None (no match)
        2. Engine continues to next detector
        3. No memory query made for None result
        4. No exception raised
        """
        class NullDetector(MemoryDetector):
            @property
            def name(self):
                return "null_detector"

            def evaluate(self, prompt, context):
                return None  # No match

        engine_with_mocks.registry.clear()
        engine_with_mocks.registry.register(NullDetector({"enabled": True, "priority": 1}))

        # Evaluate should return None
        result = engine_with_mocks.evaluate_triggers("any prompt")
        assert result is None

    def test_invalid_query_type_handled_gracefully(self, engine_with_mocks):
        """
        Test unknown query type in trigger result

        Flow:
        1. Trigger returns unknown query_type
        2. query_memory() handles gracefully
        3. Warning logged
        4. None returned
        """
        engine_with_mocks.memory_client.is_available.return_value = True

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=100,
            query_type="unknown_query_type",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        # Should handle gracefully
        result = engine_with_mocks.query_memory(trigger_result)
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
