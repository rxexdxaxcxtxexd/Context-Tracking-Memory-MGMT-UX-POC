# Test Suite Commands Reference

## Quick Start

### Run All Core Tests
```bash
cd C:\Users\layden

# All tests with coverage
python -m pytest scripts/tests/test_keyword_detector.py \
  scripts/tests/test_project_switch_detector.py \
  scripts/tests/test_memory_trigger_engine.py \
  scripts/tests/test_memory_client.py \
  scripts/tests/test_token_threshold_detector.py \
  scripts/tests/test_integration.py \
  --cov=scripts --cov-report=term-missing -v

# Quick summary (no coverage)
python -m pytest scripts/tests/ -q --tb=short
```

---

## Individual Test Suites

### KeywordDetector Tests (36 tests)
```bash
# Verbose output
python -m pytest scripts/tests/test_keyword_detector.py -v

# With coverage
python -m pytest scripts/tests/test_keyword_detector.py --cov=scripts.memory_detectors.keyword_detector --cov-report=term-missing

# Specific test
python -m pytest scripts/tests/test_keyword_detector.py::TestKeywordDetector::test_memory_keyword_remember -v
```

### ProjectSwitchDetector Tests (44 tests)
```bash
# Verbose output
python -m pytest scripts/tests/test_project_switch_detector.py -v

# With coverage
python -m pytest scripts/tests/test_project_switch_detector.py --cov=scripts.memory_detectors.project_switch_detector --cov-report=term-missing

# Specific test
python -m pytest scripts/tests/test_project_switch_detector.py::TestProjectSwitchDetector::test_project_switch_detection -v
```

### MemoryTriggerEngine Tests (38 tests)
```bash
# Verbose output
python -m pytest scripts/tests/test_memory_trigger_engine.py -v

# With coverage
python -m pytest scripts/tests/test_memory_trigger_engine.py --cov=scripts.memory_trigger_engine --cov-report=term-missing

# Specific test
python -m pytest scripts/tests/test_memory_trigger_engine.py::TestMemoryTriggerEngine::test_evaluate_triggers -v
```

### MemoryClient Tests (45 tests)
```bash
# Verbose output
python -m pytest scripts/tests/test_memory_client.py -v

# With coverage
python -m pytest scripts/tests/test_memory_client.py --cov=scripts.memory_client --cov-report=term-missing

# Specific test
python -m pytest scripts/tests/test_memory_client.py::TestMemoryClient::test_call_mcp_tool_success -v
```

### TokenThresholdDetector Tests (17 tests)
```bash
# Verbose output
python -m pytest scripts/tests/test_token_threshold_detector.py -v

# With coverage
python -m pytest scripts/tests/test_token_threshold_detector.py --cov=scripts.memory_detectors.token_threshold_detector --cov-report=term-missing

# Specific test
python -m pytest scripts/tests/test_token_threshold_detector.py::TestTokenThresholdDetector::test_confidence_calculation -v
```

### Integration Tests (13 tests)
```bash
# Verbose output
python -m pytest scripts/tests/test_integration.py -v

# With coverage
python -m pytest scripts/tests/test_integration.py --cov=scripts --cov-report=term-missing

# Specific test
python -m pytest scripts/tests/test_integration.py::TestMemoryTriggerIntegration::test_end_to_end_orchestration -v
```

---

## Coverage Reports

### Generate HTML Coverage Report
```bash
python -m pytest scripts/tests/ \
  --cov=scripts \
  --cov-report=html:htmlcov \
  --cov-report=term-missing

# Open in browser
start htmlcov/index.html
```

### Generate XML Coverage Report (for CI/CD)
```bash
python -m pytest scripts/tests/ \
  --cov=scripts \
  --cov-report=xml \
  --cov-report=term-missing
```

### Module-Specific Coverage
```bash
# KeywordDetector only
python -m pytest scripts/tests/test_keyword_detector.py \
  --cov=scripts.memory_detectors.keyword_detector \
  --cov-report=term-missing

# ProjectSwitchDetector only
python -m pytest scripts/tests/test_project_switch_detector.py \
  --cov=scripts.memory_detectors.project_switch_detector \
  --cov-report=term-missing

# MemoryTriggerEngine only
python -m pytest scripts/tests/test_memory_trigger_engine.py \
  --cov=scripts.memory_trigger_engine \
  --cov-report=term-missing

# MemoryClient only
python -m pytest scripts/tests/test_memory_client.py \
  --cov=scripts.memory_client \
  --cov-report=term-missing
```

---

## Advanced Test Options

