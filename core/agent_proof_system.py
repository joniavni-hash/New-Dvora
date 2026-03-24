#!/usr/bin/env python3
"""
Agent Proof System - בדיקת 4 הסוכנות עם routing אמיתי
"""

import sys
import json
from typing import Dict, Any
from core.working_agent_dispatcher import dispatch_message_working

# Mock sessions_spawn for testing
def mock_sessions_spawn(**kwargs):
    return {
        "status": "accepted",
        "childSessionKey": f"agent:main:subagent:test-{kwargs.get('label', 'unknown')[:8]}",
        "runId": f"test-run-{kwargs.get('task', 'unknown')[:8]}", 
        "mode": kwargs.get("mode", "run")
    }

def run_agent_proof_tests():
    """ביצוע 4 בדיקות proof"""
    
    print("🧪 **Agent Proof System - 4 Tests**")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            "name": "Legal → מאשה",
            "message": "בדקי חוזה שכירות - יש סעיפי פיגורים בלתי סבירים?",
            "expected_domain": "legal",
            "expected_agent": "masha"
        },
        {
            "name": "Groups → אודיה", 
            "message": "סכמי הודעות קבוצת אלון מהיום ושלחי לקבוצת המשפחה",
            "expected_domain": "groups",
            "expected_agent": "odya"
        },
        {
            "name": "Marketing → טלי",
            "message": "צרי פרסום Larry-style לVilla Lithos עם 6 slides לTikTok",
            "expected_domain": "marketing", 
            "expected_agent": "tali"
        },
        {
            "name": "Research → צופית",
            "message": "חקרי מגמות השוק בנדלן יווני ותמצאי הזדמנויות השקעה",
            "expected_domain": "research",
            "expected_agent": "tzofit"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n**Test {i}: {test['name']}**")
        print(f"Message: {test['message']}")
        
        # Dispatch
        result = dispatch_message_working(test['message'], mock_sessions_spawn)
        
        # Validation
        success = (
            result.get("status") == "success" and
            result.get("domain") == test['expected_domain'] and 
            result.get("intended_agent") == test['expected_agent']
        )
        
        # Results
        print(f"✅ **Chosen domain:** {result.get('domain', 'unknown')}")
        print(f"✅ **Chosen agentId:** {result.get('intended_agent', 'unknown')}")
        print(f"✅ **Agent name:** {result.get('agent_name', 'unknown')}")
        print(f"✅ **Confidence:** {result.get('confidence', 0):.1f}")
        print(f"✅ **Dispatch method:** {result.get('dispatch_method', 'unknown')}")
        print(f"✅ **Session key:** {result.get('session_key', 'unknown')}")
        print(f"✅ **Run ID:** {result.get('run_id', 'unknown')}")
        
        if success:
            print(f"🎯 **Status:** ✅ SUCCESS")
        else:
            print(f"🎯 **Status:** ❌ FAILED")
            print(f"   Expected: {test['expected_domain']} → {test['expected_agent']}")
            print(f"   Got: {result.get('domain')} → {result.get('intended_agent')}")
        
        results.append({
            "test": test['name'],
            "success": success,
            "result": result
        })
    
    # Summary
    success_count = sum(1 for r in results if r['success'])
    print(f"\n🏆 **SUMMARY:** {success_count}/4 tests passed")
    
    if success_count == 4:
        print("🎉 **ALL TESTS PASSED** - Agent routing system operational!")
        return True
    else:
        print("⚠️ **SOME TESTS FAILED** - Need fixes before production")
        return False

if __name__ == "__main__":
    run_agent_proof_tests()