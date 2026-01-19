#!/bin/bash
echo "============================================================"
echo "CSG Sprint Reporter - Generate Report"
echo "============================================================"
echo ""

cd "$(dirname "$0")"

read -p "Enter sprint number (e.g., 13): " SPRINT_NUM

if [ -z "$SPRINT_NUM" ]; then
    echo "[ERROR] Sprint number is required"
    exit 1
fi

echo ""
echo "Generating report for Sprint $SPRINT_NUM..."
echo "This will take 1-2 minutes."
echo ""

python3 csg-sprint-reporter.py --ai --quick --sprint "$SPRINT_NUM"

echo ""
echo "============================================================"
echo "DONE!"
echo "============================================================"
echo ""
echo "Your report has been saved to your Downloads folder."
echo "Look for: sprint-report-YYYY-MM-DD-HHMMSS.md"
echo ""
read -p "Press Enter to continue..."
