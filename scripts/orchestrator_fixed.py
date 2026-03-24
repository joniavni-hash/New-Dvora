#!/usr/bin/env python3
"""
Fixed Orchestrator - Pipeline עם Agent Registry
מחבר routing לagents אמיתיים
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import core modules with fallbacks
try:
    from core.router import classify_message
    from core.context_manager import load_context_for_domain  
    from core.qa_service import validate_output
    from core.model_selector import select_tier
except ImportError as e:
    print(f"⚠️ Core modules not available: {e}")
    # Use simplified versions
    def classify_message(msg, source, group_id):
        msg_lower = msg.lower()
        
        # Marketing
        if any(word in msg_lower for word in ['villa', 'tiktok', 'marketing', 'larry', 'פרסום', 'שיווק']):
            return {"domain": "marketing", "agent": "tali", "confidence": 0.9}
        
        # Fitness
        if any(word in msg_lower for word in ['שקלתי', 'אכלתי', 'קלוריות', 'חלבון', 'כושר', 'דיאטה']):
            return {"domain": "fitness", "agent": "dana", "confidence": 0.9}
        
        # Legal  
        if any(word in msg_lower for word in ['חוזה', 'הסכם', 'משפטי', 'חוק', 'סיכון']):
            return {"domain": "legal", "agent": "masha", "confidence": 0.9}
        
        # Research
        if any(word in msg_lower for word in ['חקר', 'בדק', 'מחקר', 'נתח', 'שוק']):
            return {"domain": "research", "agent": "tzofit", "confidence": 0.9}
        
        # Groups
        if any(word in msg_lower for word in ['קבוצה', 'whatsapp', 'הודעות', 'סיכום קבוצת']):
            return {"domain": "groups", "agent": "odya", "confidence": 0.9}
        
        # Automation
        if any(word in msg_lower for word in ['אוטומציה', 'תהליך', 'אינטגרציה', 'זרימה']):
            return {"domain": "automation", "agent": "eti", "confidence": 0.9}
        
        # Default to fitness if weight mentioned
        if any(word in msg_lower for word in ['71.5', '72.5', 'משקל']):
            return {"domain": "fitness", "agent": "dana", "confidence": 0.8}
        
        # Default - כל שאר לטלי (יש הכי הרבה יכולות)
        return {"domain": "general", "agent": "tali", "confidence": 0.5}
    
    def load_context_for_domain(domain):
        return {"files_loaded": [], "content": "", "truncated": False}
    
    def validate_output(output, domain, constraints):
        return {"passed": True, "reason": "No validation available"}
    
    def select_tier(domain, content_len):
        return "tier2"
from agents.agent_registry import registry

def orchestrate_message(message: str, source: str = "dm", group_id: str = None, role: str = None):
    """
    Orchestrator pipeline מלא עם agent execution
    """
    execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(message)}"
    
    try:
        # Step 1: Classification
        classification = classify_message(message, source, group_id)
        
        # Step 2: Context Loading
        context = load_context_for_domain(classification["domain"])
        
        # Step 3: Model Selection
        tier = select_tier(classification["domain"], len(context.get("content", "")))
        
        # Step 4: Agent Execution
        agent_id = classification["agent"]
        
        print(f"🎯 Routing to {agent_id} (domain: {classification['domain']})")
        
        agent_context = {
            "message": message,
            "source": source, 
            "group_id": group_id,
            "role": role,
            "files_loaded": context.get("files_loaded", []),
            "classification": classification,
            "tier": tier
        }
        
        agent_result = registry.execute_agent(agent_id, message, agent_context)
        
        # Step 5: QA Validation
        if agent_result["status"] == "success":
            qa_result = validate_output(
                agent_result.get("result", {}),
                classification["domain"],
                []  # constraints
            )
        else:
            qa_result = {
                "passed": False,
                "reason": f"Agent execution failed: {agent_result.get('error', 'Unknown error')}"
            }
        
        # Step 6: Build Response
        response = {
            "status": "success" if agent_result["status"] == "success" and qa_result["passed"] else "failed",
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "routing": {
                "classification": classification,
                "context": {
                    "files_loaded": context.get("files_loaded", []),
                    "context_size": len(context.get("content", "")),
                    "truncated": context.get("truncated", False)
                },
                "model_tier": tier
            },
            "agent_result": agent_result,
            "qa_result": qa_result,
            "execution_result": {
                "status": "success" if qa_result["passed"] else "blocked_by_qa",
                "reason": qa_result.get("reason", "QA validation")
            }
        }
        
        return response
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "execution_id": execution_id,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def main():
    parser = argparse.ArgumentParser(description='Fixed OpenClaw Orchestrator')
    parser.add_argument('--message', required=True, help='Message to process')
    parser.add_argument('--source', default='dm', choices=['dm', 'group'], help='Message source')
    parser.add_argument('--group-id', help='Group ID for group messages')
    parser.add_argument('--role', help='User role in group')
    parser.add_argument('--test-agents', action='store_true', help='Test all agents first')
    
    args = parser.parse_args()
    
    if args.test_agents:
        print("🧪 Testing all agents...")
        agents = registry.get_available_agents()
        for agent_id in agents.keys():
            test_result = registry.test_agent(agent_id)
            status = "✅" if test_result.get("available") else "❌"
            print(f"{status} {agent_id}: {test_result}")
        print()
    
    # Execute orchestration
    print(f"🚀 Processing: {args.message[:60]}...")
    
    result = orchestrate_message(
        message=args.message,
        source=args.source,
        group_id=args.group_id,
        role=args.role
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()