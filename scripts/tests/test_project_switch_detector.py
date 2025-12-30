"""
Tests for Project Switch Detector

Tests project context switching detection, including directory changes,
git remote URL changes, branch switches, confidence scoring, and ProjectTracker integration.

Author: Context-Aware Memory System
Date: 2025-12-29
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from memory_detectors.project_switch_detector import ProjectSwitchDetector
from memory_detectors import TriggerResult


class TestProjectSwitchDetector:
    """Test suite for ProjectSwitchDetector"""

    @pytest.fixture
    def mock_tracker(self):
        """Create mock ProjectTracker"""
        tracker = Mock()
        tracker.get_active_project = Mock(return_value=None)
        tracker.set_active_project = Mock()
        tracker.has_uncommitted_changes = Mock(return_value=False)
        return tracker

    @pytest.fixture
    def detector(self, mock_tracker):
        """Create detector instance with mocked tracker"""
        config = {
            'enabled': True,
            'priority': 1,
            'detect_branch_switch': True,
            'major_branches': ['main', 'master', 'develop', 'development']
        }
        with patch('memory_detectors.project_switch_detector.ProjectTracker', return_value=mock_tracker):
            detector = ProjectSwitchDetector(config)
        return detector

    @pytest.fixture
    def context_with_project(self):
        """Create test context with project metadata"""
        return {
            'current_project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',
                'git_branch': 'main'
            },
            'session_id': 'test-session',
            'cwd': '/home/user/test-project'
        }

    # ========== Initialization Tests ==========

    def test_initialization_with_defaults(self):
        """Test detector initializes with default settings"""
        config = {'enabled': True}
        with patch('memory_detectors.project_switch_detector.ProjectTracker'):
            detector = ProjectSwitchDetector(config)

        assert detector.enabled is True
        assert detector.priority == 1  # Highest priority
        assert detector.name == "project_switch_detector"
        assert detector.detect_branch_switch is True
        assert 'main' in detector.major_branches
        assert 'master' in detector.major_branches

    def test_initialization_with_custom_config(self):
        """Test detector initializes with custom configuration"""
        config = {
            'enabled': True,
            'priority': 5,
            'detect_branch_switch': False,
            'major_branches': ['production', 'staging']
        }
        with patch('memory_detectors.project_switch_detector.ProjectTracker'):
            detector = ProjectSwitchDetector(config)

        assert detector.priority == 5
        assert detector.detect_branch_switch is False
        assert detector.major_branches == ['production', 'staging']

    def test_priority_defaults_to_one_when_missing(self):
        """Test priority defaults to 1 (highest) when not specified"""
        config = {'enabled': True}
        with patch('memory_detectors.project_switch_detector.ProjectTracker'):
            detector = ProjectSwitchDetector(config)

        assert detector.priority == 1

    # ========== First Run Tests ==========

    def test_first_run_no_previous_project(self, detector, context_with_project, mock_tracker):
        """Test first run with no previous active project"""
        mock_tracker.get_active_project.return_value = None
        result = detector.evaluate("Any prompt", context_with_project)

        assert result is None  # No trigger on first run
        mock_tracker.set_active_project.assert_called_once()  # But updates tracker

    def test_no_current_project_in_context(self, detector, mock_tracker):
        """Test returns None when context has no current_project"""
        context = {'session_id': 'test', 'cwd': '/home/user'}
        result = detector.evaluate("Any prompt", context)

        assert result is None
        mock_tracker.get_active_project.assert_not_called()

    def test_malformed_active_state_no_project_key(self, detector, context_with_project, mock_tracker):
        """Test handles malformed active state gracefully"""
        mock_tracker.get_active_project.return_value = {'updated_at': '2025-01-01'}
        result = detector.evaluate("Any prompt", context_with_project)

        assert result is None

    # ========== Directory Switch Detection Tests ==========

    def test_directory_switch_detected(self, detector, context_with_project, mock_tracker):
        """Test detects directory change (different projects)"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': 'https://github.com/user/old-project.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is not None
        assert result.triggered is True
        assert result.query_type == "project_context"
        assert result.query_params['switch_type'] == 'directory'
        assert 'test-project' in result.query_params['project']

    def test_directory_switch_confidence_very_high(self, detector, context_with_project, mock_tracker):
        """Test directory switch gets very high confidence (0.95)"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': '',
                'git_branch': ''
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result.confidence >= 0.95

    def test_directory_switch_with_git_remote_boost(self, detector, context_with_project, mock_tracker):
        """Test directory switch with git remote gets confidence boost"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': 'https://github.com/user/old-project.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result.confidence >= 0.95  # 0.95 + 0.05 boost = 1.0 (capped)

    def test_directory_switch_reason_string(self, detector, context_with_project, mock_tracker):
        """Test directory switch generates correct reason string"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': '',
                'git_branch': ''
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert 'Switched projects' in result.reason
        assert 'old-project' in result.reason
        assert 'test-project' in result.reason

    def test_same_directory_no_trigger(self, detector, context_with_project, mock_tracker):
        """Test same directory doesn't trigger"""
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is None  # Same project, no switch

    # ========== Remote URL Switch Detection Tests ==========

    def test_remote_url_change_detected(self, detector, context_with_project, mock_tracker):
        """Test detects git remote URL change (same directory)"""
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/old-repo.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['switch_type'] == 'remote'

    def test_remote_url_change_confidence_high(self, detector, context_with_project, mock_tracker):
        """Test remote URL change gets high confidence (0.90)"""
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/old-repo.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result.confidence >= 0.90

    def test_remote_url_normalization_git_suffix(self, detector, context_with_project, mock_tracker):
        """Test remote URLs are normalized (.git suffix ignored)"""
        context_with_project['current_project']['git_remote_url'] = 'https://github.com/user/test-project'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',  # Has .git
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is None  # Same remote (after normalization)

    def test_remote_url_normalization_http_vs_https(self, detector, context_with_project, mock_tracker):
        """Test remote URLs normalize http to https"""
        context_with_project['current_project']['git_remote_url'] = 'http://github.com/user/test-project.git'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',  # https
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is None  # Same remote (after normalization)

    def test_remote_url_change_reason_string(self, detector, context_with_project, mock_tracker):
        """Test remote URL change generates correct reason string"""
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/old-repo.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert 'Changed git remote' in result.reason
        assert 'github.com' in result.reason

    # ========== Branch Switch Detection Tests ==========

    def test_branch_switch_to_major_branch_detected(self, detector, context_with_project, mock_tracker):
        """Test detects branch switch to major branch"""
        context_with_project['current_project']['git_branch'] = 'develop'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',
                'git_branch': 'main'  # Switching from main -> develop
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is not None
        assert result.triggered is True
        assert result.query_params['switch_type'] == 'branch'

    def test_branch_switch_from_major_branch_detected(self, detector, context_with_project, mock_tracker):
        """Test detects branch switch from major branch"""
        context_with_project['current_project']['git_branch'] = 'feature-branch'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',
                'git_branch': 'main'  # Switching from main -> feature-branch
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is not None
        assert result.triggered is True

    def test_branch_switch_non_major_branches_ignored(self, detector, context_with_project, mock_tracker):
        """Test non-major branch switches are ignored"""
        context_with_project['current_project']['git_branch'] = 'feature-2'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',
                'git_branch': 'feature-1'  # Neither is major branch
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is None  # Non-major branch switch ignored

    def test_branch_switch_confidence_moderate(self, detector, context_with_project, mock_tracker):
        """Test branch switch gets moderate confidence (0.75)"""
        context_with_project['current_project']['git_branch'] = 'develop'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result.confidence >= 0.75
        assert result.confidence < 0.90  # Lower than directory/remote switches

    def test_branch_switch_disabled_no_trigger(self, detector, context_with_project, mock_tracker):
        """Test branch switch detection can be disabled"""
        detector.detect_branch_switch = False
        context_with_project['current_project']['git_branch'] = 'develop'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result is None  # Branch detection disabled

    def test_branch_switch_reason_string(self, detector, context_with_project, mock_tracker):
        """Test branch switch generates correct reason string"""
        context_with_project['current_project']['git_branch'] = 'develop'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': 'https://github.com/user/test-project.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert 'Switched branch' in result.reason
        assert 'main' in result.reason
        assert 'develop' in result.reason

    # ========== Switch Priority Tests ==========

    def test_directory_switch_takes_priority_over_remote(self, detector, context_with_project, mock_tracker):
        """Test directory switch detected first (higher priority than remote)"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',  # Different path
                'git_remote_url': 'https://github.com/user/old-repo.git',  # Different remote
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result.query_params['switch_type'] == 'directory'  # Directory wins

    def test_remote_switch_takes_priority_over_branch(self, detector, context_with_project, mock_tracker):
        """Test remote switch detected before branch switch"""
        context_with_project['current_project']['git_branch'] = 'develop'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',  # Same path
                'git_remote_url': 'https://github.com/user/old-repo.git',  # Different remote
                'git_branch': 'main'  # Different branch
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result.query_params['switch_type'] == 'remote'  # Remote wins over branch

    # ========== URL Shortening Tests ==========

    def test_shorten_github_url(self, detector):
        """Test GitHub URL shortening"""
        url = 'https://github.com/user/repo.git'
        short = detector._shorten_remote_url(url)
        assert short == 'github.com/user/repo'

    def test_shorten_gitlab_url(self, detector):
        """Test GitLab URL shortening"""
        url = 'https://gitlab.com/user/repo.git'
        short = detector._shorten_remote_url(url)
        assert short == 'gitlab.com/user/repo'

    def test_shorten_bitbucket_url(self, detector):
        """Test Bitbucket URL shortening"""
        url = 'https://bitbucket.org/user/repo.git'
        short = detector._shorten_remote_url(url)
        assert short == 'bitbucket.org/user/repo'

    def test_shorten_ssh_github_url(self, detector):
        """Test SSH GitHub URL shortening"""
        url = 'git@github.com:user/repo.git'
        short = detector._shorten_remote_url(url)
        assert short == 'github.com/user/repo'

    def test_shorten_unknown_url_truncates(self, detector):
        """Test unknown URLs are truncated to 50 chars"""
        url = 'https://some-custom-git-server.com/very/long/path/to/repository.git'
        short = detector._shorten_remote_url(url)
        assert len(short) <= 50

    # ========== ProjectTracker Integration Tests ==========

    def test_tracker_state_updated_on_first_run(self, detector, context_with_project, mock_tracker):
        """Test tracker state is updated on first run"""
        mock_tracker.get_active_project.return_value = None
        detector.evaluate("Any prompt", context_with_project)

        mock_tracker.set_active_project.assert_called_once()
        call_args = mock_tracker.set_active_project.call_args
        assert call_args[1]['project_metadata'] == context_with_project['current_project']

    def test_tracker_state_updated_after_switch(self, detector, context_with_project, mock_tracker):
        """Test tracker state is updated after detecting switch"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': '',
                'git_branch': ''
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        detector.evaluate("Any prompt", context_with_project)

        mock_tracker.set_active_project.assert_called_once()

    def test_tracker_state_updated_even_without_switch(self, detector, context_with_project, mock_tracker):
        """Test tracker timestamp updates even when no switch detected"""
        previous_state = {
            'project': context_with_project['current_project'].copy()
        }
        mock_tracker.get_active_project.return_value = previous_state

        detector.evaluate("Any prompt", context_with_project)

        mock_tracker.set_active_project.assert_called_once()

    def test_tracker_has_uncommitted_changes_called(self, detector, context_with_project, mock_tracker):
        """Test tracker checks for uncommitted changes"""
        mock_tracker.get_active_project.return_value = None
        mock_tracker.has_uncommitted_changes.return_value = True

        detector.evaluate("Any prompt", context_with_project)

        mock_tracker.has_uncommitted_changes.assert_called_once()
        call_args = mock_tracker.set_active_project.call_args
        assert call_args[1]['has_uncommitted'] is True

    def test_tracker_error_doesnt_crash_detector(self, detector, context_with_project, mock_tracker):
        """Test detector handles tracker errors gracefully"""
        mock_tracker.get_active_project.return_value = None
        mock_tracker.has_uncommitted_changes.side_effect = Exception("Git not found")

        # Should not raise exception
        result = detector.evaluate("Any prompt", context_with_project)
        assert result is None  # First run, no previous project

    # ========== Confidence Calculation Tests ==========

    def test_confidence_git_remote_boost(self, detector, context_with_project, mock_tracker):
        """Test confidence gets +0.05 boost when git remote present"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': '',  # No git remote
                'git_branch': ''
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        # Directory switch (0.95) + git remote boost (0.05) = 1.0 (capped)
        assert result.confidence >= 0.95

    def test_confidence_capped_at_one(self, detector, context_with_project, mock_tracker):
        """Test confidence is capped at 1.0"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': 'https://github.com/user/old-project.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        # Even with boost, should not exceed 1.0
        assert result.confidence <= 1.0

    # ========== Query Parameters Tests ==========

    def test_query_params_include_project_metadata(self, detector, context_with_project, mock_tracker):
        """Test query_params includes all project metadata"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': '',
                'git_branch': ''
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert 'project' in result.query_params
        assert 'project_path' in result.query_params
        assert 'git_remote' in result.query_params
        assert 'branch' in result.query_params
        assert 'switch_type' in result.query_params

    def test_query_params_values_match_current_project(self, detector, context_with_project, mock_tracker):
        """Test query_params values come from current project (not previous)"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': 'https://github.com/user/old-project.git',
                'git_branch': 'old-branch'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        # Should have current project info, not previous
        assert result.query_params['project'] == 'test-project'
        assert result.query_params['branch'] == 'main'
        assert 'test-project' in result.query_params['git_remote']

    # ========== Trigger Result Structure Tests ==========

    def test_trigger_result_structure(self, detector, context_with_project, mock_tracker):
        """Test TriggerResult has all required fields"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': '',
                'git_branch': ''
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert hasattr(result, 'triggered')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'estimated_tokens')
        assert hasattr(result, 'query_type')
        assert hasattr(result, 'query_params')
        assert hasattr(result, 'reason')

        assert result.triggered is True
        assert 0.0 <= result.confidence <= 1.0
        assert result.estimated_tokens == 200
        assert result.query_type == "project_context"

    def test_estimated_tokens_is_200(self, detector, context_with_project, mock_tracker):
        """Test estimated tokens for project context is 200"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': '',
                'git_branch': ''
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context_with_project)

        assert result.estimated_tokens == 200

    # ========== Edge Cases ==========

    def test_missing_absolute_path_in_both_projects(self, detector, context_with_project, mock_tracker):
        """Test handles missing absolute_path gracefully"""
        del context_with_project['current_project']['absolute_path']
        previous_state = {
            'project': {
                'name': 'old-project',
                'git_remote_url': 'https://github.com/user/old-project.git',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        # Should detect remote switch instead
        result = detector.evaluate("Any prompt", context_with_project)

        assert result is not None
        assert result.query_params['switch_type'] == 'remote'

    def test_missing_git_remote_in_both_projects(self, detector, context_with_project, mock_tracker):
        """Test handles missing git_remote gracefully"""
        context_with_project['current_project']['git_remote_url'] = ''
        context_with_project['current_project']['git_branch'] = 'develop'
        previous_state = {
            'project': {
                'name': 'test-project',
                'absolute_path': '/home/user/test-project',
                'git_remote_url': '',
                'git_branch': 'main'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        # Should detect branch switch
        result = detector.evaluate("Any prompt", context_with_project)

        assert result is not None
        assert result.query_params['switch_type'] == 'branch'

    def test_empty_project_metadata(self, detector, mock_tracker):
        """Test handles empty project metadata"""
        context = {
            'current_project': {},
            'session_id': 'test'
        }
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project'
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        result = detector.evaluate("Any prompt", context)

        # No valid metadata to compare, no switch detected
        assert result is None

    def test_prompt_text_not_used_for_detection(self, detector, context_with_project, mock_tracker):
        """Test prompt text doesn't affect project switch detection"""
        previous_state = {
            'project': {
                'name': 'old-project',
                'absolute_path': '/home/user/old-project',
                'git_remote_url': '',
                'git_branch': ''
            }
        }
        mock_tracker.get_active_project.return_value = previous_state

        # Different prompts should produce same result
        result1 = detector.evaluate("Remember our architecture decision", context_with_project)
        result2 = detector.evaluate("What is the weather?", context_with_project)

        assert result1.triggered == result2.triggered
        assert result1.query_params['switch_type'] == result2.query_params['switch_type']
