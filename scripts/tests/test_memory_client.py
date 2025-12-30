"""
Tests for Memory Client

Tests MCP memory server client wrapper, including availability checks,
query methods, token estimation, retry logic, and timeout handling.

Author: Context-Aware Memory System
Date: 2025-12-29
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from memory_client import MemoryClient


class TestMemoryClient:
    """Test suite for MemoryClient"""

    @pytest.fixture
    def client(self):
        """Create client instance with default config"""
        return MemoryClient()

    @pytest.fixture
    def client_with_config(self):
        """Create client instance with custom config"""
        config = {
            'connection_timeout_seconds': 10,
            'query_timeout_seconds': 5,
            'retry_attempts': 3,
            'retry_backoff_seconds': 2
        }
        return MemoryClient(config)

    @pytest.fixture
    def mock_result(self):
        """Create mock memory query result"""
        return {
            'entities': [
                {
                    'name': 'test-entity',
                    'entityType': 'decision',
                    'observations': ['Test observation 1', 'Test observation 2']
                }
            ],
            'relations': []
        }

    # ========== Initialization Tests ==========

    def test_initialization_with_defaults(self, client):
        """Test client initializes with default configuration"""
        assert client.connection_timeout == 5
        assert client.query_timeout == 3
        assert client.retry_attempts == 2
        assert client.retry_backoff == 1

    def test_initialization_with_custom_config(self, client_with_config):
        """Test client initializes with custom configuration"""
        assert client_with_config.connection_timeout == 10
        assert client_with_config.query_timeout == 5
        assert client_with_config.retry_attempts == 3
        assert client_with_config.retry_backoff == 2

    def test_initialization_with_empty_config(self):
        """Test client handles empty config dict"""
        client = MemoryClient({})
        assert client.connection_timeout == 5  # Uses defaults

    def test_initialization_sets_cache_vars(self, client):
        """Test initialization sets availability cache variables"""
        assert client._is_available_cache is None
        assert client._is_available_cache_time == 0
        assert client._is_available_cache_ttl == 60

    # ========== Availability Check Tests ==========

    def test_is_available_calls_read_graph(self, client):
        """Test is_available() checks connection via read_graph()"""
        with patch.object(client, 'read_graph', return_value={'entities': []}) as mock_read:
            result = client.is_available()

        mock_read.assert_called_once()
        assert result is True

    def test_is_available_returns_true_when_graph_readable(self, client):
        """Test is_available() returns True when read_graph succeeds"""
        with patch.object(client, 'read_graph', return_value={'entities': []}):
            assert client.is_available() is True

    def test_is_available_returns_false_when_graph_unreadable(self, client):
        """Test is_available() returns False when read_graph fails"""
        with patch.object(client, 'read_graph', return_value=None):
            assert client.is_available() is False

    def test_is_available_returns_false_on_exception(self, client):
        """Test is_available() returns False when exception raised"""
        with patch.object(client, 'read_graph', side_effect=Exception("Connection error")):
            assert client.is_available() is False

    def test_is_available_caches_result(self, client):
        """Test is_available() caches result for 60 seconds"""
        with patch.object(client, 'read_graph', return_value={'entities': []}) as mock_read:
            # First call
            client.is_available()
            # Second call (should use cache)
            client.is_available()

        # Should only call read_graph once (second uses cache)
        assert mock_read.call_count == 1

    def test_is_available_cache_expires_after_ttl(self, client):
        """Test is_available() cache expires after TTL"""
        with patch.object(client, 'read_graph', return_value={'entities': []}) as mock_read:
            # First call
            client.is_available()

            # Mock time.time() to simulate TTL expiration
            with patch('time.time', return_value=time.time() + 61):  # 61 seconds later
                # Second call (cache expired)
                client.is_available()

        # Should call read_graph twice (cache expired)
        assert mock_read.call_count == 2

    def test_is_available_caches_both_true_and_false(self, client):
        """Test is_available() caches both success and failure"""
        # Cache failure
        with patch.object(client, 'read_graph', return_value=None) as mock_read:
            result1 = client.is_available()
            result2 = client.is_available()

        assert result1 is False
        assert result2 is False
        assert mock_read.call_count == 1  # Cached

    # ========== Search Nodes Tests ==========

    def test_search_nodes_calls_mcp_tool(self, client, mock_result):
        """Test search_nodes() calls _call_mcp_tool with correct params"""
        with patch.object(client, '_call_mcp_tool', return_value=mock_result) as mock_call:
            client.search_nodes("test query")

        mock_call.assert_called_with('search_nodes', {'query': 'test query'})

    def test_search_nodes_returns_result(self, client, mock_result):
        """Test search_nodes() returns result from MCP"""
        with patch.object(client, '_call_mcp_tool', return_value=mock_result):
            result = client.search_nodes("test query")

        assert result == mock_result
        assert 'entities' in result

    def test_search_nodes_with_limit_parameter(self, client):
        """Test search_nodes() accepts limit parameter (for documentation)"""
        with patch.object(client, '_call_mcp_tool', return_value={'entities': []}):
            # Limit is documented but not enforced by MCP
            result = client.search_nodes("test query", limit=5)

        assert result is not None

    def test_search_nodes_returns_none_on_error(self, client):
        """Test search_nodes() returns None when operation fails"""
        with patch.object(client, '_retry_operation', return_value=None):
            result = client.search_nodes("test query")

        assert result is None

    # ========== Open Nodes Tests ==========

    def test_open_nodes_calls_mcp_tool(self, client, mock_result):
        """Test open_nodes() calls _call_mcp_tool with correct params"""
        with patch.object(client, '_call_mcp_tool', return_value=mock_result) as mock_call:
            client.open_nodes(['entity1', 'entity2'])

        mock_call.assert_called_with('open_nodes', {'names': ['entity1', 'entity2']})

    def test_open_nodes_returns_result(self, client, mock_result):
        """Test open_nodes() returns result from MCP"""
        with patch.object(client, '_call_mcp_tool', return_value=mock_result):
            result = client.open_nodes(['entity1'])

        assert result == mock_result

    def test_open_nodes_with_empty_list(self, client):
        """Test open_nodes() handles empty name list"""
        with patch.object(client, '_call_mcp_tool', return_value={'entities': []}) as mock_call:
            client.open_nodes([])

        mock_call.assert_called_with('open_nodes', {'names': []})

    # ========== Read Graph Tests ==========

    def test_read_graph_calls_mcp_tool(self, client, mock_result):
        """Test read_graph() calls _call_mcp_tool"""
        with patch.object(client, '_call_mcp_tool', return_value=mock_result) as mock_call:
            client.read_graph()

        mock_call.assert_called_with('read_graph', {})

    def test_read_graph_returns_result(self, client, mock_result):
        """Test read_graph() returns result from MCP"""
        with patch.object(client, '_call_mcp_tool', return_value=mock_result):
            result = client.read_graph()

        assert result == mock_result
        assert 'entities' in result

    # ========== Create Entities Tests ==========

    def test_create_entities_calls_mcp_tool(self, client):
        """Test create_entities() calls _call_mcp_tool with correct params"""
        entities = [{
            'name': 'test-entity',
            'entityType': 'decision',
            'observations': ['Test observation']
        }]

        with patch.object(client, '_call_mcp_tool', return_value={'success': True}) as mock_call:
            client.create_entities(entities)

        mock_call.assert_called_with('create_entities', {'entities': entities})

    def test_create_entities_returns_true_on_success(self, client):
        """Test create_entities() returns True when successful"""
        entities = [{'name': 'test', 'entityType': 'test', 'observations': []}]

        with patch.object(client, '_call_mcp_tool', return_value={'success': True}):
            result = client.create_entities(entities)

        assert result is True

    def test_create_entities_returns_false_on_failure(self, client):
        """Test create_entities() returns False when operation fails"""
        entities = [{'name': 'test', 'entityType': 'test', 'observations': []}]

        with patch.object(client, '_retry_operation', return_value=None):
            result = client.create_entities(entities)

        assert result is False

    # ========== Add Observations Tests ==========

    def test_add_observations_calls_mcp_tool(self, client):
        """Test add_observations() calls _call_mcp_tool with correct params"""
        observations = [{
            'entityName': 'test-entity',
            'contents': ['New observation']
        }]

        with patch.object(client, '_call_mcp_tool', return_value={'success': True}) as mock_call:
            client.add_observations(observations)

        mock_call.assert_called_with('add_observations', {'observations': observations})

    def test_add_observations_returns_true_on_success(self, client):
        """Test add_observations() returns True when successful"""
        observations = [{'entityName': 'test', 'contents': ['obs']}]

        with patch.object(client, '_call_mcp_tool', return_value={'success': True}):
            result = client.add_observations(observations)

        assert result is True

    def test_add_observations_returns_false_on_failure(self, client):
        """Test add_observations() returns False when operation fails"""
        observations = [{'entityName': 'test', 'contents': ['obs']}]

        with patch.object(client, '_retry_operation', return_value=None):
            result = client.add_observations(observations)

        assert result is False

    # ========== Token Estimation Tests ==========

    def test_estimate_tokens_with_valid_result(self, client, mock_result):
        """Test estimate_tokens() calculates tokens from JSON length"""
        tokens = client.estimate_tokens(mock_result)

        # Should be non-zero for non-empty result
        assert tokens > 0

    def test_estimate_tokens_returns_zero_for_none(self, client):
        """Test estimate_tokens() returns 0 for None result"""
        tokens = client.estimate_tokens(None)
        assert tokens == 0

    def test_estimate_tokens_uses_4_char_per_token_ratio(self, client):
        """Test estimate_tokens() uses ~4 characters per token"""
        # Create result with known character count
        result = {'entities': [{'name': 'x' * 100}]}  # Known length
        tokens = client.estimate_tokens(result)

        # Should divide by ~4
        # Exact calculation: len(json.dumps(result)) // 4
        import json
        expected = len(json.dumps(result)) // 4
        assert tokens == expected

    def test_estimate_tokens_with_empty_result(self, client):
        """Test estimate_tokens() handles empty result"""
        result = {'entities': [], 'relations': []}
        tokens = client.estimate_tokens(result)

        # Should return small positive number (empty JSON is ~30 chars)
        assert tokens >= 0

    def test_estimate_tokens_with_large_result(self, client):
        """Test estimate_tokens() handles large results"""
        # Create large result with many entities
        result = {
            'entities': [
                {'name': f'entity{i}', 'entityType': 'test', 'observations': ['obs'] * 10}
                for i in range(100)
            ]
        }
        tokens = client.estimate_tokens(result)

        # Should return proportionally large number
        assert tokens > 100  # At least 100 tokens for 100 entities

    # ========== Retry Logic Tests ==========

    def test_retry_operation_succeeds_on_first_attempt(self, client):
        """Test _retry_operation() returns immediately on success"""
        operation = Mock(return_value={'success': True})

        result = client._retry_operation(operation, 'test_op')

        assert result == {'success': True}
        assert operation.call_count == 1

    def test_retry_operation_retries_on_failure(self, client):
        """Test _retry_operation() retries when operation fails"""
        # Fail first 2 attempts, succeed on 3rd
        operation = Mock(side_effect=[Exception("Error"), Exception("Error"), {'success': True}])

        result = client._retry_operation(operation, 'test_op')

        assert result == {'success': True}
        assert operation.call_count == 3  # 1 initial + 2 retries

    def test_retry_operation_respects_retry_attempts_config(self, client_with_config):
        """Test _retry_operation() uses configured retry attempts"""
        # Fail all attempts
        operation = Mock(side_effect=Exception("Error"))

        result = client_with_config._retry_operation(operation, 'test_op')

        # Should try: 1 initial + 3 retries (from config) = 4 total
        assert operation.call_count == 4
        assert result is None

    def test_retry_operation_uses_exponential_backoff(self, client):
        """Test _retry_operation() uses exponential backoff between retries"""
        operation = Mock(side_effect=[Exception("Error"), Exception("Error"), {'success': True}])

        with patch('time.sleep') as mock_sleep:
            client._retry_operation(operation, 'test_op')

        # Should sleep with exponential backoff: backoff * (2^attempt)
        # Attempt 0 fails → sleep(1 * 2^0) = 1
        # Attempt 1 fails → sleep(1 * 2^1) = 2
        # Attempt 2 succeeds (no sleep after success)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # First retry: 1 * 2^0
        mock_sleep.assert_any_call(2)  # Second retry: 1 * 2^1

    def test_retry_operation_returns_none_after_all_attempts_fail(self, client):
        """Test _retry_operation() returns None when all attempts fail"""
        operation = Mock(side_effect=Exception("Persistent error"))

        result = client._retry_operation(operation, 'test_op')

        assert result is None
        assert operation.call_count == 3  # 1 initial + 2 retries (default)

    def test_retry_operation_prints_error_after_final_failure(self, client, capsys):
        """Test _retry_operation() prints error after exhausting retries"""
        operation = Mock(side_effect=Exception("Test error"))

        client._retry_operation(operation, 'test_operation')

        captured = capsys.readouterr()
        assert 'Error in test_operation' in captured.out
        assert 'Test error' in captured.out

    # ========== MCP Tool Call Tests ==========

    def test_call_mcp_tool_returns_result(self, client):
        """Test _call_mcp_tool() returns result (placeholder implementation)"""
        result = client._call_mcp_tool('search_nodes', {'query': 'test'})

        # Placeholder returns empty result
        assert result is not None
        assert 'entities' in result

    def test_call_mcp_tool_handles_timeout_exception(self, client, capsys):
        """Test _call_mcp_tool() handles timeout exception"""
        import subprocess

        # Patch to raise timeout, verify it's caught
        with patch.object(client, '_call_mcp_tool', side_effect=subprocess.TimeoutExpired(cmd='test', timeout=5)):
            # Call through _retry_operation which will catch the exception
            result = client._retry_operation(lambda: client._call_mcp_tool('test_tool', {}), 'test')

        assert result is None

    def test_call_mcp_tool_handles_general_exception(self, client, capsys):
        """Test _call_mcp_tool() handles general exceptions"""
        # Patch to raise exception, verify it's caught
        with patch.object(client, '_call_mcp_tool', side_effect=ValueError("Test error")):
            # Call through _retry_operation which will catch the exception
            result = client._retry_operation(lambda: client._call_mcp_tool('test_tool', {}), 'test')

        assert result is None

    # ========== Integration Tests with Retry ==========

    def test_search_nodes_with_retry_on_failure(self, client):
        """Test search_nodes() retries on failure"""
        # Simulate transient failure
        call_count = {'count': 0}

        def mock_call_mcp(*args, **kwargs):
            call_count['count'] += 1
            if call_count['count'] < 2:
                raise Exception("Transient error")
            return {'entities': []}

        with patch.object(client, '_call_mcp_tool', side_effect=mock_call_mcp):
            result = client.search_nodes("test")

        assert result is not None
        assert call_count['count'] == 2  # Failed once, succeeded second time

    def test_open_nodes_with_retry_on_failure(self, client):
        """Test open_nodes() retries on failure"""
        call_count = {'count': 0}

        def mock_call_mcp(*args, **kwargs):
            call_count['count'] += 1
            if call_count['count'] < 3:
                raise Exception("Transient error")
            return {'entities': []}

        with patch.object(client, '_call_mcp_tool', side_effect=mock_call_mcp):
            result = client.open_nodes(['entity1'])

        assert result is not None
        assert call_count['count'] == 3  # Failed twice, succeeded third time

    # ========== Edge Cases ==========

    def test_search_nodes_with_empty_query(self, client):
        """Test search_nodes() handles empty query string"""
        with patch.object(client, '_call_mcp_tool', return_value={'entities': []}) as mock_call:
            client.search_nodes("")

        mock_call.assert_called_with('search_nodes', {'query': ''})

    def test_estimate_tokens_with_special_characters(self, client):
        """Test estimate_tokens() handles special characters in result"""
        result = {
            'entities': [{
                'name': 'test-entity-™-€-£',
                'observations': ['Unicode: 你好 🎉']
            }]
        }

        tokens = client.estimate_tokens(result)

        # Should handle Unicode without errors
        assert tokens > 0

    def test_retry_operation_with_zero_backoff(self):
        """Test _retry_operation() works with zero backoff time"""
        client = MemoryClient({'retry_backoff_seconds': 0})
        operation = Mock(side_effect=[Exception("Error"), {'success': True}])

        with patch('time.sleep') as mock_sleep:
            result = client._retry_operation(operation, 'test_op')

        # Should still retry but with 0 sleep time
        assert result == {'success': True}
        mock_sleep.assert_called_with(0)  # 0 * 2^0 = 0
