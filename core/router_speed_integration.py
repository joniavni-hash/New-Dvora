#!/usr/bin/env python3
"""
Router Speed Integration - Connects speed optimization with main router
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add workspace to path
workspace = Path(__file__).parent.parent
sys.path.append(str(workspace))

try:
    from core.speed_integration import SpeedIntegration
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class RouterSpeedIntegration:
    """
    Integration layer between the main router and speed optimization system
    This would be called by the main router before full processing
    """
    
    def __init__(self, workspace_path: str = None):
        self.speed_integration = SpeedIntegration(workspace_path)
        
    def pre_process_message(self, message: str, domain: str, channel: str = "direct", 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Pre-process message to determine if it can be handled via fast path
        
        This is called by the main router before loading full context
        
        Returns:
            - If fast path successful: complete response
            - If needs full system: optimization recommendations
        """
        
        result = self.speed_integration.process_request(message, domain, channel, context)
        
        if result["success"]:
            # Fast path successful - return complete response
            return {
                "handled": True,
                "response": result["response"],
                "processing_info": result["processing_info"],
                "cost_info": result["cost_info"],
                "skip_full_processing": True
            }
        else:
            # Needs full system - return optimization recommendations
            optimization = result.get("optimization_recommendations", {})
            
            return {
                "handled": False,
                "skip_full_processing": False,
                "optimization_recommendations": {
                    "suggested_tier": optimization.get("tier_selection", {}).get("tier", "tier2"),
                    "suggested_model": optimization.get("tier_selection", {}).get("model", "sonnet"),
                    "estimated_cost": optimization.get("tier_selection", {}).get("estimated_cost", 0.01),
                    "context_strategy": optimization.get("context_optimization", {}).get("strategy", "selective"),
                    "suggested_files": optimization.get("context_optimization", {}).get("suggested_files", []),
                    "complexity_analysis": optimization.get("complexity_analysis", {})
                },
                "processing_info": result["processing_info"]
            }
    
    def post_process_usage(self, tier: str, actual_cost: float, response_time_ms: float, 
                          tokens_used: int, was_successful: bool = True):
        """
        Track actual usage after full system processing
        This helps improve future optimization decisions
        """
        
        self.speed_integration.cost_optimizer.track_usage(
            tier=tier,
            actual_cost=actual_cost,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            was_cached=False  # Full system is never cached
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get speed optimization system status for monitoring"""
        
        report = self.speed_integration.get_performance_report()
        
        # Simplified status for main system
        return {
            "fast_path_available": True,
            "cache_hit_rate": report["detailed_metrics"]["fast_path_stats"].get("total_cached_responses", 0),
            "avg_response_time_ms": report["summary"]["avg_response_time"].replace("ms", ""),
            "cost_optimization_active": True,
            "total_cost_savings": report["summary"]["cost_savings"],
            "system_health": report["performance_analysis"]["system_health"],
            "recommendations_count": len(report["recommendations"])
        }
    
    def optimize_for_heartbeat(self) -> Dict[str, Any]:
        """
        Optimize system during heartbeat periods
        Clean cache, update patterns, etc.
        """
        
        # Clean old cache files
        cleanup_result = self.speed_integration.fast_path.cleanup_cache(max_age_hours=12)
        
        # Get current stats
        stats = self.speed_integration.fast_path.get_fast_path_stats()
        
        return {
            "cache_cleanup": cleanup_result,
            "current_stats": stats,
            "optimization_completed": True
        }
    
    def suggest_user_tier_preference(self, user_id: str, recent_queries: List[str]) -> str:
        """
        Suggest optimal default tier for specific user based on their patterns
        Called by user management system
        """
        
        analysis = self.speed_integration.optimize_for_user_patterns(user_id, recent_queries)
        return analysis.get("recommended_tier_preference", "tier2")

# Example integration with hypothetical main router
def integrate_with_main_router():
    """
    Example of how this would integrate with the main router
    This is pseudocode showing the integration pattern
    """
    
    router_integration = RouterSpeedIntegration()
    
    def main_router_process_message(message: str, domain: str, user_context: Dict[str, Any]):
        """Hypothetical main router function"""
        
        # Step 1: Try speed optimization first
        speed_result = router_integration.pre_process_message(
            message=message,
            domain=domain, 
            channel=user_context.get("channel", "direct"),
            context=user_context
        )
        
        if speed_result["handled"]:
            # Fast path successful - return immediately
            return {
                "response": speed_result["response"],
                "cost": speed_result["cost_info"]["actual_cost"],
                "processing_time_ms": speed_result["processing_info"]["processing_time_ms"],
                "path": "fast"
            }
        
        # Step 2: Use optimization recommendations for full processing
        optimization = speed_result["optimization_recommendations"]
        
        # Apply tier selection
        selected_tier = optimization["suggested_tier"]
        selected_model = optimization["suggested_model"]
        
        # Apply context optimization
        context_files = optimization["suggested_files"][:5]  # Limit context loading
        
        # Process with full system (hypothetical)
        full_result = process_with_full_system(
            message=message,
            model=selected_model,
            context_files=context_files,
            domain=domain
        )
        
        # Step 3: Track usage for learning
        router_integration.post_process_usage(
            tier=selected_tier,
            actual_cost=full_result.get("cost", 0.01),
            response_time_ms=full_result.get("processing_time_ms", 1000),
            tokens_used=full_result.get("tokens_used", 2000)
        )
        
        return {
            "response": full_result["response"],
            "cost": full_result["cost"],
            "processing_time_ms": full_result["processing_time_ms"],
            "path": "optimized_full_system",
            "optimization_applied": True
        }
    
    def process_with_full_system(message: str, model: str, context_files: List[str], domain: str):
        """Hypothetical full system processing"""
        return {
            "response": f"Full system response for: {message[:30]}...",
            "cost": 0.008,
            "processing_time_ms": 1200,
            "tokens_used": 1800
        }

def main():
    """CLI interface for testing router integration"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  router_speed_integration.py test '<message>' [domain]")
        print("  router_speed_integration.py status")
        print("  router_speed_integration.py optimize-heartbeat")
        print("  router_speed_integration.py suggest-tier <user_id> '<query1>' '<query2>' ...")
        return
    
    integration = RouterSpeedIntegration()
    command = sys.argv[1]
    
    if command == "test" and len(sys.argv) >= 3:
        message = sys.argv[2]
        domain = sys.argv[3] if len(sys.argv) > 3 else "general"
        
        result = integration.pre_process_message(message, domain)
        
        if result["handled"]:
            print("✅ Handled by fast path:")
            print(f"   Response: {result['response']}")
            print(f"   Cost: ${result['cost_info']['actual_cost']:.4f}")
            print(f"   Time: {result['processing_info']['processing_time_ms']:.1f}ms")
        else:
            print("🔄 Needs full system processing:")
            opt = result["optimization_recommendations"]
            print(f"   Suggested tier: {opt['suggested_tier']} ({opt['suggested_model']})")
            print(f"   Estimated cost: ${opt['estimated_cost']:.4f}")
            print(f"   Context strategy: {opt['context_strategy']}")
            print(f"   Suggested files: {len(opt['suggested_files'])}")
    
    elif command == "status":
        status = integration.get_system_status()
        print("📊 Speed Integration Status:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif command == "optimize-heartbeat":
        result = integration.optimize_for_heartbeat()
        print("🧹 Heartbeat optimization completed:")
        print(f"   Cache files cleaned: {result['cache_cleanup'].get('cleaned_files', 0)}")
        print(f"   Current cache size: {result['current_stats'].get('total_cached_responses', 0)} responses")
    
    elif command == "suggest-tier" and len(sys.argv) >= 4:
        user_id = sys.argv[2]
        queries = sys.argv[3:]
        
        suggested_tier = integration.suggest_user_tier_preference(user_id, queries)
        print(f"👤 Suggested tier for user {user_id}: {suggested_tier}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()