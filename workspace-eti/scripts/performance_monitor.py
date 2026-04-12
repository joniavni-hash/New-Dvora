#!/usr/bin/env python3
"""
אתי - Performance Monitor
בודק ביצועים של כל הסקריפטים ומזהה בעיות
"""

import os
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import glob

def get_script_runtimes():
    """
    מחפש logs של סקריפטים ומודד זמני ריצה
    """
    main_workspace = "/home/jonia/.openclaw/workspace"
    eti_logs = "/home/jonia/.openclaw/workspace-eti/logs/performance"
    
    runtimes = {}
    
    # בדיקת health_check log
    try:
        result = subprocess.run(['python3', f'{main_workspace}/scripts/health_check.py', '--timing'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and "Runtime:" in result.stdout:
            runtime = float(result.stdout.split("Runtime:")[-1].split("s")[0].strip())
            runtimes['health_check.py'] = runtime
    except Exception as e:
        runtimes['health_check.py'] = {'error': str(e)}
    
    return runtimes

def analyze_performance(current_runtimes):
    """
    משווה ביצועים נוכחיים לממוצע
    """
    performance_file = "/home/jonia/.openclaw/workspace-eti/data/trends/performance_history.json"
    
    # טען היסטוריה קיימת
    history = []
    if os.path.exists(performance_file):
        try:
            with open(performance_file, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # הוסף מדידה נוכחית
    current_entry = {
        'timestamp': datetime.now().isoformat(),
        'runtimes': current_runtimes
    }
    history.append(current_entry)
    
    # שמור רק 7 ימים אחרונים
    cutoff_time = datetime.now() - timedelta(days=7)
    history = [entry for entry in history 
               if datetime.fromisoformat(entry['timestamp']) > cutoff_time]
    
    # שמור עדכון
    os.makedirs(os.path.dirname(performance_file), exist_ok=True)
    with open(performance_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    # חשב ממוצעים
    alerts = []
    if len(history) > 5:  # מספיק דאטה להשוואה
        for script_name in current_runtimes:
            if isinstance(current_runtimes[script_name], dict):
                continue  # skip errors
                
            recent_times = []
            for entry in history[-20:]:  # 20 מדידות אחרונות
                if script_name in entry['runtimes'] and not isinstance(entry['runtimes'][script_name], dict):
                    recent_times.append(entry['runtimes'][script_name])
            
            if recent_times:
                avg_time = sum(recent_times) / len(recent_times)
                current_time = current_runtimes[script_name]
                
                # אזהרה אם הזמן גדול ב-50% מהממוצע
                if current_time > avg_time * 1.5 and current_time > 10:  # רק אם גם מעל 10 שניות
                    alerts.append({
                        'type': 'performance',
                        'script': script_name,
                        'current': current_time,
                        'average': avg_time,
                        'severity': 'warning' if current_time < avg_time * 2 else 'critical'
                    })
    
    return alerts

def save_alert(alert_data):
    """
    שומר התרעה לדבורה
    """
    alert_file = "/home/jonia/.openclaw/workspace/state/eti_alerts.md"
    timestamp = datetime.now().strftime("%H:%M")
    
    alert_text = f"⚡ {timestamp} - {alert_data['script']}: {alert_data['current']:.1f}s (ממוצע: {alert_data['average']:.1f}s)\n"
    
    # הוסף לקובץ אלרטים
    with open(alert_file, 'a') as f:
        f.write(alert_text)

def main():
    print("🤖 אתי - Performance Monitor starting...")
    
    # מדוד ביצועים נוכחיים
    current_runtimes = get_script_runtimes()
    
    # נתח והשווה
    alerts = analyze_performance(current_runtimes)
    
    # שלח התרעות אם נדרש
    critical_alerts = [a for a in alerts if a['severity'] == 'critical']
    
    if critical_alerts:
        for alert in critical_alerts:
            save_alert(alert)
            print(f"🚨 CRITICAL: {alert['script']} - {alert['current']:.1f}s (avg: {alert['average']:.1f}s)")
    
    # לוג יומי
    log_file = f"/home/jonia/.openclaw/workspace-eti/logs/performance/{datetime.now().strftime('%Y-%m-%d')}.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - {json.dumps(current_runtimes)}\n")
    
    print(f"📊 Monitored {len(current_runtimes)} scripts, {len(alerts)} alerts")
    
    if not alerts:
        print("✅ All systems performing normally")

if __name__ == "__main__":
    main()