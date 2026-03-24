#!/usr/bin/env python3
"""
Regression Test Pack - 15 fixed scenarios to validate routing & execution.
Tests the complete pipeline: message → router → agent → QA → response

Usage:
    python3 tests/regression_pack.py --run-all
    python3 tests/regression_pack.py --scenario 1
    python3 tests/regression_pack.py --report-only
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add workspace to path
WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
sys.path.insert(0, str(WORKSPACE / "core"))
sys.path.insert(0, str(WORKSPACE / "scripts"))

from execution_pipeline import ExecutionPipeline

# Test scenarios with expected routing
REGRESSION_SCENARIOS = [
    {
        "id": 1,
        "name": "Legal Contract Analysis",
        "message": "חוזה עבודה לבדיקה משפטית - צריך לבדוק סעיף 3.1",
        "channel": "direct",
        "expected": {
            "domain": "legal",
            "agent": "masha",
            "model_tier": "tier3",
            "requires_approval": True,
            "context_files_include": ["policies/EXTERNAL_ACTIONS_POLICY.md"]
        }
    },
    {
        "id": 2,
        "name": "Fitness Tracking - Meal",
        "message": "אכלתי חזה עוף עם אורז וירקות, בערך 400 קלוריות",
        "channel": "direct",
        "expected": {
            "domain": "fitness",
            "agent": "dana",
            "model_tier": "tier1",
            "requires_approval": False,
            "file_update": "state/fitness_tracker.md"
        }
    },
    {
        "id": 3,
        "name": "WhatsApp Group Message",
        "message": "שלום לכולם, איך אתם?",
        "channel": "whatsapp",
        "group_id": "family_group",
        "expected": {
            "domain": "whatsapp_group",
            "agent": "odya",
            "model_tier": "tier1",
            "requires_approval": True,
            "low_response_confidence": True
        }
    },
    {
        "id": 4,
        "name": "Fitness Tracking - Weight",
        "message": "שקלתי היום 71.2 קילו",
        "channel": "direct",
        "expected": {
            "domain": "fitness",
            "agent": "dana",
            "model_tier": "tier1",
            "requires_approval": False,
            "file_update": "state/fitness_tracker.md"
        }
    },
    {
        "id": 5,
        "name": "Research Task",
        "message": "תחקרי לי על השוק של AI agents בישראל",
        "channel": "direct",
        "expected": {
            "domain": "research",
            "agent": "tzofit",
            "model_tier": "tier2",
            "requires_approval": False
        }
    },
    {
        "id": 6,
        "name": "General Question",
        "message": "מה מזג האוויר היום?",
        "channel": "direct",
        "expected": {
            "domain": "general",
            "agent": "direct",
            "model_tier": "tier2",
            "requires_approval": False
        }
    },
    {
        "id": 7,
        "name": "Legal - Contract Review",
        "message": "סיכום חוזה השכרה - בדקי את התנאים",
        "channel": "direct",
        "expected": {
            "domain": "legal",
            "agent": "masha",
            "model_tier": "tier3",
            "requires_approval": True
        }
    },
    {
        "id": 8,
        "name": "Marketing Request",
        "message": "תכיני פוסט לטיקטוק על הווילה בליתוס",
        "channel": "direct",
        "expected": {
            "domain": "marketing", 
            "agent": "tali",
            "model_tier": "tier2",
            "requires_approval": False
        }
    },
    {
        "id": 9,
        "name": "Fitness Complex",
        "message": "אכלתי ארוחת בוקר: 3 ביצים, לחם מלא, אבוקדו. בערך 500 קק\"ל",
        "channel": "direct",
        "expected": {
            "domain": "fitness",
            "agent": "dana",
            "model_tier": "tier1",
            "requires_approval": False,
            "file_update": "state/fitness_tracker.md"
        }
    },
    {
        "id": 10,
        "name": "Legal - Brief Query",
        "message": "זה חוזה תקין?",
        "channel": "direct",
        "expected": {
            "domain": "legal",
            "agent": "masha",
            "model_tier": "tier3",
            "requires_approval": True
        }
    },
    {
        "id": 11,
        "name": "Group - Direct Mention",
        "message": "דבורה, מה דעתך על הנושא?",
        "channel": "whatsapp",
        "group_id": "work_group",
        "expected": {
            "domain": "whatsapp_group",
            "agent": "odya",
            "model_tier": "tier1",
            "requires_approval": True,
            "high_response_confidence": True
        }
    },
    {
        "id": 12,
        "name": "System Status",
        "message": "מה סטטוס המערכת?",
        "channel": "direct",
        "expected": {
            "domain": "automation",
            "agent": "eti",
            "model_tier": "tier1",
            "requires_approval": False
        }
    },
    {
        "id": 13,
        "name": "Mixed Domain - Fitness + Legal",
        "message": "אכלתי ארוחה והקחתי חוזה עבודה לבדיקה",
        "channel": "direct",
        "expected": {
            "domain": "legal",  # Legal should take precedence
            "agent": "masha",
            "model_tier": "tier3",
            "requires_approval": True
        }
    },
    {
        "id": 14,
        "name": "Empty/Minimal Input",
        "message": "היי",
        "channel": "direct",
        "expected": {
            "domain": "general",
            "agent": "direct",
            "model_tier": "tier2",
            "requires_approval": False
        }
    },
    {
        "id": 15,
        "name": "Long Complex Message",
        "message": "שלום דבורה, אני צריך עזרה עם כמה דברים: ראשית, אכלתי היום ארוחת צהריים עם דג סלמון וירקות, שנית יש לי חוזה עבודה שצריך בדיקה משפטית, ושלישית רציתי לשאול אותך מה דעתך על המצב הכלכלי בעולם",
        "channel": "direct",
        "expected": {
            "domain": "legal",  # Legal should take precedence over fitness/general
            "agent": "masha", 
            "model_tier": "tier3",
            "requires_approval": True
        }
    }
]

class RegressionTester:
    def __init__(self):
        self.pipeline = ExecutionPipeline(str(WORKSPACE))
        self.results = []
        
    def run_scenario(self, scenario: dict) -> dict:
        """Run a single test scenario"""
        print(f"🧪 Running scenario {scenario['id']}: {scenario['name']}")
        
        try:
            # Execute through pipeline
            result = self.pipeline.execute(
                message=scenario["message"],
                channel=scenario["channel"], 
                group_id=scenario.get("group_id"),
                metadata={"test_id": scenario["id"]}
            )
            
            # Extract key metrics for validation
            actual = {
                "domain": result["routing"]["classification"]["domain"],
                "agent": result["routing"]["classification"]["agent"],
                "model_tier": result["routing"]["model"],
                "confidence": result["routing"]["classification"]["confidence"],
                "qa_passed": result["qa_result"]["passed"],
                "qa_score": result["qa_result"]["score"],
                "approval_required": len(result["qa_result"]["blocking_issues"]) > 0,
                "context_files": result["routing"]["context"]["files_loaded"],
                "context_size": result["routing"]["context"]["context_size"],
                "execution_status": result["execution_result"]["status"],
                "cost_estimate": self._estimate_cost(result),
                "duration_ms": result["execution_summary"]["duration_ms"]
            }
            
            # Validate against expected results
            validation = self._validate_scenario(scenario["expected"], actual)
            
            return {
                "scenario": scenario,
                "actual": actual,
                "validation": validation,
                "raw_result": result,
                "status": "completed"
            }
            
        except Exception as e:
            return {
                "scenario": scenario,
                "error": str(e),
                "status": "failed"
            }
    
    def _validate_scenario(self, expected: dict, actual: dict) -> dict:
        """Validate actual results against expected"""
        validations = {}
        score = 0
        total = 0
        
        # Domain check
        if "domain" in expected:
            validations["domain"] = expected["domain"] == actual["domain"]
            total += 1
            if validations["domain"]:
                score += 1
                
        # Agent check  
        if "agent" in expected:
            validations["agent"] = expected["agent"] == actual["agent"]
            total += 1
            if validations["agent"]:
                score += 1
                
        # Model tier check
        if "model_tier" in expected:
            validations["model_tier"] = expected["model_tier"] == actual["model_tier"]
            total += 1
            if validations["model_tier"]:
                score += 1
                
        # Approval requirement check
        if "requires_approval" in expected:
            validations["requires_approval"] = expected["requires_approval"] == actual["approval_required"]
            total += 1
            if validations["requires_approval"]:
                score += 1
                
        # Context files check
        if "context_files_include" in expected:
            includes_required = all(f in actual["context_files"] for f in expected["context_files_include"])
            validations["context_files"] = includes_required
            total += 1
            if validations["context_files"]:
                score += 1
                
        return {
            "validations": validations,
            "score": score,
            "total": total,
            "percentage": (score / total * 100) if total > 0 else 0,
            "passed": score == total
        }
    
    def _estimate_cost(self, result: dict) -> float:
        """Estimate cost based on model tier and usage"""
        tier = result["routing"]["model"]
        context_size = result["routing"]["context"]["context_size"]
        
        # Rough token estimation (1.25 chars per token)
        estimated_tokens = context_size / 1.25
        
        # Cost per 1M tokens
        costs = {
            "tier1": {"input": 3.0, "output": 15.0},
            "tier2": {"input": 3.0, "output": 15.0}, 
            "tier3": {"input": 15.0, "output": 75.0}
        }
        
        if tier in costs:
            input_cost = (estimated_tokens / 1_000_000) * costs[tier]["input"]
            output_cost = (500 / 1_000_000) * costs[tier]["output"]  # Assume 500 output tokens
            return round(input_cost + output_cost, 6)
        
        return 0.0
    
    def run_all_scenarios(self) -> list:
        """Run all regression scenarios"""
        print(f"🚀 Running {len(REGRESSION_SCENARIOS)} regression scenarios...")
        
        for scenario in REGRESSION_SCENARIOS:
            result = self.run_scenario(scenario)
            self.results.append(result)
        
        return self.results
    
    def generate_report(self) -> dict:
        """Generate comprehensive test report"""
        if not self.results:
            return {"error": "No test results available"}
        
        # Calculate overall stats
        passed_scenarios = sum(1 for r in self.results if r.get("validation", {}).get("passed", False))
        total_scenarios = len(self.results)
        
        # Calculate validation breakdown
        validation_stats = {}
        for result in self.results:
            if "validation" in result:
                for check, passed in result["validation"]["validations"].items():
                    if check not in validation_stats:
                        validation_stats[check] = {"passed": 0, "total": 0}
                    validation_stats[check]["total"] += 1
                    if passed:
                        validation_stats[check]["passed"] += 1
        
        # Cost analysis
        total_cost = sum(r.get("actual", {}).get("cost_estimate", 0) for r in self.results)
        
        # Performance analysis
        avg_duration = sum(r.get("actual", {}).get("duration_ms", 0) for r in self.results) / len(self.results)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_scenarios": total_scenarios,
                "passed_scenarios": passed_scenarios,
                "failed_scenarios": total_scenarios - passed_scenarios,
                "success_rate": (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0,
                "total_estimated_cost": round(total_cost, 6),
                "average_duration_ms": round(avg_duration, 1)
            },
            "validation_breakdown": validation_stats,
            "scenario_results": self.results,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> list:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_count = sum(1 for r in self.results if not r.get("validation", {}).get("passed", True))
        
        if failed_count > 0:
            recommendations.append(f"Fix {failed_count} failing scenarios for full system reliability")
            
        # Check for specific patterns
        routing_failures = sum(1 for r in self.results 
                              if not r.get("validation", {}).get("validations", {}).get("domain", True) or 
                                 not r.get("validation", {}).get("validations", {}).get("agent", True))
        
        if routing_failures > 2:
            recommendations.append("Review routing logic - multiple domain/agent mismatches detected")
            
        # Cost optimization
        high_cost_scenarios = sum(1 for r in self.results if r.get("actual", {}).get("cost_estimate", 0) > 0.01)
        
        if high_cost_scenarios > 5:
            recommendations.append("Consider cost optimization - several high-cost scenarios detected")
            
        return recommendations

def main():
    parser = argparse.ArgumentParser(description="Regression test pack for Dvorah architecture")
    parser.add_argument("--run-all", action="store_true", help="Run all scenarios")
    parser.add_argument("--scenario", type=int, help="Run specific scenario by ID")
    parser.add_argument("--report-only", action="store_true", help="Generate report from existing results")
    parser.add_argument("--output", default="regression_report.json", help="Output file for report")
    
    args = parser.parse_args()
    
    tester = RegressionTester()
    
    if args.scenario:
        scenario = next((s for s in REGRESSION_SCENARIOS if s["id"] == args.scenario), None)
        if not scenario:
            print(f"❌ Scenario {args.scenario} not found")
            return
        
        result = tester.run_scenario(scenario)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.run_all:
        tester.run_all_scenarios()
        report = tester.generate_report()
        
        # Save report
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n📊 Regression Test Summary:")
        print(f"✅ Passed: {report['summary']['passed_scenarios']}/{report['summary']['total_scenarios']} ({report['summary']['success_rate']:.1f}%)")
        print(f"💰 Total Cost: ${report['summary']['total_estimated_cost']:.6f}")
        print(f"⏱️  Avg Duration: {report['summary']['average_duration_ms']}ms")
        print(f"📄 Full report: {args.output}")
        
        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in report["recommendations"]:
                print(f"   • {rec}")
    
    elif args.report_only:
        # Generate report from existing results (if any)
        print("📄 Report-only mode not implemented yet")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()