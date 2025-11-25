#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup automated session continuity for Claude Code

.DESCRIPTION
    This script configures Claude Code hooks to automatically:
    - Resume previous session on startup
    - Create checkpoint on exit

    Hooks are configured in .claude/settings.json

.PARAMETER Global
    Install hooks globally (~/.claude/settings.json) instead of project-local

.PARAMETER SkipValidation
    Skip validation of Python scripts

.EXAMPLE
    .\setup-automation.ps1
    Set up automation for current project

.EXAMPLE
    .\setup-automation.ps1 -Global
    Set up automation globally for all Claude Code sessions
#>

param(
    [switch]$Global,
    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "     CLAUDE CODE SESSION CONTINUITY - AUTOMATION SETUP" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Determine installation location
if ($Global) {
    $claudeDir = Join-Path $env:USERPROFILE ".claude"
    $installLocation = "Global (~/.claude)"
    $scriptsBasePath = Join-Path $env:USERPROFILE "Projects\context-tracking-memory\scripts"
} else {
    $claudeDir = Join-Path $PSScriptRoot ".." ".claude"
    $installLocation = "Project-local (.claude)"
    $scriptsBasePath = "scripts"
}

Write-Host "[1/4] Installation location: $installLocation" -ForegroundColor Yellow
Write-Host ""

# Create .claude directory if it doesn't exist
if (!(Test-Path $claudeDir)) {
    Write-Host "Creating $claudeDir..." -ForegroundColor Gray
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
}

$settingsPath = Join-Path $claudeDir "settings.json"

# Validate Python scripts exist
if (!$SkipValidation) {
    Write-Host "[2/4] Validating Python scripts..." -ForegroundColor Yellow

    $checkpointScript = if ($Global) {
        Join-Path $env:USERPROFILE "Projects\context-tracking-memory\scripts\checkpoint.py"
    } else {
        Join-Path $PSScriptRoot "checkpoint.py"
    }

    $resumeScript = if ($Global) {
        Join-Path $env:USERPROFILE "Projects\context-tracking-memory\scripts\resume-session.py"
    } else {
        Join-Path $PSScriptRoot "resume-session.py"
    }

    if (!(Test-Path $checkpointScript)) {
        Write-Host "ERROR: checkpoint.py not found at: $checkpointScript" -ForegroundColor Red
        exit 1
    }

    if (!(Test-Path $resumeScript)) {
        Write-Host "ERROR: resume-session.py not found at: $resumeScript" -ForegroundColor Red
        exit 1
    }

    Write-Host "  - checkpoint.py: Found" -ForegroundColor Green
    Write-Host "  - resume-session.py: Found" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[2/4] Skipping validation" -ForegroundColor Gray
    Write-Host ""
}

# Build hooks configuration
Write-Host "[3/4] Creating hooks configuration..." -ForegroundColor Yellow

$resumeCommand = if ($Global) {
    "python `"$scriptsBasePath\resume-session.py`" summary"
} else {
    "python $scriptsBasePath/resume-session.py summary"
}

$checkpointCommand = if ($Global) {
    "python `"$scriptsBasePath\checkpoint.py`" --quick"
} else {
    "python $scriptsBasePath/checkpoint.py --quick"
}

$hooksConfig = @{
    hooks = @{
        SessionStart = @(
            @{
                matcher = ""
                hooks = @(
                    @{
                        type = "command"
                        command = $resumeCommand
                        timeout = 30000
                    }
                )
            }
        )
        SessionEnd = @(
            @{
                matcher = ""
                hooks = @(
                    @{
                        type = "command"
                        command = $checkpointCommand
                        timeout = 60000
                    }
                )
            }
        )
    }
}

# Check if settings.json exists and merge
if (Test-Path $settingsPath) {
    Write-Host "  Existing settings.json found, merging hooks..." -ForegroundColor Gray

    try {
        $existingSettings = Get-Content $settingsPath -Raw | ConvertFrom-Json -AsHashtable

        # Merge hooks
        if (!$existingSettings.hooks) {
            $existingSettings.hooks = @{}
        }

        $existingSettings.hooks.SessionStart = $hooksConfig.hooks.SessionStart
        $existingSettings.hooks.SessionEnd = $hooksConfig.hooks.SessionEnd

        $finalConfig = $existingSettings
    } catch {
        Write-Host "  Warning: Could not parse existing settings.json, backing up and overwriting" -ForegroundColor Yellow
        $backupPath = "$settingsPath.backup"
        Copy-Item $settingsPath $backupPath
        Write-Host "  Backup saved to: $backupPath" -ForegroundColor Gray

        $finalConfig = $hooksConfig
    }
} else {
    $finalConfig = $hooksConfig
}

# Write settings.json
$finalConfig | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8

Write-Host "  Settings saved to: $settingsPath" -ForegroundColor Green
Write-Host ""

# Test configuration
Write-Host "[4/4] Testing configuration..." -ForegroundColor Yellow

try {
    $testConfig = Get-Content $settingsPath -Raw | ConvertFrom-Json

    if ($testConfig.hooks.SessionStart -and $testConfig.hooks.SessionEnd) {
        Write-Host "  Configuration valid!" -ForegroundColor Green
    } else {
        Write-Host "  Warning: Configuration may be incomplete" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Error: Invalid JSON in settings.json" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "                    SETUP COMPLETE!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Automation configured:" -ForegroundColor White
Write-Host "  - SessionStart: Runs resume-session.py (shows summary)" -ForegroundColor Gray
Write-Host "  - SessionEnd: Runs checkpoint.py --quick (saves session)" -ForegroundColor Gray
Write-Host ""

Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Start a new Claude Code session" -ForegroundColor Gray
Write-Host "  2. Session will automatically resume and show summary" -ForegroundColor Gray
Write-Host "  3. When you exit, session will automatically checkpoint" -ForegroundColor Gray
Write-Host ""

Write-Host "Optional: Set up Task Scheduler safety net" -ForegroundColor Yellow
Write-Host "  -> .\scripts\setup-task-scheduler.ps1" -ForegroundColor Gray
Write-Host ""

Write-Host "Test hooks manually:" -ForegroundColor Yellow
Write-Host "  python scripts/resume-session.py summary" -ForegroundColor Gray
Write-Host "  python scripts/checkpoint.py --quick" -ForegroundColor Gray
Write-Host ""

Write-Host "======================================================================" -ForegroundColor Cyan
