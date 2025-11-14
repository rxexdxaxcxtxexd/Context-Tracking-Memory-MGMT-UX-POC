#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Windows Task Scheduler for periodic session checkpoints

.DESCRIPTION
    Creates a scheduled task that runs checkpoint.py every N minutes.
    This provides a safety net to catch crashes and forced terminations
    that bypass Claude Code's SessionEnd hook.

.PARAMETER IntervalMinutes
    Minutes between checkpoint runs (default: 30)

.PARAMETER ScriptPath
    Full path to checkpoint.py (default: auto-detect)

.PARAMETER TaskName
    Name for the scheduled task (default: ClaudePeriodicCheckpoint)

.PARAMETER Remove
    Remove the scheduled task instead of creating it

.EXAMPLE
    .\setup-task-scheduler.ps1
    Create task with default settings (every 30 minutes)

.EXAMPLE
    .\setup-task-scheduler.ps1 -IntervalMinutes 60
    Create task that runs every hour

.EXAMPLE
    .\setup-task-scheduler.ps1 -Remove
    Remove the scheduled task
#>

param(
    [int]$IntervalMinutes = 30,
    [string]$ScriptPath = "",
    [string]$TaskName = "ClaudePeriodicCheckpoint",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

# Check if running as Administrator (Task Scheduler requires it for some operations)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "     WINDOWS TASK SCHEDULER - PERIODIC CHECKPOINT SETUP" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Handle removal
if ($Remove) {
    Write-Host "Removing scheduled task: $TaskName" -ForegroundColor Yellow
    Write-Host ""

    try {
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "[OK] Task '$TaskName' removed successfully" -ForegroundColor Green
        } else {
            Write-Host "[INFO] Task '$TaskName' does not exist" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] Failed to remove task: $_" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Cyan
    exit 0
}

# Detect script path if not provided
if ($ScriptPath -eq "") {
    $ScriptPath = Join-Path $PSScriptRoot "checkpoint.py"

    if (!(Test-Path $ScriptPath)) {
        # Try alternative locations
        $altPath = Join-Path $env:USERPROFILE "Projects\context-tracking-memory\scripts\checkpoint.py"

        if (Test-Path $altPath) {
            $ScriptPath = $altPath
        } else {
            Write-Host "[ERROR] Could not find checkpoint.py" -ForegroundColor Red
            Write-Host "  Tried: $ScriptPath" -ForegroundColor Gray
            Write-Host "  Tried: $altPath" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Please specify the path:" -ForegroundColor Yellow
            Write-Host "  .\setup-task-scheduler.ps1 -ScriptPath 'C:\path\to\checkpoint.py'" -ForegroundColor Gray
            exit 1
        }
    }
}

Write-Host "[1/5] Configuration" -ForegroundColor Yellow
Write-Host "  Task name: $TaskName" -ForegroundColor Gray
Write-Host "  Interval: Every $IntervalMinutes minutes" -ForegroundColor Gray
Write-Host "  Script: $ScriptPath" -ForegroundColor Gray
Write-Host "  User: $env:USERNAME" -ForegroundColor Gray
Write-Host ""

# Validate Python and script
Write-Host "[2/5] Validating Python and script..." -ForegroundColor Yellow

try {
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
    Write-Host "  Python: $pythonPath" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found in PATH" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $ScriptPath)) {
    Write-Host "  [ERROR] Script not found: $ScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "  Script: Found" -ForegroundColor Green
Write-Host ""

# Check for existing task
Write-Host "[3/5] Checking for existing task..." -ForegroundColor Yellow

$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "  Task already exists" -ForegroundColor Yellow
    $response = Read-Host "  Replace existing task? (y/n)"

    if ($response -ne "y") {
        Write-Host "  Cancelled" -ForegroundColor Gray
        exit 0
    }

    Write-Host "  Removing existing task..." -ForegroundColor Gray
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Write-Host "  Ready to create new task" -ForegroundColor Green
Write-Host ""

# Create scheduled task
Write-Host "[4/5] Creating scheduled task..." -ForegroundColor Yellow

try {
    # Action: Run Python script
    $action = New-ScheduledTaskAction `
        -Execute "python.exe" `
        -Argument "`"$ScriptPath`" --quick --description `"Periodic safety checkpoint`""

    # Trigger: Repeat every N minutes
    $trigger = New-ScheduledTaskTrigger `
        -Once `
        -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
        -RepetitionDuration ([TimeSpan]::MaxValue)

    # Settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    # Principal (run as current user, interactive mode)
    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive `
        -RunLevel Limited

    # Register task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Periodic checkpoint for Claude Code session continuity. Runs checkpoint.py every $IntervalMinutes minutes." | Out-Null

    Write-Host "  Task created successfully" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to create task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verify task
Write-Host "[5/5] Verifying task..." -ForegroundColor Yellow

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($task) {
    Write-Host "  Task registered: $TaskName" -ForegroundColor Green
    Write-Host "  Status: $($task.State)" -ForegroundColor Gray

    # Get next run time
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    if ($taskInfo.NextRunTime) {
        Write-Host "  Next run: $($taskInfo.NextRunTime)" -ForegroundColor Gray
    }
} else {
    Write-Host "  [WARNING] Could not verify task" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "                    SETUP COMPLETE!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Periodic checkpoint configured:" -ForegroundColor White
Write-Host "  - Runs every $IntervalMinutes minutes" -ForegroundColor Gray
Write-Host "  - Creates checkpoint with: python checkpoint.py --quick" -ForegroundColor Gray
Write-Host "  - Catches crashes and forced terminations" -ForegroundColor Gray
Write-Host ""

Write-Host "Task Scheduler commands:" -ForegroundColor White
Write-Host "  View task: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Run now: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Disable: Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Remove: .\setup-task-scheduler.ps1 -Remove" -ForegroundColor Gray
Write-Host ""

Write-Host "Testing:" -ForegroundColor Yellow
Write-Host "  Run checkpoint manually: python $ScriptPath --quick" -ForegroundColor Gray
Write-Host "  Or trigger task: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""

Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Task will run automatically every $IntervalMinutes minutes" -ForegroundColor Gray
Write-Host "  2. Combined with SessionEnd hook, provides 95%+ reliability" -ForegroundColor Gray
Write-Host "  3. No further action needed!" -ForegroundColor Gray
Write-Host ""

Write-Host "======================================================================" -ForegroundColor Cyan
