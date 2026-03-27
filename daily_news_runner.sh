#!/bin/bash
# Daily AI News runner with retry logic
# Tries up to 5 times between 9-10am if the first attempt fails

PROJECT_DIR="$HOME/Bobo_pen/ai-agent-hub"
PYTHON="/opt/anaconda3/bin/python"
LOG_FILE="$PROJECT_DIR/data/daily_news.log"
LOCK_FILE="$PROJECT_DIR/data/.news_done_today"

TODAY=$(date +%Y-%m-%d)

# Skip if already succeeded today
if [ -f "$LOCK_FILE" ] && [ "$(cat "$LOCK_FILE")" = "$TODAY" ]; then
    echo "$(date): Already fetched news today, skipping." >> "$LOG_FILE"
    exit 0
fi

echo "$(date): Attempting to fetch AI news..." >> "$LOG_FILE"

# Run the script
cd "$PROJECT_DIR"
$PYTHON "$PROJECT_DIR/daily_news.py" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "$TODAY" > "$LOCK_FILE"
    echo "$(date): Success!" >> "$LOG_FILE"
else
    echo "$(date): Failed. Will retry on next cron trigger." >> "$LOG_FILE"
fi
