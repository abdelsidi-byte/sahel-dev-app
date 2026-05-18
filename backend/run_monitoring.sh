#!/bin/bash
# Sahel Dev - Monitoring Cron Script
# Add to crontab: * * * * * /home/ubuntu/sahel_dev/backend/run_monitoring.sh

cd /home/ubuntu/sahel_dev/backend

# Activate virtual environment if exists
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

# Run monitoring
python -c "from worker import run_monitoring; run_monitoring()"