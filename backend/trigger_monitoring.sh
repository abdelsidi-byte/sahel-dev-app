#!/bin/bash
# Sahel Dev - Run Monitoring via API
# This script calls the API endpoint to trigger monitoring

API_URL="${1:-http://localhost:8000}"

curl -X POST "$API_URL/api/run-monitoring" 2>/dev/null

echo ""
echo "Monitoring check triggered at $(date)"