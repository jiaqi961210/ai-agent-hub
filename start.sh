#!/bin/bash
# Start the full Ximen Nao system — bots + remote bridge
cd "$(dirname "$0")"

echo "Starting Ximen Nao Agent Hub..."

# Kill any existing processes
pkill -f "telegram_group_bot.py" 2>/dev/null
pkill -f "remote_bridge.py" 2>/dev/null
sleep 2

# Start remote bridge in background
echo "  Starting Remote Bridge..."
python3 remote_bridge.py > /tmp/remote_bridge.log 2>&1 &
echo "  PID: $!"

# Start multi-bot system
echo "  Starting Telegram bots..."
python3 telegram_group_bot.py > /tmp/groupbot.log 2>&1 &
echo "  PID: $!"

echo ""
echo "All systems running!"
echo "  Bots log: /tmp/groupbot.log"
echo "  Bridge log: /tmp/remote_bridge.log"
echo ""
echo "Use /remote in Telegram to send commands to this Mac."
echo "Press Ctrl+C or run 'pkill -f telegram_group_bot; pkill -f remote_bridge' to stop."
