#!/usr/bin/env python3
"""
Speed Integration Layer - Connects fast path, cost optimizer with main router
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add workspace to path for imports
workspace = Path(__file__).parent.parent
sys.path.append(str(workspace))

try:
    from core.fast_path import FastPathRouter
    from core.cost_optimizer import CostOptimizer
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class SpeedIntegration:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or workspace)
        self.fast_path = FastPathRouter(workspace_path)
        self.cost_optimizer = CostOptimizer(workspace_path)
        
        # Performance targets
        self.targets = {
            "l0_max_time_ms": 50,
            "l1_max_time_ms": 300,
            "l2_max_time_ms": 2000,
            "target_cache_hit_rate": 0.4,
            "target_cost_reduction": 0.5  # 50% cost reduction vs naive approach
        }
    
    def process_request(self, message: str, domain: str = "general", 
                       channel: str = "direct", context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point - decide how to process request for optimal speed/cost
        
        Args:
            message: User message
            domain: Task domain (general, email, legal, etc.)
            channel: Communication channel (direct, group)
            context: Additional context (user_id, urgency, etc.)
        
        Returns:
            Dict with response, processing_info, cost_info
        """
        
        start_time = time.time()
        context = context or {}
        
        # Step 1: Classify for fast path
        classification = self.fast_path.classify_request(message, channel)
        
        processing_info = {
            "classification": classification,
            "start_time": start_time,
            "domain": domain,
            "channel": channel
        }
        
        # Step 2: Try fast path (L0/L1)
        if classification["level"] in ["L0", "L1"]:
            fast_result = self._handle_fast_path(message, classification)
            
            if fast_result["success"]:
                end_time = time.time()
                processing_time_ms = (end_time - start_time) * 1000
                
                # Track usage for optimization
                self.cost_optimizer.track_usage(
                    tier="cache" if fast_result.get("source") == "cache" else "tier1",
                    actual_cost=0.0,  # Fast path is essentially free
                    response_time_ms=processing_time_ms,
                    tokens_used=len(message) // 4,  # Rough estimate
                    was_cached=fast_result.get("source") == "cache"
                )
                
                return {
                    "success": True,
                    "response": fast_result["response"],
                    "processing_info": {
                        **processing_info,
                        "path": "fast",
                        "level": classification["level"],
                        "processing_time_ms": processing_time_ms,
                        "source": fast_result.get("source", "generated")
                    },
                    "cost_info": {
                        "tier": "cache" if fast_result.get("source") == "cache" else "tier1",
                        "estimated_cost": 0.0,
                        "actual_cost": 0.0,
                        "tokens_used": len(message) // 4
                    }
                }
        
        # Step 3: Need full system (L2) - optimize model selection and context
        return self._handle_full_system(message, domain, context, processing_info)
    
    def _handle_fast_path(self, message: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle L0/L1 fast path requests"""
        
        if classification["level"] == "L0":
            cache_key = classification.get("cache_key")
            return self.fast_path.handle_l0_request(message, cache_key)
        
        elif classification["level"] == "L1":
            cache_key = classification.get("cache_key")
            return self.fast_path.handle_l1_request(message, cache_key)
        
        return {"success": False, "reason": "unsupported_level"}
    
    def _handle_full_system(self, message: str, domain: str, 
                           context: Dict[str, Any], processing_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle L2 requests with optimization"""
        
        # Analyze complexity for model selection
        complexity_indicators = self._analyze_complexity(message, domain, context)
        
        # Get optimal tier and context loading strategy
        tier_selection = self.cost_optimizer.select_optimal_tier(domain, complexity_indicators)
        context_optimization = self.cost_optimizer.optimize_context_loading(domain, message)
        
        # This would integrate with the main router
        # For now, return optimization recommendations
        return {
            "success": False,  # Indicates needs full system processing
            "requires_full_system": True,
            "optimization_recommendations": {
                "tier_selection": tier_selection,
                "context_optimization": context_optimization,
                "complexity_analysis": complexity_indicators
            },
            "processing_info": {
                **processing_info,
                "path": "full_system",
                "level": "L2",
                "optimization_applied": True
            }
        }
    
    def _analyze_complexity(self, message: str, domain: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze message complexity for optimization"""
        
        message_length = len(message)
        
        # Basic complexity indicators
        complexity = {
            "context_size": message_length * 2,  # Rough estimate
            "requires_reasoning": False,
            "has_tools": False,
            "is_urgent": False,
            "user_preference": context.get("model_tier")
        }
        
        # Detect reasoning requirements
        reasoning_keywords = [
            "למה", "מדוע", "כיצד", "איך", "תסביר", "תנתח", "השווה", "העריך",
            "why", "how", "explain", "analyze", "compare", "evaluate"
        ]
        
        if any(keyword in message.lower() for keyword in reasoning_keywords):
            complexity["requires_reasoning"] = True
        
        # Detect tool usage hints
        tool_keywords = [
            "קובץ", "קרא", "כתוב", "שלח", "בדוק", "הרץ", "צור",
            "file", "read", "write", "send", "check", "run", "create"
        ]
        
        if any(keyword in message.lower() for keyword in tool_keywords):
            complexity["has_tools"] = True
            complexity["tools"] = ["file_ops", "communication"]  # Rough estimate
        
        # Urgency detection
        urgent_keywords = ["דחוף", "מיידי", "חירום", "urgent", "immediate", "emergency", "🔴"]
        
        if any(keyword in message.lower() for keyword in urgent_keywords):
            complexity["is_urgent"] = True
        
        # Domain-specific complexity
        if domain == "legal":
            complexity["requires_reasoning"] = True
            complexity["context_size"] *= 2
        
        elif domain == "email" and message_length > 100:
            complexity["has_tools"] = True
            complexity["tools"] = ["email", "calendar"]
        
        elif domain == "group" and "סיכום" in message:
            complexity["has_tools"] = True
            complexity["tools"] = ["group_analysis", "summarization"]
        
        return complexity
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance and optimization report"""
        
        # Get cost optimizer report
        cost_report = self.cost_optimizer.get_usage_report()
        
        # Get fast path stats
        fast_path_stats = self.fast_path.get_fast_path_stats()
        
        # Calculate overall performance metrics
        total_requests = cost_report["total_requests"]
        cache_hits = fast_path_stats.get("total_cached_responses", 0)
        
        # Performance analysis
        performance_analysis = {
            "speed_optimization": {
                "avg_response_time_ms": cost_report["avg_response_time_ms"],
                "target_met": cost_report["avg_response_time_ms"] <= self.targets["l2_max_time_ms"],
                "cache_usage": f"{cache_hits} cached responses"
            },
            "cost_optimization": {
                "total_cost": cost_report["total_cost"],
                "avg_cost_per_request": cost_report["avg_cost_per_request"],
                "estimated_savings": cost_report["estimated_savings"],
                "savings_percentage": cost_report["savings_percentage"],
                "target_met": cost_report["savings_percentage"] >= (self.targets["target_cost_reduction"] * 100)
            },
            "tier_distribution": cost_report["tier_distribution"],
            "system_health": "healthy" if (
                cost_report["avg_response_time_ms"] <= self.targets["l2_max_time_ms"] and
                cost_report["savings_percentage"] >= (self.targets["target_cost_reduction"] * 100 * 0.5)
            ) else "needs_optimization"
        }
        
        # Recommendations
        recommendations = self.cost_optimizer.get_optimization_recommendations()
        
        # Fast path specific recommendations
        if fast_path_stats.get("total_cached_responses", 0) < total_requests * 0.2:
            recommendations.append("Consider caching more common responses")
        
        if cost_report["avg_response_time_ms"] > self.targets["l1_max_time_ms"]:
            recommendations.append("Expand fast path patterns to cover more queries")
        
        return {
            "summary": {
                "total_requests": total_requests,
                "total_cost": cost_report["total_cost"],
                "avg_response_time": f"{cost_report['avg_response_time_ms']:.1f}ms",
                "cost_savings": f"{cost_report['savings_percentage']:.1f}%"
            },
            "performance_analysis": performance_analysis,
            "detailed_metrics": {
                "cost_report": cost_report,
                "fast_path_stats": fast_path_stats
            },
            "recommendations": recommendations,
            "targets": self.targets
        }
    
    def optimize_for_user_patterns(self, user_id: str, recent_queries: List[str]) -> Dict[str, Any]:
        """Optimize based on user's recent query patterns"""
        
        # Analyze user patterns
        query_analysis = {
            "avg_length": sum(len(q) for q in recent_queries) / len(recent_queries) if recent_queries else 0,
            "common_domains": [],
            "frequent_patterns": [],
            "suggested_cache_entries": []
        }
        
        # Find common patterns in user queries
        for query in recent_queries:
            query_lower = query.lower()
            
            # Domain detection
            if any(word in query_lower for word in ["מייל", "email"]):
                query_analysis["common_domains"].append("email")
            elif any(word in query_lower for word in ["משימה", "task"]):
                query_analysis["common_domains"].append("tasks")
            elif any(word in query_lower for word in ["סטטוס", "status"]):
                query_analysis["common_domains"].append("status")
        
        # Count domain frequency
        domain_counts = {}
        for domain in query_analysis["common_domains"]:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Get most common domains
        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
        query_analysis["top_domains"] = [domain for domain, count in sorted_domains[:3]]
        
        # Suggestions for optimization
        suggestions = []
        
        if query_analysis["avg_length"] < 30:
            suggestions.append("User tends to send short queries - optimize for fast path")
        
        if "status" in query_analysis["top_domains"]:
            suggestions.append("User frequently checks status - increase cache TTL for status queries")
        
        if "email" in query_analysis["top_domains"]:
            suggestions.append("User frequently checks email - pre-load email context")
        
        return {
            "user_id": user_id,
            "analysis": query_analysis,
            "optimization_suggestions": suggestions,
            "recommended_tier_preference": "tier1" if query_analysis["avg_length"] < 50 else "tier2"
        }
    
    def benchmark_performance(self, test_queries: List[Dict[str, str]]) -> Dict[str, Any]:
        """Run performance benchmark on test queries"""
        
        results = {
            "total_queries": len(test_queries),
            "fast_path_count": 0,
            "full_system_count": 0,
            "avg_response_time_ms": 0.0,
            "total_cost": 0.0,
            "query_results": []
        }
        
        total_time_ms = 0.0
        total_cost = 0.0
        
        for i, test_query in enumerate(test_queries):
            message = test_query["message"]
            domain = test_query.get("domain", "general")
            
            start_time = time.time()
            result = self.process_request(message, domain)
            end_time = time.time()
            
            query_time_ms = (end_time - start_time) * 1000
            query_cost = result.get("cost_info", {}).get("actual_cost", 0.0)
            
            total_time_ms += query_time_ms
            total_cost += query_cost
            
            if result.get("processing_info", {}).get("path") == "fast":
                results["fast_path_count"] += 1
            else:
                results["full_system_count"] += 1
            
            results["query_results"].append({
                "query_index": i,
                "message": message[:50] + "..." if len(message) > 50 else message,
                "domain": domain,
                "response_time_ms": round(query_time_ms, 1),
                "cost": query_cost,
                "path": result.get("processing_info", {}).get("path", "unknown"),
                "success": result.get("success", False)
            })
        
        # Calculate averages
        if len(test_queries) > 0:
            results["avg_response_time_ms"] = total_time_ms / len(test_queries)
            results["total_cost"] = total_cost
            results["avg_cost_per_query"] = total_cost / len(test_queries)
            results["fast_path_percentage"] = (results["fast_path_count"] / len(test_queries)) * 100
        
        return results

def main():
    """CLI interface for testing and benchmarking"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  speed_integration.py process '<message>' [domain] [channel]")
        print("  speed_integration.py report")
        print("  speed_integration.py benchmark <test_file.json>")
        print("  speed_integration.py optimize-user <user_id> '<query1>' '<query2>' ...")
        return
    
    speed_integration = SpeedIntegration()
    command = sys.argv[1]
    
    if command == "process" and len(sys.argv) >= 3:
        message = sys.argv[2]
        domain = sys.argv[3] if len(sys.argv) > 3 else "general"
        channel = sys.argv[4] if len(sys.argv) > 4 else "direct"
        
        start_time = time.time()
        result = speed_integration.process_request(message, domain, channel)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000
        
        print(f"⚡ Processed in {processing_time:.1f}ms")
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            print(f"📊 Path: {result['processing_info']['path']} ({result['processing_info']['level']})")
            print(f"💰 Cost: ${result['cost_info']['actual_cost']:.4f}")
        else:
            print("🔄 Requires full system processing")
            recommendations = result.get("optimization_recommendations", {})
            if recommendations:
                tier = recommendations.get("tier_selection", {})
                print(f"💡 Recommended tier: {tier.get('tier', 'unknown')}")
                print(f"💰 Estimated cost: ${tier.get('estimated_cost', 0):.4f}")
    
    elif command == "report":
        report = speed_integration.get_performance_report()
        
        print("📊 Speed Integration Performance Report")
        print("=" * 50)
        
        summary = report["summary"]
        print(f"Total requests: {summary['total_requests']}")
        print(f"Total cost: ${summary['total_cost']:.4f}")
        print(f"Avg response time: {summary['avg_response_time']}")
        print(f"Cost savings: {summary['cost_savings']}")
        print()
        
        analysis = report["performance_analysis"]
        print("🎯 Performance Targets:")
        print(f"  Speed target met: {'✅' if analysis['speed_optimization']['target_met'] else '❌'}")
        print(f"  Cost target met: {'✅' if analysis['cost_optimization']['target_met'] else '❌'}")
        print(f"  System health: {analysis['system_health']}")
        print()
        
        if report["recommendations"]:
            print("💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")
    
    elif command == "benchmark" and len(sys.argv) >= 3:
        test_file = sys.argv[2]
        
        try:
            with open(test_file, 'r') as f:
                test_queries = json.load(f)
            
            print(f"🧪 Running benchmark with {len(test_queries)} queries...")
            results = speed_integration.benchmark_performance(test_queries)
            
            print(f"📊 Benchmark Results:")
            print(f"  Total queries: {results['total_queries']}")
            print(f"  Fast path: {results['fast_path_count']} ({results.get('fast_path_percentage', 0):.1f}%)")
            print(f"  Full system: {results['full_system_count']}")
            print(f"  Avg response time: {results['avg_response_time_ms']:.1f}ms")
            print(f"  Total cost: ${results['total_cost']:.4f}")
            print(f"  Avg cost per query: ${results.get('avg_cost_per_query', 0):.4f}")
            
        except FileNotFoundError:
            print(f"❌ Test file not found: {test_file}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in test file: {test_file}")
    
    elif command == "optimize-user" and len(sys.argv) >= 4:
        user_id = sys.argv[2]
        queries = sys.argv[3:]
        
        optimization = speed_integration.optimize_for_user_patterns(user_id, queries)
        
        print(f"👤 User Optimization for {user_id}:")
        print(f"  Avg query length: {optimization['analysis']['avg_length']:.1f}")
        print(f"  Top domains: {', '.join(optimization['analysis']['top_domains'])}")
        print(f"  Recommended tier: {optimization['recommended_tier_preference']}")
        print()
        
        if optimization["optimization_suggestions"]:
            print("💡 Suggestions:")
            for suggestion in optimization["optimization_suggestions"]:
                print(f"  • {suggestion}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()