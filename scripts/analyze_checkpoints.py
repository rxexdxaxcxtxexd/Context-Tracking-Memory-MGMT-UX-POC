#!/usr/bin/env python3
"""
Checkpoint Analysis Script
Analyzes all checkpoint files to understand data patterns and prepare for migration.

Purpose:
- Parse all 1,810+ checkpoint JSON files
- Calculate statistics (date range, file change counts, field usage)
- Identify last 90 days of checkpoints
- Flag high-value older checkpoints for migration
- Generate migration priorities and sample extracts
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import traceback

class CheckpointAnalyzer:
    """Analyzes checkpoint files and generates migration reports."""

    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoints = []
        self.errors = []
        self.stats = {
            'total_count': 0,
            'parsed_successfully': 0,
            'parse_errors': 0,
            'oldest_date': None,
            'newest_date': None,
            'date_range_days': 0,
            'last_90_days_count': 0,
            'high_value_older_count': 0,
            'by_project': defaultdict(int),
            'field_usage': Counter(),
            'total_file_changes': 0,
            'avg_file_changes': 0,
            'max_file_changes': 0,
            'avg_size_kb': 0,
            'decisions_count': 0,
            'problems_count': 0,
            'manual_descriptions': 0,
        }
        self.priority_lists = {
            'priority_1_recent': [],
            'priority_2_high_value': [],
            'priority_3_archive': []
        }
        self.samples = {
            'recent': None,
            'high_file_changes': None,
            'with_decisions': None,
            'with_problems': None,
            'auto_generated': None
        }

    def analyze_all(self) -> Dict[str, Any]:
        """Main analysis workflow."""
        print(f"Analyzing checkpoints in: {self.checkpoint_dir}")
        print("-" * 80)

        # Step 1: Find all checkpoint files
        checkpoint_files = self._find_checkpoint_files()
        self.stats['total_count'] = len(checkpoint_files)
        print(f"Found {self.stats['total_count']} checkpoint files")

        # Step 2: Parse all checkpoints
        print("\nParsing checkpoint files...")
        self._parse_checkpoints(checkpoint_files)

        # Step 3: Calculate statistics
        print("\nCalculating statistics...")
        self._calculate_statistics()

        # Step 4: Identify priorities
        print("\nIdentifying migration priorities...")
        self._identify_priorities()

        # Step 5: Extract samples
        print("\nExtracting sample checkpoints...")
        self._extract_samples()

        # Step 6: Generate reports
        print("\nGenerating reports...")
        self._generate_reports()

        return {
            'stats': self.stats,
            'priority_lists': self.priority_lists,
            'samples': self.samples,
            'errors': self.errors
        }

    def _find_checkpoint_files(self) -> List[Path]:
        """Find all checkpoint JSON files."""
        return sorted(self.checkpoint_dir.glob("checkpoint-*.json"))

    def _parse_checkpoints(self, files: List[Path]):
        """Parse all checkpoint files."""
        for i, file_path in enumerate(files, 1):
            if i % 100 == 0:
                print(f"  Parsed {i}/{len(files)} files...")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Add file metadata
                data['_file_path'] = str(file_path)
                data['_file_size_bytes'] = file_path.stat().st_size
                data['_file_mtime'] = datetime.fromtimestamp(file_path.stat().st_mtime)

                self.checkpoints.append(data)
                self.stats['parsed_successfully'] += 1

            except Exception as e:
                self.stats['parse_errors'] += 1
                self.errors.append({
                    'file': str(file_path),
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })

        print(f"  Successfully parsed: {self.stats['parsed_successfully']}")
        print(f"  Parse errors: {self.stats['parse_errors']}")

    def _calculate_statistics(self):
        """Calculate comprehensive statistics."""
        if not self.checkpoints:
            print("  No checkpoints to analyze!")
            return

        # Sort by timestamp
        self.checkpoints.sort(key=lambda x: x.get('timestamp', ''))

        # Date range
        timestamps = [datetime.fromisoformat(cp['timestamp'])
                     for cp in self.checkpoints if cp.get('timestamp')]
        if timestamps:
            self.stats['oldest_date'] = min(timestamps)
            self.stats['newest_date'] = max(timestamps)
            self.stats['date_range_days'] = (
                self.stats['newest_date'] - self.stats['oldest_date']
            ).days

        # 90-day cutoff
        cutoff_date = datetime.now() - timedelta(days=90)

        # File change stats
        file_change_counts = []

        # Per-checkpoint analysis
        for cp in self.checkpoints:
            # Timestamp analysis
            ts = cp.get('timestamp')
            if ts:
                cp_date = datetime.fromisoformat(ts)
                if cp_date >= cutoff_date:
                    self.stats['last_90_days_count'] += 1

            # Project tracking
            project_name = self._extract_project_name(cp)
            if project_name:
                self.stats['by_project'][project_name] += 1

            # Field usage tracking
            for field in cp.keys():
                if not field.startswith('_'):
                    self.stats['field_usage'][field] += 1

            # File changes
            file_changes = cp.get('file_changes', [])
            file_change_count = len(file_changes)
            file_change_counts.append(file_change_count)
            self.stats['total_file_changes'] += file_change_count
            self.stats['max_file_changes'] = max(
                self.stats['max_file_changes'],
                file_change_count
            )

            # Decisions
            decisions = cp.get('decisions', [])
            if decisions:
                self.stats['decisions_count'] += len(decisions)

            # Problems
            problems = cp.get('problems_encountered', [])
            if problems:
                self.stats['problems_count'] += len(problems)

            # Manual descriptions
            context = cp.get('context', {})
            if isinstance(context, dict):
                desc = context.get('description', '')
                if desc and not desc.startswith('Auto'):
                    self.stats['manual_descriptions'] += 1

        # Averages
        if file_change_counts:
            self.stats['avg_file_changes'] = sum(file_change_counts) / len(file_change_counts)

        file_sizes = [cp['_file_size_bytes'] for cp in self.checkpoints if '_file_size_bytes' in cp]
        if file_sizes:
            self.stats['avg_size_kb'] = (sum(file_sizes) / len(file_sizes)) / 1024

        # Display stats
        print(f"  Date range: {self.stats['oldest_date']} to {self.stats['newest_date']}")
        print(f"  Span: {self.stats['date_range_days']} days")
        print(f"  Last 90 days: {self.stats['last_90_days_count']} checkpoints")
        print(f"  Average file changes: {self.stats['avg_file_changes']:.1f}")
        print(f"  Max file changes: {self.stats['max_file_changes']}")
        print(f"  Average size: {self.stats['avg_size_kb']:.1f} KB")
        print(f"  Checkpoints with decisions: {self.stats['decisions_count']}")
        print(f"  Checkpoints with problems: {self.stats['problems_count']}")
        print(f"  Manual descriptions: {self.stats['manual_descriptions']}")

    def _extract_project_name(self, checkpoint: Dict[str, Any]) -> Optional[str]:
        """Extract project name from checkpoint."""
        # Try new format
        project = checkpoint.get('project', {})
        if isinstance(project, dict):
            return project.get('name')

        # Try old format
        context = checkpoint.get('context', {})
        if isinstance(context, dict):
            project_info = context.get('project')
            if isinstance(project_info, dict):
                return project_info.get('name')
            elif isinstance(project_info, str):
                return project_info

        return None

    def _identify_priorities(self):
        """Identify migration priorities based on value."""
        cutoff_date = datetime.now() - timedelta(days=90)

        for cp in self.checkpoints:
            ts = cp.get('timestamp')
            if not ts:
                continue

            cp_date = datetime.fromisoformat(ts)
            file_change_count = len(cp.get('file_changes', []))
            has_decisions = bool(cp.get('decisions'))
            has_problems = bool(cp.get('problems_encountered'))

            # Check for manual description
            context = cp.get('context', {})
            if isinstance(context, dict):
                desc = context.get('description', '')
                has_manual_desc = desc and not desc.startswith('Auto')
            else:
                has_manual_desc = False

            # Categorize
            if cp_date >= cutoff_date:
                # Priority 1: Recent (last 90 days)
                self.priority_lists['priority_1_recent'].append(cp['_file_path'])

            elif (file_change_count >= 10 or has_decisions or
                  has_problems or has_manual_desc):
                # Priority 2: High-value older checkpoints
                self.priority_lists['priority_2_high_value'].append(cp['_file_path'])
                self.stats['high_value_older_count'] += 1

            else:
                # Priority 3: Archive only
                self.priority_lists['priority_3_archive'].append(cp['_file_path'])

        print(f"  Priority 1 (recent): {len(self.priority_lists['priority_1_recent'])} checkpoints")
        print(f"  Priority 2 (high-value): {len(self.priority_lists['priority_2_high_value'])} checkpoints")
        print(f"  Priority 3 (archive): {len(self.priority_lists['priority_3_archive'])} checkpoints")

    def _prepare_for_json(self, obj: Any) -> Any:
        """Convert datetime objects to strings for JSON serialization."""
        if isinstance(obj, dict):
            return {k: self._prepare_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def _extract_samples(self):
        """Extract representative sample checkpoints."""
        cutoff_date = datetime.now() - timedelta(days=7)

        # Recent checkpoint (last 7 days)
        for cp in reversed(self.checkpoints):
            ts = cp.get('timestamp')
            if ts and datetime.fromisoformat(ts) >= cutoff_date:
                self.samples['recent'] = cp
                break

        # High file change checkpoint
        max_changes = 0
        for cp in self.checkpoints:
            change_count = len(cp.get('file_changes', []))
            if change_count > max_changes:
                max_changes = change_count
                self.samples['high_file_changes'] = cp

        # With decisions
        for cp in self.checkpoints:
            if cp.get('decisions'):
                self.samples['with_decisions'] = cp
                break

        # With problems
        for cp in self.checkpoints:
            if cp.get('problems_encountered'):
                self.samples['with_problems'] = cp
                break

        # Auto-generated
        for cp in self.checkpoints:
            context = cp.get('context', {})
            if isinstance(context, dict):
                desc = context.get('description', '')
                if desc and desc.startswith('Auto'):
                    self.samples['auto_generated'] = cp
                    break

        print(f"  Extracted {sum(1 for s in self.samples.values() if s)} sample checkpoints")

    def _generate_reports(self):
        """Generate all output reports."""
        output_dir = Path('C:/Users/layden/.claude')
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Checkpoint inventory (JSON)
        inventory_path = output_dir / 'checkpoint-inventory.json'
        inventory = {
            'generated_at': datetime.now().isoformat(),
            'checkpoint_directory': str(self.checkpoint_dir),
            'statistics': {
                'total_count': self.stats['total_count'],
                'parsed_successfully': self.stats['parsed_successfully'],
                'parse_errors': self.stats['parse_errors'],
                'date_range': {
                    'oldest': self.stats['oldest_date'].isoformat() if self.stats['oldest_date'] else None,
                    'newest': self.stats['newest_date'].isoformat() if self.stats['newest_date'] else None,
                    'span_days': self.stats['date_range_days']
                },
                'last_90_days_count': self.stats['last_90_days_count'],
                'high_value_older_count': self.stats['high_value_older_count'],
                'by_project': dict(self.stats['by_project']),
                'file_changes': {
                    'total': self.stats['total_file_changes'],
                    'average': round(self.stats['avg_file_changes'], 2),
                    'max': self.stats['max_file_changes']
                },
                'average_size_kb': round(self.stats['avg_size_kb'], 2),
                'content_counts': {
                    'decisions': self.stats['decisions_count'],
                    'problems': self.stats['problems_count'],
                    'manual_descriptions': self.stats['manual_descriptions']
                }
            },
            'field_usage': dict(self.stats['field_usage'].most_common()),
            'top_projects': dict(Counter(self.stats['by_project']).most_common(10))
        }

        with open(inventory_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2)
        print(f"  Generated: {inventory_path}")

        # 2. Migration priorities (JSON)
        priorities_path = output_dir / 'migration-priorities.json'
        priorities = {
            'generated_at': datetime.now().isoformat(),
            'priority_1_recent': {
                'description': 'Last 90 days (all checkpoints)',
                'count': len(self.priority_lists['priority_1_recent']),
                'files': [Path(p).name for p in self.priority_lists['priority_1_recent'][:20]]  # First 20
            },
            'priority_2_high_value': {
                'description': 'Older but high-value (file_changes >= 10 OR has decisions OR has problems OR manual description)',
                'count': len(self.priority_lists['priority_2_high_value']),
                'files': [Path(p).name for p in self.priority_lists['priority_2_high_value'][:20]]  # First 20
            },
            'priority_3_archive': {
                'description': 'Low-value, archive only',
                'count': len(self.priority_lists['priority_3_archive']),
                'action': 'Archive but do not migrate'
            }
        }

        with open(priorities_path, 'w', encoding='utf-8') as f:
            json.dump(priorities, f, indent=2)
        print(f"  Generated: {priorities_path}")

        # 3. Save sample checkpoints
        sample_dir = output_dir / 'sample-checkpoints'
        sample_dir.mkdir(parents=True, exist_ok=True)

        for sample_type, checkpoint in self.samples.items():
            if checkpoint:
                # Convert datetime objects to strings for JSON serialization
                checkpoint_copy = self._prepare_for_json(checkpoint)
                sample_path = sample_dir / f'sample-{sample_type}.json'
                with open(sample_path, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint_copy, f, indent=2)
                print(f"  Generated sample: {sample_path.name}")

        # 4. Error log
        if self.errors:
            error_log_path = output_dir / 'checkpoint-analysis-errors.log'
            with open(error_log_path, 'w', encoding='utf-8') as f:
                f.write(f"Checkpoint Analysis Errors\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Total errors: {len(self.errors)}\n")
                f.write("=" * 80 + "\n\n")

                for i, error in enumerate(self.errors, 1):
                    f.write(f"Error #{i}\n")
                    f.write(f"File: {error['file']}\n")
                    f.write(f"Error: {error['error']}\n")
                    f.write(f"Traceback:\n{error['traceback']}\n")
                    f.write("-" * 80 + "\n\n")
            print(f"  Generated error log: {error_log_path}")

        # 5. Summary markdown report
        summary_path = output_dir / 'phase1b-results.md'
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# Phase 1B: Checkpoint Analysis Results\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"- **Total checkpoints analyzed:** {self.stats['total_count']}\n")
            f.write(f"- **Successfully parsed:** {self.stats['parsed_successfully']}\n")
            f.write(f"- **Parse errors:** {self.stats['parse_errors']}\n")
            f.write(f"- **Date range:** {self.stats['date_range_days']} days ({self.stats['oldest_date'].strftime('%Y-%m-%d')} to {self.stats['newest_date'].strftime('%Y-%m-%d')})\n")
            f.write(f"- **Last 90 days:** {self.stats['last_90_days_count']} checkpoints\n")
            f.write(f"- **High-value older:** {self.stats['high_value_older_count']} checkpoints\n\n")

            f.write("## Migration Priorities\n\n")
            f.write(f"1. **Priority 1 (Recent):** {len(self.priority_lists['priority_1_recent'])} checkpoints - MIGRATE ALL\n")
            f.write(f"2. **Priority 2 (High-value):** {len(self.priority_lists['priority_2_high_value'])} checkpoints - MIGRATE SELECTIVELY\n")
            f.write(f"3. **Priority 3 (Archive):** {len(self.priority_lists['priority_3_archive'])} checkpoints - ARCHIVE ONLY\n\n")

            f.write("## Statistics\n\n")
            f.write(f"- **Average file changes:** {self.stats['avg_file_changes']:.1f} per checkpoint\n")
            f.write(f"- **Max file changes:** {self.stats['max_file_changes']}\n")
            f.write(f"- **Average checkpoint size:** {self.stats['avg_size_kb']:.1f} KB\n")
            f.write(f"- **Checkpoints with decisions:** {self.stats['decisions_count']}\n")
            f.write(f"- **Checkpoints with problems:** {self.stats['problems_count']}\n")
            f.write(f"- **Manual descriptions:** {self.stats['manual_descriptions']}\n\n")

            f.write("## Top Projects\n\n")
            for project, count in Counter(self.stats['by_project']).most_common(10):
                f.write(f"- **{project}:** {count} checkpoints\n")
            f.write("\n")

            f.write("## Field Usage\n\n")
            f.write("| Field | Usage Count | Percentage |\n")
            f.write("|-------|-------------|------------|\n")
            for field, count in self.stats['field_usage'].most_common(20):
                percentage = (count / self.stats['parsed_successfully']) * 100
                f.write(f"| {field} | {count} | {percentage:.1f}% |\n")
            f.write("\n")

            f.write("## Sample Checkpoints\n\n")
            f.write("Representative samples extracted to `.claude/sample-checkpoints/`:\n\n")
            for sample_type in self.samples.keys():
                if self.samples[sample_type]:
                    f.write(f"- `sample-{sample_type}.json`\n")
            f.write("\n")

            f.write("## Output Files\n\n")
            f.write("- `checkpoint-inventory.json` - Full statistics and metadata\n")
            f.write("- `migration-priorities.json` - Prioritized file lists\n")
            f.write("- `sample-checkpoints/` - Representative checkpoint examples\n")
            if self.errors:
                f.write("- `checkpoint-analysis-errors.log` - Parsing error details\n")
            f.write("- `phase1b-results.md` - This summary report\n")

        print(f"  Generated summary: {summary_path}")


def main():
    """Main entry point."""
    checkpoint_dir = "C:/Users/layden/.claude-sessions/checkpoints"

    if not Path(checkpoint_dir).exists():
        print(f"ERROR: Checkpoint directory not found: {checkpoint_dir}")
        sys.exit(1)

    analyzer = CheckpointAnalyzer(checkpoint_dir)

    try:
        results = analyzer.analyze_all()

        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE!")
        print("=" * 80)
        print(f"\nTotal checkpoints: {results['stats']['total_count']}")
        print(f"Parsed successfully: {results['stats']['parsed_successfully']}")
        print(f"Parse errors: {results['stats']['parse_errors']}")
        print(f"\nMigration priorities:")
        print(f"  - Recent (90 days): {len(results['priority_lists']['priority_1_recent'])}")
        print(f"  - High-value older: {len(results['priority_lists']['priority_2_high_value'])}")
        print(f"  - Archive only: {len(results['priority_lists']['priority_3_archive'])}")
        print(f"\nOutput files generated in: C:/Users/layden/.claude/")
        print(f"  - checkpoint-inventory.json")
        print(f"  - migration-priorities.json")
        print(f"  - sample-checkpoints/ (directory)")
        print(f"  - phase1b-results.md")
        if results['errors']:
            print(f"  - checkpoint-analysis-errors.log")

        return 0

    except Exception as e:
        print(f"\nERROR: Analysis failed!")
        print(f"Exception: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
