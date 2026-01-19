#!/bin/bash
echo "============================================================"
echo "CSG Sprint Reporter - Installation"
echo "============================================================"
echo ""
echo "Installing required packages..."
echo "This may take 1-2 minutes."
echo ""

cd "$(dirname "$0")"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-sprint-reporter.txt

echo ""
echo "============================================================"
echo "INSTALLATION COMPLETE!"
echo "============================================================"
echo ""
echo "Next step: Run ./setup.sh to configure your credentials"
echo ""
read -p "Press Enter to continue..."
