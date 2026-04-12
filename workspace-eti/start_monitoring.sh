#!/bin/bash
# אתי - התחלת ניטור אוטומטי
# רץ כל 15 דקות ומפעיל את performance monitor

cd /home/jonia/.openclaw/workspace-eti

# הרץ performance monitor
python3 scripts/performance_monitor.py

# בעתיד - סקריפטים נוספים:
# python3 scripts/error_scanner.py
# python3 scripts/trend_analyzer.py