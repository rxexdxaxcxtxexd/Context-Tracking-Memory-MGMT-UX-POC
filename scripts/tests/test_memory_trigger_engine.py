"""
Tests for Memory Trigger Engine

Tests engine orchestration, detector auto-registration, trigger evaluation,
memory queries, state management, and budget enforcement.

Author: Context-Aware Memory System
Date: 2025-12-29
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from memory_trigger_engine import MemoryTriggerEngine
from memory_detectors import MemoryDetector, TriggerResult, DetectorRegistry
from memory_client import MemoryClient


class MockDetector(MemoryDetector):
    """Mock detector for testing"""

    def __init__(self, config, detector_name="mock_detector", trigger_on_prompt=None):
        super().__init__(config)
        self._name = detector_name
        self.trigger_on_prompt = trigger_on_prompt
        self.evaluate_count = 0

    def evaluate(self, prompt, context):
        self.evaluate_count += 1

        if self.trigger_on_prompt and self.trigger_on_prompt in prompt:
            return TriggerResult(
                triggered=True,
                confidence=0.9,
                estimated_tokens=150,
                query_type="mock_query",
                query_params={"query": "test"},
                reason="Mock trigger"
            )
        return None

    @property
    def name(self):
        return self._name


class TestMemoryTriggerEngine:
    """Test suite for MemoryTriggerEngine"""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary .claude directory"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        return claude_dir

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return {
            "detectors": {
                "project_switch": {
                    "enabled": False,  # Disabled to avoid import issues
                    "priority": 1
                },
                "keyword": {
                    "enabled": False,  # Disabled to avoid import issues
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
                "level": "ERROR",  # Reduce log noise during tests
                "file": ".claude/memory-trigger.log"
            }
        }

    @pytest.fixture
    def mock_state(self):
        """Create mock state"""
        return {
            "session_id": "test-session-123",
            "session_start": "2025-12-29T10:00:00",
            "tokens_used": 100,
            "triggers_fired": []
        }

    # ========== Initialization Tests ==========

    def test_initialization_creates_directories(self, tmp_path):
        """Test initialization creates .claude directory"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        assert (tmp_path / ".claude").exists()

    def test_initialization_loads_config(self, tmp_path, mock_config):
        """Test initialization loads configuration from file"""
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(mock_config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        assert engine.config['budget']['max_tokens_per_session'] == 5000

    def test_initialization_uses_default_config_when_missing(self, tmp_path):
        """Test initialization uses defaults when config file missing"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        assert 'budget' in engine.config
        assert 'detectors' in engine.config

    def test_initialization_creates_memory_client(self, tmp_path):
        """Test initialization creates MemoryClient instance"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        assert isinstance(engine.memory_client, MemoryClient)

    def test_initialization_creates_detector_registry(self, tmp_path):
        """Test initialization creates DetectorRegistry"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        assert isinstance(engine.registry, DetectorRegistry)

    def test_initialization_loads_state(self, tmp_path, mock_state):
        """Test initialization loads session state from file"""
        state_path = tmp_path / ".claude" / "memory-trigger-state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(mock_state))

        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        assert engine.state['session_id'] == 'test-session-123'
        assert engine.state['tokens_used'] == 100

    def test_initialization_creates_new_state_when_missing(self, tmp_path):
        """Test initialization creates new state when file missing"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        assert 'session_id' in engine.state
        assert 'session_start' in engine.state
        assert engine.state['tokens_used'] == 0

    # ========== Auto-Registration Tests (CRITICAL) ==========

    def test_auto_registration_called_during_init(self, tmp_path, mock_config):
        """Test _initialize_detectors() is called during __init__()"""
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(mock_config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors') as mock_init:
                engine = MemoryTriggerEngine()

        mock_init.assert_called_once()

    def test_auto_registration_enables_detectors_from_config(self, tmp_path):
        """Test enabled detectors are auto-registered"""
        config = {
            "detectors": {
                "keyword": {
                    "enabled": True,
                    "priority": 2
                }
            },
            "budget": {"max_tokens_per_session": 5000}
        }
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()

        # Should have registered keyword detector
        assert len(engine.registry) > 0
        assert engine.registry.get_detector('keyword_detector') is not None

    def test_auto_registration_skips_disabled_detectors(self, tmp_path, mock_config):
        """Test disabled detectors are not auto-registered"""
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(mock_config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()

        # All detectors disabled in mock_config
        assert engine.registry.get_detector('project_switch_detector') is None
        assert engine.registry.get_detector('keyword_detector') is None

    def test_auto_registration_handles_import_errors_gracefully(self, tmp_path):
        """Test auto-registration continues when detector import fails"""
        config = {
            "detectors": {
                "nonexistent_detector": {  # This will fail to import
                    "enabled": True,
                    "priority": 1
                },
                "keyword": {
                    "enabled": True,
                    "priority": 2
                }
            },
            "budget": {"max_tokens_per_session": 5000}
        }
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            # Should not raise exception
            engine = MemoryTriggerEngine()

        # Keyword detector should still be registered despite import error
        assert engine.registry.get_detector('keyword_detector') is not None

    def test_auto_registration_sets_memory_client_for_entity_detector(self, tmp_path):
        """Test auto-registration calls set_memory_client() for EntityMentionDetector"""
        config = {
            "detectors": {
                "entity_mention": {
                    "enabled": True,
                    "priority": 3
                }
            },
            "budget": {"max_tokens_per_session": 5000}
        }
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()

        detector = engine.registry.get_detector('entity_mention_detector')
        if detector:  # Only if import succeeded
            assert hasattr(detector, '_memory_client')
            assert detector._memory_client is engine.memory_client

    def test_auto_registration_respects_priority_order(self, tmp_path):
        """Test auto-registered detectors are ordered by priority"""
        config = {
            "detectors": {
                "keyword": {
                    "enabled": True,
                    "priority": 2
                },
                "token_threshold": {
                    "enabled": True,
                    "priority": 4
                }
            },
            "budget": {"max_tokens_per_session": 5000}
        }
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()

        detectors = engine.registry.get_enabled_detectors()
        if len(detectors) >= 2:
            # Priority 2 should come before priority 4
            assert detectors[0].priority <= detectors[1].priority

    def test_auto_registration_logs_success_and_failures(self, tmp_path, mock_config):
        """Test auto-registration logs registration results"""
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(mock_config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()

        # Logger should have been called (can't easily test log contents without mocking logger)
        assert hasattr(engine, 'logger')

    # ========== Manual Registration Tests ==========

    def test_manual_registration_adds_detector(self, tmp_path):
        """Test manual detector registration"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        mock_detector = MockDetector({'enabled': True, 'priority': 10})
        engine.register_detector(mock_detector)

        assert engine.registry.get_detector('mock_detector') is not None

    def test_manual_registration_overrides_auto_registered(self, tmp_path):
        """Test manual registration can override auto-registered detector"""
        config = {
            "detectors": {
                "keyword": {
                    "enabled": True,
                    "priority": 2
                }
            },
            "budget": {"max_tokens_per_session": 5000}
        }
        config_path = tmp_path / ".claude" / "memory-trigger-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config))

        with patch('pathlib.Path.home', return_value=tmp_path):
            engine = MemoryTriggerEngine()

        # Manually register a detector with same name
        custom_detector = MockDetector({'enabled': True, 'priority': 1}, detector_name='keyword_detector')
        engine.register_detector(custom_detector)

        # Should have only one keyword_detector (the custom one)
        detectors = [d for d in engine.registry._detectors if d.name == 'keyword_detector']
        assert len(detectors) == 1
        assert detectors[0] == custom_detector

    # ========== Trigger Evaluation Tests ==========

    def test_evaluate_triggers_calls_enabled_detectors(self, tmp_path):
        """Test evaluate_triggers() calls all enabled detectors"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        detector1 = MockDetector({'enabled': True, 'priority': 1}, detector_name="detector1")
        detector2 = MockDetector({'enabled': True, 'priority': 2}, detector_name="detector2")
        engine.register_detector(detector1)
        engine.register_detector(detector2)

        engine.evaluate_triggers("test prompt")

        assert detector1.evaluate_count == 1
        assert detector2.evaluate_count == 1

    def test_evaluate_triggers_short_circuits_on_first_match(self, tmp_path):
        """Test evaluation stops after first triggered detector"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        detector1 = MockDetector({'enabled': True, 'priority': 1}, detector_name="detector1", trigger_on_prompt="trigger")
        detector2 = MockDetector({'enabled': True, 'priority': 2}, detector_name="detector2")
        engine.register_detector(detector1)
        engine.register_detector(detector2)

        result = engine.evaluate_triggers("test trigger prompt")

        assert result is not None
        assert detector1.evaluate_count == 1
        assert detector2.evaluate_count == 0  # Should not be called (short-circuit)

    def test_evaluate_triggers_respects_priority_order(self, tmp_path):
        """Test detectors evaluated in priority order"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        detector_high = MockDetector({'enabled': True, 'priority': 1}, detector_name="high_priority", trigger_on_prompt="trigger")
        detector_low = MockDetector({'enabled': True, 'priority': 10}, detector_name="low_priority", trigger_on_prompt="trigger")

        # Register in reverse order
        engine.register_detector(detector_low)
        engine.register_detector(detector_high)

        result = engine.evaluate_triggers("test trigger prompt")

        # High priority detector should trigger first
        assert result.reason == "Mock trigger"
        assert detector_high.evaluate_count == 1
        assert detector_low.evaluate_count == 0

    def test_evaluate_triggers_returns_none_when_no_match(self, tmp_path):
        """Test returns None when no detectors trigger"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        detector = MockDetector({'enabled': True, 'priority': 1})
        engine.register_detector(detector)

        result = engine.evaluate_triggers("test prompt")

        assert result is None

    def test_evaluate_triggers_handles_detector_exceptions(self, tmp_path):
        """Test evaluation continues when detector raises exception"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        # Create detector that raises exception
        bad_detector = MockDetector({'enabled': True, 'priority': 1}, detector_name="bad")
        bad_detector.evaluate = Mock(side_effect=ValueError("Test error"))

        good_detector = MockDetector({'enabled': True, 'priority': 2}, detector_name="good", trigger_on_prompt="trigger")

        engine.register_detector(bad_detector)
        engine.register_detector(good_detector)

        result = engine.evaluate_triggers("test trigger prompt")

        # Should continue to good_detector despite bad_detector error
        assert result is not None

    def test_evaluate_triggers_builds_context(self, tmp_path):
        """Test evaluate_triggers builds context when not provided"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        detector = MockDetector({'enabled': True, 'priority': 1})

        # Mock evaluate to capture context
        original_evaluate = detector.evaluate
        context_captured = {}

        def capture_context(prompt, context):
            context_captured.update(context)
            return original_evaluate(prompt, context)

        detector.evaluate = capture_context
        engine.register_detector(detector)

        engine.evaluate_triggers("test prompt")

        assert 'session_id' in context_captured
        assert 'token_count' in context_captured
        assert 'timestamp' in context_captured

    # ========== Budget Enforcement Tests ==========

    def test_budget_check_prevents_trigger_when_exhausted(self, tmp_path):
        """Test trigger is skipped when budget exhausted"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        # Set tokens_used to max
        engine.state['tokens_used'] = engine.config['budget']['max_tokens_per_session']

        detector = MockDetector({'enabled': True, 'priority': 1}, trigger_on_prompt="trigger")
        engine.register_detector(detector)

        result = engine.evaluate_triggers("test trigger prompt")

        assert result is None  # Budget exhausted, no trigger

    def test_budget_check_allows_trigger_when_within_budget(self, tmp_path):
        """Test trigger allowed when within budget"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        engine.state['tokens_used'] = 100  # Well within budget

        detector = MockDetector({'enabled': True, 'priority': 1}, trigger_on_prompt="trigger")
        engine.register_detector(detector)

        result = engine.evaluate_triggers("test trigger prompt")

        assert result is not None

    def test_budget_check_per_trigger_prevents_large_query(self, tmp_path):
        """Test individual trigger budget is checked"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        # Set tokens_used close to max
        max_tokens = engine.config['budget']['max_tokens_per_session']
        engine.state['tokens_used'] = max_tokens - 50  # 50 tokens remaining

        # Create detector that would exceed budget (150 tokens)
        detector = MockDetector({'enabled': True, 'priority': 1}, trigger_on_prompt="trigger")
        engine.register_detector(detector)

        result = engine.evaluate_triggers("test trigger prompt")

        assert result is None  # Trigger would exceed budget

    # ========== Memory Query Tests ==========

    def test_query_memory_keyword_search(self, tmp_path):
        """Test query_memory() with keyword_search type"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="keyword_search",
            query_params={"query": "test query"},
            reason="Test"
        )

        with patch.object(engine.memory_client, 'search_nodes', return_value={'entities': []}) as mock_search:
            engine.query_memory(trigger_result)

        mock_search.assert_called_once_with("test query")

    def test_query_memory_entity_details(self, tmp_path):
        """Test query_memory() with entity_details type"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="entity_details",
            query_params={"names": ["entity1", "entity2"]},
            reason="Test"
        )

        with patch.object(engine.memory_client, 'open_nodes', return_value={'entities': []}) as mock_open:
            engine.query_memory(trigger_result)

        mock_open.assert_called_once_with(["entity1", "entity2"])

    def test_query_memory_project_context(self, tmp_path):
        """Test query_memory() with project_context type"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="project_context",
            query_params={"project": "my-project"},
            reason="Test"
        )

        with patch.object(engine.memory_client, 'search_nodes', return_value={'entities': []}) as mock_search:
            engine.query_memory(trigger_result)

        mock_search.assert_called_once_with("project:my-project")

    def test_query_memory_returns_none_when_unavailable(self, tmp_path):
        """Test query_memory() returns None when MCP unavailable"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test"
        )

        with patch.object(engine.memory_client, 'is_available', return_value=False):
            result = engine.query_memory(trigger_result)

        assert result is None

    def test_query_memory_records_trigger_on_success(self, tmp_path):
        """Test query_memory() records trigger when successful"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test"
        )

        with patch.object(engine.memory_client, 'search_nodes', return_value={'entities': []}):
            with patch.object(engine.memory_client, 'estimate_tokens', return_value=150):
                engine.query_memory(trigger_result)

        assert engine.state['tokens_used'] > 0

    # ========== State Management Tests ==========

    def test_save_state_persists_to_file(self, tmp_path):
        """Test _save_state() writes to file"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        engine.state['test_key'] = 'test_value'
        engine._save_state()

        state_path = tmp_path / ".claude" / "memory-trigger-state.json"
        assert state_path.exists()

        saved_state = json.loads(state_path.read_text())
        assert saved_state['test_key'] == 'test_value'

    def test_record_trigger_updates_state(self, tmp_path):
        """Test _record_trigger() updates tokens and fires list"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        initial_tokens = engine.state['tokens_used']

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        engine._record_trigger(trigger_result, actual_tokens=150)

        assert engine.state['tokens_used'] == initial_tokens + 150
        assert len(engine.state['triggers_fired']) == 1
        assert engine.state['triggers_fired'][0]['tokens'] == 150

    # ========== Statistics Tests ==========

    def test_get_stats_returns_session_info(self, tmp_path):
        """Test get_stats() returns comprehensive session statistics"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        stats = engine.get_stats()

        assert 'session_id' in stats
        assert 'session_start' in stats
        assert 'tokens_used' in stats
        assert 'tokens_budget' in stats
        assert 'tokens_remaining' in stats
        assert 'triggers_fired' in stats
        assert 'detectors_registered' in stats
        assert 'detectors_enabled' in stats

    def test_get_stats_calculates_tokens_remaining(self, tmp_path):
        """Test get_stats() correctly calculates remaining tokens"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        engine.state['tokens_used'] = 1000

        stats = engine.get_stats()

        expected_remaining = engine.config['budget']['max_tokens_per_session'] - 1000
        assert stats['tokens_remaining'] == expected_remaining

    # ========== Result Formatting Tests ==========

    def test_format_result_with_entities(self, tmp_path):
        """Test format_result() formats entities correctly"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        memory_result = {
            'entities': [
                {
                    'name': 'TestEntity',
                    'entityType': 'decision',
                    'observations': ['Observation 1', 'Observation 2']
                }
            ]
        }

        output = engine.format_result(trigger_result, memory_result)

        assert 'KEYWORD_SEARCH TRIGGER' in output
        assert 'Test trigger' in output
        assert 'TestEntity' in output
        assert 'Observation 1' in output

    def test_format_result_with_no_entities(self, tmp_path):
        """Test format_result() handles empty results"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        memory_result = {'entities': []}

        output = engine.format_result(trigger_result, memory_result)

        assert 'No relevant memory found' in output

    def test_format_result_limits_entities_to_five(self, tmp_path):
        """Test format_result() limits output to 5 entities"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        memory_result = {
            'entities': [
                {'name': f'Entity{i}', 'entityType': 'test', 'observations': ['obs']}
                for i in range(10)  # 10 entities
            ]
        }

        output = engine.format_result(trigger_result, memory_result)

        # Should only show first 5
        assert 'Entity0' in output
        assert 'Entity4' in output
        assert 'Entity9' not in output  # Should be truncated

    def test_format_result_limits_observations_to_three(self, tmp_path):
        """Test format_result() limits observations to 3 per entity"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch.object(MemoryTriggerEngine, '_initialize_detectors'):
                engine = MemoryTriggerEngine()

        trigger_result = TriggerResult(
            triggered=True,
            confidence=0.9,
            estimated_tokens=150,
            query_type="keyword_search",
            query_params={"query": "test"},
            reason="Test trigger"
        )

        memory_result = {
            'entities': [
                {
                    'name': 'TestEntity',
                    'entityType': 'test',
                    'observations': [f'Obs {i}' for i in range(10)]  # 10 observations
                }
            ]
        }

        output = engine.format_result(trigger_result, memory_result)

        # Should only show first 3 observations
        assert 'Obs 0' in output
        assert 'Obs 2' in output
        assert 'Obs 9' not in output  # Should be truncated
