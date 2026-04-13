#!/usr/bin/env python3
"""
Daily Integration Health Check — Cron job for monitoring all integrations
"""

import sys
from pathlib import Path

# Add workspace to path
workspace = Path(__file__).parent.parent
sys.path.append(str(workspace))

from core.integration_health import IntegrationHealthMonitor

def main():
    """Run daily integration health check"""
    monitor = IntegrationHealthMonitor()
    
    print("🔍 Daily Integration Health Check")
    print("=" * 40)
    
    # Run full health check
    results = monitor.check_all_integrations()
    
    # Print results
    critical_failures = []
    warnings = []
    
    for name, result in results["results"].items():
        status = "✅" if result["connected"] else "❌"
        reason = f" - {result['reason']}" if result["reason"] else ""
        print(f"{status} {name}{reason}")
        
        if not result["connected"]:
            if name in ["outlook", "whatsapp", "telegram"]:
                critical_failures.append(name)
            else:
                warnings.append(name)
    
    print()
    summary = results["summary"]
    print(f"📊 Summary: {summary['connected']}/{summary['total_integrations']} integrations connected")
    
    # Report issues to user if needed
    if critical_failures:
        print()
        print("🔴 CRITICAL: These integrations are down:")
        for integration in critical_failures:
            details = results["results"][integration]
            print(f"   • {integration}: {details['reason']}")
            
            # Provide fix hints
            if details["reason"] == "missing_credentials":
                if integration == "outlook":
                    print("     Fix: Add MS_GRAPH_CLIENT_SECRET to /home/ubuntu/.openclaw/.env")
        
        # In real implementation, this would send notification to user
        print("\n📱 User notification recommended for critical failures")
    
    if warnings:
        print()
        print("🟡 WARNINGS: These integrations have issues:")
        for integration in warnings:
            details = results["results"][integration]
            print(f"   • {integration}: {details['reason']}")
    
    if not critical_failures and not warnings:
        print("\n🎉 All integrations healthy!")
    
    print(f"\n⏰ Check completed at {results['timestamp']}")
    return len(critical_failures) == 0  # Exit code 0 if no critical failures

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)