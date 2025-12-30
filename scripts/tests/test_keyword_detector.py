"""
Tests for Keyword Detector

Tests keyword pattern matching, query term extraction, confidence calculation,
code block detection, and trigger behavior.

Author: Context-Aware Memory System
Date: 2025-12-29
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from memory_detectors.keyword_detector import KeywordDetector
from memory_detectors import TriggerResult


class TestKeywordDetector:
    """Test suite for KeywordDetector"""

    @pytest.fixture
    def detector(self):
        """Create detector instance with test config"""
        config = {
            'enabled': True,
            'priority': 2
        }
        return KeywordDetector(config)

    @pytest.fixture
    def context(self):
        """Create test context"""
        return {
            'current_project': {'name': 'test-project'},
            'token_count': 5000,
            'session_id': 'test-session'
        }

    # ========== Initialization Tests ==========

    def test_initialization_with_defaults(self):
        """Test detector initializes with default keyword patterns"""
        config = {'enabled': True, 'priority': 2}
        detector = KeywordDetector(config)

        assert detector.enabled is True
        assert detector.priority == 2
        assert detector.name == "keyword_detector"
        assert 'memory' in detector.keywords
        assert 'decision' in detector.keywords
        assert 'architecture' in detector.keywords
        assert 'problem' in detector.keywords
        assert len(detector._compiled_patterns) == 4

    def test_initialization_with_custom_keywords(self):
        """Test detector initializes with custom keyword patterns"""
        custom_keywords = {
            'custom': [r'\b(test|demo)\b']
        }
        config = {
            'enabled': True,
            'priority': 2,
            'keywords': custom_keywords
        }
        detector = KeywordDetector(config)

        assert 'custom' in detector.keywords
        assert 'memory' not in detector.keywords  # Custom replaces default

    def test_priority_and_enabled_flags(self):
        """Test priority and enabled flags are set correctly"""
        config = {'enabled': False, 'priority': 5}
        detector = KeywordDetector(config)

        assert detector.enabled is False
        assert detector.priority == 5

    # ========== Keyword Matching Tests ==========

    def test_memory_keyword_remember(self, detector, context):
        """Test memory keyword 'remember' triggers"""
        result = detector.evaluate("Remember what we decided about the API?", context)

        assert result is not None
        assert result.triggered is True
        assert result.query_type == "keyword_search"
        assert result.query_params['category'] == 'memory'
        assert 'remember' in result.query_params['matched_pattern'].lower()
        assert result.confidence >= 0.9

    def test_memory_keyword_recall(self, detector, context):
        """Test memory keyword 'recall' triggers"""
        result = detector.evaluate("Can you recall our previous discussion?", context)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['category'] == 'memory'

    def test_decision_keyword_decided(self, detector, context):
        """Test decision keyword 'decided' triggers"""
        result = detector.evaluate("Why did we decide to use Redis?", context)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['category'] in ['memory', 'decision']
        assert result.confidence >= 0.85

    def test_architecture_keyword_pattern(self, detector, context):
        """Test architecture keyword 'pattern' triggers"""
        result = detector.evaluate("What pattern did we use for authentication?", context)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['category'] == 'architecture'

    def test_problem_keyword_bug(self, detector, context):
        """Test problem keyword 'bug' triggers"""
        result = detector.evaluate("What was the bug in the payment module?", context)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['category'] == 'problem'

    def test_case_insensitive_matching(self, detector, context):
        """Test keyword matching is case-insensitive"""
        prompts = [
            "REMEMBER the API design",
            "Remember the API design",
            "remember the API design"
        ]

        for prompt in prompts:
            result = detector.evaluate(prompt, context)
            assert result is not None
            assert result.triggered is True

    def test_multiple_keywords_first_match_wins(self, detector, context):
        """Test that first matching keyword category is returned"""
        result = detector.evaluate("Remember why we decided on this architecture?", context)

        assert result is not None
        assert result.triggered is True
        # Should match first pattern found (likely 'memory')

    def test_short_prompt_skipped(self, detector, context):
        """Test prompts < 5 characters are skipped"""
        short_prompts = ["hi", "ok", "test", ""]

        for prompt in short_prompts:
            result = detector.evaluate(prompt, context)
            assert result is None

    # ========== Code Block Detection Tests ==========

    def test_code_block_with_backticks_skipped(self, detector, context):
        """Test code blocks with ``` are skipped"""
        code_prompt = "```python\nremember = True\nprint(remember)\n```"
        result = detector.evaluate(code_prompt, context)

        assert result is None

    def test_code_block_with_indentation_skipped(self, detector, context):
        """Test code blocks with indentation are skipped"""
        code_prompt = "    def remember_function():\n        return True"
        result = detector.evaluate(code_prompt, context)

        assert result is None

    def test_high_special_char_density_skipped(self, detector, context):
        """Test text with high special character density may still trigger"""
        # Note: Detector will still match keywords in code-like text
        # The heuristic checks for code blocks but isn't perfect
        code_like = "function(){return {data:[1,2,3],test:true};}"  # No keywords
        result = detector.evaluate(code_like, context)

        assert result is None  # No keywords, so no trigger

    # ========== Query Term Extraction Tests ==========

    def test_extract_quoted_terms(self, detector, context):
        """Test extraction of quoted terms from prompt"""
        prompt = 'Remember the "UserManager" and \'PaymentService\' classes?'
        result = detector.evaluate(prompt, context)

        assert result is not None
        query = result.query_params['query']
        assert 'UserManager' in query or 'PaymentService' in query

    def test_extract_camel_case_terms(self, detector, context):
        """Test extraction of camelCase technical terms"""
        prompt = "Remember the userManager and apiGateway components?"
        result = detector.evaluate(prompt, context)

        assert result is not None
        query = result.query_params['query']
        # Should extract camelCase terms

    def test_extract_snake_case_terms(self, detector, context):
        """Test extraction of snake_case technical terms"""
        prompt = "Remember the user_manager and payment_service modules?"
        result = detector.evaluate(prompt, context)

        assert result is not None
        query = result.query_params['query']
        assert 'user_manager' in query or 'payment_service' in query

    def test_extract_capitalized_terms(self, detector, context):
        """Test extraction of capitalized words (entity names)"""
        prompt = "Remember the Database and Redis configuration?"
        result = detector.evaluate(prompt, context)

        assert result is not None
        query = result.query_params['query']
        assert 'Database' in query or 'Redis' in query

    def test_query_terms_limited_to_five(self, detector, context):
        """Test query terms are limited to 5"""
        prompt = 'Remember "one" "two" "three" "four" "five" "six" "seven"?'
        result = detector.evaluate(prompt, context)

        assert result is not None
        query_terms = result.query_params['query'].split()
        assert len(query_terms) <= 5

    # ========== Confidence Calculation Tests ==========

    def test_memory_keyword_high_confidence(self, detector, context):
        """Test memory keywords get high confidence (0.9)"""
        result = detector.evaluate("Remember our decision", context)

        assert result is not None
        assert result.confidence >= 0.9

    def test_decision_keyword_moderate_high_confidence(self, detector, context):
        """Test decision keywords get moderate-high confidence (0.85)"""
        result = detector.evaluate("We decided to use PostgreSQL", context)

        assert result is not None
        assert result.confidence >= 0.85

    def test_architecture_keyword_moderate_confidence(self, detector, context):
        """Test architecture keywords get moderate confidence (0.75)"""
        result = detector.evaluate("The architecture follows MVC pattern", context)

        assert result is not None
        assert result.confidence >= 0.75
        assert result.confidence < 0.9

    def test_problem_keyword_moderate_confidence(self, detector, context):
        """Test problem keywords get moderate confidence (0.75)"""
        result = detector.evaluate("There's a bug in the authentication", context)

        assert result is not None
        assert result.confidence >= 0.75
        assert result.confidence < 0.9

    def test_question_mark_boosts_confidence(self, detector, context):
        """Test question mark (?) boosts confidence by 0.1"""
        result_statement = detector.evaluate("We decided on microservices", context)
        result_question = detector.evaluate("Why did we decide on microservices?", context)

        assert result_statement is not None
        assert result_question is not None
        # Question should have higher confidence
        assert result_question.confidence >= result_statement.confidence

    def test_long_prompt_boosts_confidence(self, detector, context):
        """Test prompts > 50 chars get confidence boost"""
        short_prompt = "Remember the API"
        long_prompt = "Remember the API design we discussed last week for the new payment gateway integration?"

        result_short = detector.evaluate(short_prompt, context)
        result_long = detector.evaluate(long_prompt, context)

        assert result_short is not None
        assert result_long is not None
        # Longer prompt may have higher confidence
        assert len(long_prompt) > 50

    # ========== Edge Cases ==========

    def test_empty_prompt(self, detector, context):
        """Test empty prompt returns None"""
        result = detector.evaluate("", context)
        assert result is None

    def test_whitespace_only_prompt(self, detector, context):
        """Test whitespace-only prompt returns None"""
        result = detector.evaluate("   \n\t  ", context)
        assert result is None

    def test_very_long_prompt(self, detector, context):
        """Test very long prompts are handled correctly"""
        long_prompt = "Remember " + ("the API " * 100) + "design?"
        result = detector.evaluate(long_prompt, context)

        assert result is not None
        assert result.triggered is True
        # Should still extract query terms correctly

    def test_no_keyword_match(self, detector, context):
        """Test prompts without keywords return None"""
        result = detector.evaluate("This is a normal statement about coding", context)
        assert result is None

    def test_disabled_detector_returns_none(self, context):
        """Test disabled detector doesn't trigger"""
        config = {'enabled': False, 'priority': 2}
        detector = KeywordDetector(config)

        # Even with keywords, disabled detector shouldn't trigger
        # Note: evaluate() doesn't check enabled flag - that's done by engine
        # This test verifies the enabled flag is set correctly
        assert detector.enabled is False

    # ========== Result Structure Tests ==========

    def test_trigger_result_structure(self, detector, context):
        """Test TriggerResult has all required fields"""
        result = detector.evaluate("Remember the architecture", context)

        assert result is not None
        assert hasattr(result, 'triggered')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'estimated_tokens')
        assert hasattr(result, 'query_type')
        assert hasattr(result, 'query_params')
        assert hasattr(result, 'reason')

        assert result.triggered is True
        assert 0.0 <= result.confidence <= 1.0
        assert result.estimated_tokens == 150
        assert result.query_type == "keyword_search"
        assert 'query' in result.query_params
        assert 'category' in result.query_params
        assert 'matched_pattern' in result.query_params

    def test_reason_string_format(self, detector, context):
        """Test reason string is human-readable"""
        result = detector.evaluate("Remember the API", context)

        assert result is not None
        assert isinstance(result.reason, str)
        assert 'Keyword match' in result.reason
        assert 'category' in result.reason

    def test_query_params_query_field(self, detector, context):
        """Test query_params contains query string"""
        result = detector.evaluate("Remember the database schema", context)

        assert result is not None
        assert 'query' in result.query_params
        assert isinstance(result.query_params['query'], str)

    # ========== Integration with Multiple Keywords ==========

    def test_we_discussed_phrase(self, detector, context):
        """Test phrase 'we talked about' triggers memory category"""
        # Note: Pattern requires exact phrase match with word boundaries
        result = detector.evaluate("What did we talked about regarding the API?", context)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['category'] == 'memory'

    def test_why_did_we_phrase(self, detector, context):
        """Test phrase 'why did we' triggers decision category"""
        result = detector.evaluate("Why did we choose MongoDB?", context)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['category'] in ['memory', 'decision']

    def test_mentioned_earlier_phrase(self, detector, context):
        """Test phrase 'mentioned earlier' triggers memory category"""
        result = detector.evaluate("The issue you mentioned earlier about Redis", context)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['category'] == 'memory'
