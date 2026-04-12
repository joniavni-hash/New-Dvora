#!/usr/bin/env python3
"""
Health Check — בדיקת תקינות API ושירותים
רץ יומית מ-HEARTBEAT או ידנית
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OPENCLAW_ENV = Path("/home/ubuntu/.openclaw/.env")
SECRETS_PATH = BASE_DIR / "secrets" / ".env"
RESULTS_PATH = BASE_DIR / "state" / "health_check.json"


def load_secrets():
    secrets = {}
    # Check OpenClaw root .env first, then workspace secrets/.env
    for env_path in [OPENCLAW_ENV, SECRETS_PATH]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k.strip() not in secrets:
                        secrets[k.strip()] = v.strip()
    return secrets


def check_outlook(secrets):
    """Test Microsoft Graph token acquisition with detailed diagnostics"""
    try:
        import urllib.request
        import urllib.parse
        import urllib.error
        tenant = secrets.get('MS_GRAPH_TENANT', '')
        client_id = secrets.get('MS_GRAPH_CLIENT_ID', '')
        client_secret = secrets.get('MS_GRAPH_CLIENT_SECRET', '')
        if not all([tenant, client_id, client_secret]):
            missing = []
            if not tenant: missing.append('MS_GRAPH_TENANT')
            if not client_id: missing.append('MS_GRAPH_CLIENT_ID')
            if not client_secret: missing.append('MS_GRAPH_CLIENT_SECRET')
            return {
                "status": "missing_credentials",
                "ok": False,
                "missing": missing,
                "action": "הגדירו את המפתחות החסרים ב-secrets/.env"
            }

        data = urllib.parse.urlencode({
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }).encode()
        url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        req = urllib.request.Request(url, data=data)
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read())
            if result.get('access_token'):
                return {
                    "status": "ok",
                    "ok": True,
                    "last_success": datetime.now().isoformat()
                }
            return {"status": "no_token", "ok": False}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='replace')
            try:
                err_json = json.loads(error_body)
                azure_error = err_json.get('error', '')
                azure_desc = err_json.get('error_description', '')
                if 'invalid_client' in azure_error or 'expired' in azure_desc.lower():
                    return {
                        "status": "secret_expired",
                        "ok": False,
                        "action": "Secret פג תוקף ב-Azure. צריך ליצור חדש ב-Azure Portal > App Registrations > Certificates & secrets ולעדכן ב-secrets/.env"
                    }
                return {
                    "status": f"auth_error:{azure_error}",
                    "ok": False,
                    "detail": azure_desc[:150]
                }
            except:
                return {"status": f"http_{e.code}", "ok": False, "detail": error_body[:100]}
    except Exception as e:
        return {"status": str(e)[:100], "ok": False}


def check_google_ads(secrets):
    """Test Google Ads OAuth refresh"""
    try:
        import urllib.request
        import urllib.parse
        client_id = secrets.get('GOOGLE_ADS_CLIENT_ID', '')
        client_secret = secrets.get('GOOGLE_ADS_CLIENT_SECRET', '')
        refresh_token = secrets.get('GOOGLE_ADS_REFRESH_TOKEN', '')
        if not all([client_id, client_secret, refresh_token]):
            return {"status": "missing_credentials", "ok": False}

        data = urllib.parse.urlencode({
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }).encode()
        req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        if result.get('access_token'):
            return {"status": "ok", "ok": True}
        return {"status": "no_token", "ok": False}
    except Exception as e:
        return {"status": str(e)[:100], "ok": False}


def check_dashboard():
    """Test Vercel dashboard push endpoint"""
    try:
        import urllib.request
        url = "https://vercel-dashboard-two-ruby.vercel.app/api/data"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if data.get('error') == 'no_data':
            return {"status": "no_data_pushed", "ok": False}
        if 'tasks' in data or 'error' not in data:
            return {"status": "ok", "ok": True}
        return {"status": data.get('error', 'unknown'), "ok": False}
    except Exception as e:
        return {"status": str(e)[:100], "ok": False}


def check_gog():
    """Test GOG CLI (Gmail/Calendar)"""
    try:
        result = subprocess.run(
            ['gog', '--version'], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return {"status": "ok", "ok": True, "version": result.stdout.strip()}
        return {"status": "not_working", "ok": False}
    except FileNotFoundError:
        return {"status": "not_installed", "ok": False}
    except Exception as e:
        return {"status": str(e)[:100], "ok": False}


def check_brave_api():
    """Check if Brave Search API is configured"""
    try:
        result = subprocess.run(
            ['openclaw', 'status'], capture_output=True, text=True, timeout=10
        )
        # Just check if the tool works — actual key is in openclaw config
        return {"status": "check_manually", "ok": None, "note": "Run web_search to test"}
    except Exception as e:
        return {"status": str(e)[:100], "ok": False}


def check_cron():
    """Check if dashboard cron is active"""
    try:
        result = subprocess.run(
            ['crontab', '-l'], capture_output=True, text=True, timeout=5
        )
        if 'dashboard_push' in result.stdout:
            return {"status": "ok", "ok": True}
        return {"status": "missing_dashboard_cron", "ok": False}
    except Exception as e:
        return {"status": str(e)[:100], "ok": False}


def main():
    secrets = load_secrets()
    checks = {
        "outlook": check_outlook(secrets),
        "google_ads": check_google_ads(secrets),
        "dashboard": check_dashboard(),
        "gog_cli": check_gog(),
        "brave_search": check_brave_api(),
        "cron": check_cron(),
    }

    report = {
        "timestamp": datetime.now().isoformat(),
        "stale": False,
        "stale_note": "Results are fresh. After 24 hours, treat failed checks as stale — always retry the API live before assuming a service is broken.",
        "checks": checks,
        "summary": {
            "total": len(checks),
            "ok": sum(1 for c in checks.values() if c.get("ok") is True),
            "failed": sum(1 for c in checks.values() if c.get("ok") is False),
            "unknown": sum(1 for c in checks.values() if c.get("ok") is None),
        }
    }

    # Save results
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    # Print summary
    print(f"🏥 Health Check — {report['timestamp'][:16]}")
    for name, result in checks.items():
        icon = "✅" if result.get("ok") is True else "❌" if result.get("ok") is False else "❓"
        print(f"  {icon} {name}: {result['status']}")

    ok_count = report['summary']['ok']
    total = report['summary']['total']
    print(f"\n{ok_count}/{total} services healthy")

    if report['summary']['failed'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