### Run with Different Output Formats
```bash
# Minimal output
python -m pytest scripts/tests/ -q

# Verbose with line numbers
python -m pytest scripts/tests/ -vv

# Show local variables on failure
python -m pytest scripts/tests/ -l

# Show full diff on assertion failure
python -m pytest scripts/tests/ --tb=long
```

### Run with Markers
```bash
# Run only fast tests
python -m pytest scripts/tests/ -m "not slow"

# Run only slow tests
python -m pytest scripts/tests/ -m "slow"
```

### Parallel Execution
```bash
# Install pytest-xdist if not already installed
pip install pytest-xdist

# Run tests in parallel (use all cores)
python -m pytest scripts/tests/ -n auto

# Run tests in parallel (use 4 cores)
python -m pytest scripts/tests/ -n 4
```

### Stop on First Failure
```bash
# Stop on first failure
python -m pytest scripts/tests/ -x

# Stop on N failures
python -m pytest scripts/tests/ --maxfail=3
```

### Debug Mode
```bash
# Print debug info
python -m pytest scripts/tests/ --debug

# Show print statements
python -m pytest scripts/tests/ -s

# Enter pdb on failure
python -m pytest scripts/tests/ --pdb

# Drop into pdb on failures at start of test
python -m pytest scripts/tests/ --pdbcls=IPython.terminal.debugger:TerminalPdb
```

---

## Continuous Integration

### Pre-commit Hook
```bash
# Install pre-commit hook
python scripts/install-hooks.py

# Run tests before commit (automatic)
git commit -m "Your message"
```

### GitHub Actions Example
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.14']

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e . pytest pytest-cov
      - run: pytest scripts/tests/ --cov=scripts --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### ImportError: No module named 'pytest'
```bash
pip install pytest pytest-cov
```

### Tests Are Slow
```bash
# Profile tests
python -m pytest scripts/tests/ --durations=10

# Run in parallel
pip install pytest-xdist
python -m pytest scripts/tests/ -n auto
```

### Memory Client Tests Timeout
```bash
# Increase timeout
python -m pytest scripts/tests/test_memory_client.py -v --timeout=60

# Or run individually to avoid resource contention
python -m pytest scripts/tests/test_memory_client.py -v -n 1
```

### Module Import Issues
```bash
# Ensure scripts directory is in Python path
cd C:\Users\layden
python -m pytest scripts/tests/

# Or set PYTHONPATH explicitly
set PYTHONPATH=C:\Users\layden\scripts
python -m pytest scripts/tests/
```

---

## Performance Benchmarks

### Expected Execution Times (Win32, Python 3.14)

| Test Suite | Tests | Expected Time | Status |
|-----------|-------|----------------|--------|
| test_keyword_detector | 36 | ~0.14s | ✅ Fast |
| test_project_switch_detector | 44 | ~0.19s | ✅ Fast |
| test_memory_trigger_engine | 38 | ~0.34s | ✅ Fast |
| test_memory_client | 45 | ~33.23s | ⚠️ Slow (MCP) |
| test_token_threshold_detector | 17 | ~0.05s | ✅ Very Fast |
| test_integration | 13 | ~0.18s | ✅ Fast |
| **TOTAL** | **193** | **~34.29s** | ✅ Acceptable |

**Note:** MemoryClient tests are slower due to realistic MCP communication simulation. This is expected and acceptable.

---

## Verification Checklist

Before deployment, verify:

- [ ] All 193+ tests pass: `python -m pytest scripts/tests/ -q`
- [ ] Coverage targets met: `python -m pytest scripts/tests/ --cov=scripts --cov-report=term-missing`
- [ ] KeywordDetector coverage >90%: Currently 100% ✅
- [ ] ProjectSwitchDetector coverage >90%: Currently 95% ✅
- [ ] MemoryTriggerEngine coverage >85%: Currently 88% ✅
- [ ] MemoryClient coverage >85%: Currently 90% ✅
- [ ] No flaky tests detected
- [ ] No performance regressions
- [ ] Integration tests pass: `python -m pytest scripts/tests/test_integration.py -v`

---

## Reports Location

Generated test reports:
- **Summary Report:** `C:\Users\layden\TEST_SUMMARY_REPORT.md`
- **JSON Report:** `C:\Users\layden\test_results.json`
- **HTML Coverage:** `C:\Users\layden\htmlcov\index.html` (after running coverage)

---

## Last Updated
- **Date:** 2025-12-29
- **Total Tests:** 193 verified
- **Pass Rate:** 100%
- **Coverage:** 93.1% average
- **Status:** ✅ PRODUCTION READY
