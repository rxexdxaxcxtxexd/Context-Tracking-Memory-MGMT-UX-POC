#!/usr/bin/env python3
"""
Resume Point Generator - Enhanced resume points using dependency analysis

This module generates smart resume points by analyzing:
- Cross-file dependencies
- Impact scores
- Test coverage
- Import relationships

Used by save-session.py and resume-session.py for intelligent context restoration.
"""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class FileDependency:
    """Dependency information for a single file (matches dependency_analyzer.py)"""
    file_path: str
    imports_from: List[str]
    used_by: List[str]
    used_by_count: int
    function_calls_to: List[str]
    has_tests: bool
    impact_score: int


def generate_dependency_warnings(dependencies: Dict[str, Dict]) -> List[str]:
    """Generate warnings for high-impact changes

    Args:
        dependencies: Dict mapping file paths to dependency info dicts

    Returns:
        List of warning strings for high-impact files
    """
    warnings = []

    for filepath, dep_dict in dependencies.items():
        # Convert dict to FileDependency for easier access
        dep = FileDependency(**dep_dict) if isinstance(dep_dict, dict) else dep_dict

        # High-impact file warnings
        if dep.impact_score >= 70:
            warnings.append(
                f"[!] {filepath} is used by {dep.used_by_count} file(s) - test thoroughly (impact: {dep.impact_score})"
            )

            # Show which files depend on this
            if dep.used_by:
                top_users = dep.used_by[:3]
                if len(dep.used_by) > 3:
                    warnings.append(f"    Verify: {', '.join(top_users)} (+{len(dep.used_by) - 3} more)")
                else:
                    warnings.append(f"    Verify: {', '.join(top_users)}")

        # Medium-impact files
        elif dep.impact_score >= 50:
            warnings.append(f"[WARNING] {filepath} has moderate impact (score: {dep.impact_score}, used by {dep.used_by_count} files)")

        # Files with many imports (complex dependencies)
        if len(dep.imports_from) > 5:
            imports_preview = ', '.join(dep.imports_from[:3])
            if len(dep.imports_from) > 3:
                imports_preview += f" (+{len(dep.imports_from) - 3} more)"
            warnings.append(f"Verify {filepath} still works with dependencies: {imports_preview}")

    return warnings


def generate_test_suggestions(dependencies: Dict[str, Dict]) -> List[str]:
    """Generate test-related suggestions

    Args:
        dependencies: Dict mapping file paths to dependency info dicts

    Returns:
        List of test suggestion strings
    """
    suggestions = []

    # Files with existing tests
    files_with_tests = []
    files_without_tests = []

    for filepath, dep_dict in dependencies.items():
        dep = FileDependency(**dep_dict) if isinstance(dep_dict, dict) else dep_dict

        if dep.has_tests:
            files_with_tests.append(filepath)
        else:
            files_without_tests.append(filepath)

    # Suggest running tests for files with test coverage
    if files_with_tests:
        if len(files_with_tests) <= 3:
            suggestions.append(f"Run tests for: {', '.join(files_with_tests)}")
        else:
            preview = ', '.join(files_with_tests[:3])
            suggestions.append(f"Run tests for: {preview} (+{len(files_with_tests) - 3} more files)")

    # Suggest writing tests for files without coverage
    if files_without_tests:
        high_impact_no_tests = [
            f for f in files_without_tests
            if dependencies[f].get('impact_score', 0) >= 50
        ]

        if high_impact_no_tests:
            if len(high_impact_no_tests) <= 2:
                suggestions.append(f"[!] Consider writing tests for: {', '.join(high_impact_no_tests)}")
            else:
                preview = ', '.join(high_impact_no_tests[:2])
                suggestions.append(f"[!] Consider writing tests for: {preview} (+{len(high_impact_no_tests) - 2} more)")

    return suggestions


def generate_impact_summary(dependencies: Dict[str, Dict]) -> List[str]:
    """Generate summary of overall impact

    Args:
        dependencies: Dict mapping file paths to dependency info dicts

    Returns:
        List of summary strings
    """
    if not dependencies:
        return []

    summary = []

    # Count by impact level
    high_impact = [f for f, d in dependencies.items() if d.get('impact_score', 0) >= 70]
    medium_impact = [f for f, d in dependencies.items() if 50 <= d.get('impact_score', 0) < 70]

    # Overall summary
    if high_impact:
        summary.append(f"--- Impact Analysis: {len(high_impact)} high-impact file(s), {len(medium_impact)} medium-impact ---")
    elif medium_impact:
        summary.append(f"--- Impact Analysis: {len(medium_impact)} medium-impact file(s) ---")
    else:
        summary.append("--- Impact Analysis: Low-impact changes ---")

    return summary


def enhance_resume_points(existing_points: List[str], dependencies: Dict[str, Dict]) -> List[str]:
    """Enhance resume points with dependency context

    Args:
        existing_points: List of existing resume points (from AST analysis, TODOs, etc.)
        dependencies: Dict mapping file paths to dependency info dicts

    Returns:
        Enhanced list of resume points with dependency warnings
    """
    if not dependencies:
        return existing_points

    enhanced = []

    # Start with impact summary
    summary = generate_impact_summary(dependencies)
    enhanced.extend(summary)

    # Add dependency warnings (high priority)
    warnings = generate_dependency_warnings(dependencies)
    enhanced.extend(warnings)

    # Add test suggestions
    test_suggestions = generate_test_suggestions(dependencies)
    enhanced.extend(test_suggestions)

    # Add original resume points (from AST, TODOs, etc.)
    if existing_points:
        enhanced.append("--- Code-Level Resume Points ---")
        enhanced.extend(existing_points)

    # Limit to reasonable number
    return enhanced[:25]  # Top 25 most important points


def format_dependency_info(dependencies: Dict[str, Dict]) -> str:
    """Format dependency information for display

    Args:
        dependencies: Dict mapping file paths to dependency info dicts

    Returns:
        Formatted string for terminal display
    """
    if not dependencies:
        return "No dependency analysis available"

    lines = []
    lines.append("\n" + "="*70)
    lines.append("DEPENDENCY ANALYSIS")
    lines.append("="*70)

    # Sort by impact score (highest first)
    sorted_deps = sorted(
        dependencies.items(),
        key=lambda x: x[1].get('impact_score', 0),
        reverse=True
    )

    for filepath, dep_dict in sorted_deps:
        dep = FileDependency(**dep_dict) if isinstance(dep_dict, dict) else dep_dict

        lines.append(f"\n{filepath}")
        lines.append(f"  Impact Score: {dep.impact_score}/100")
        lines.append(f"  Used by: {dep.used_by_count} file(s)")

        if dep.used_by:
            users = ', '.join(dep.used_by[:3])
            if len(dep.used_by) > 3:
                users += f" (+{len(dep.used_by) - 3} more)"
            lines.append(f"    -> {users}")

        if dep.imports_from:
            imports = ', '.join(dep.imports_from[:3])
            if len(dep.imports_from) > 3:
                imports += f" (+{len(dep.imports_from) - 3} more)"
            lines.append(f"  Imports: {imports}")

        lines.append(f"  Has tests: {'Yes' if dep.has_tests else 'No'}")

    lines.append("="*70)

    return '\n'.join(lines)
