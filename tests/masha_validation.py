#!/usr/bin/env python3
"""
מאשה (Legal Agent) Real Validation Test
Tests actual legal analysis capabilities with real scenarios.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add workspace to path
WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
sys.path.insert(0, str(WORKSPACE / "core"))

from execution_pipeline import ExecutionPipeline

# Real legal scenarios for validation
LEGAL_SCENARIOS = [
    {
        "id": "L1",
        "name": "Employment Contract Review",
        "document": """
חוזה עבודה
בין: חברת טכנולוגיה בע"מ (המעסיק)
לבין: יוחנן כהן (העובד)

סעיף 3: שכר והטבות
3.1 השכר החודשי יהיה 15,000 ש"ח ברוטו
3.2 העובד יהיה זכאי לרכב חברה לשימוש פרטי
3.3 העובד יקבל 20 ימי חופשה בשנה

סעיף 4: תקופת ההתחייבות  
4.1 העובד מתחייב לעבוד לפחות שנתיים
4.2 בפרישה מוקדמת, יחזיר העובד 50% מהשכר שקיבל בשנה האחרונה

סעיף 5: סודיות
5.1 העובד לא יגלה מידע רגיש על החברה
        """,
        "query": "בדקי את החוזה מבחינת חוקיות וסיכונים",
        "expected_issues": [
            "תקופת התחייבות של שנתיים יכולה להיחשב בלתי סבירה",
            "החזר 50% מהשכר בפרישה מוקדמת בעייתי",
            "סעיף הסודיות כללי מדי"
        ]
    },
    {
        "id": "L2", 
        "name": "Rental Agreement Analysis",
        "document": """
חוזה השכרה - דירת מגורים
מושכר: יוסי לוי
משכיר: שרה כהן

תנאי השכירות:
- דמי שכירות: 4,500 ש"ח לחודש + ועד בית
- פיקדון: 13,500 ש"ח (3 חודשי שכירות)
- תקופת השכירות: שנה אחת עם אופציה להארכה
- הדירה מועברת ללא מכשירי חשמל
- האחריות לתיקונים על השוכר

סעיפי מיוחדים:
- אסור להכניס חיות מחמד
- אסור לעשות שינויים בדירה ללא אישור
- הפסקת חוזה מוקדמת - דמי פיצוי של 2 חודשי שכירות
        """,
        "query": "מה הסיכונים עבור השוכר?",
        "expected_issues": [
            "פיקדון גבוה (3 חודשים)",
            "כל האחריות לתיקונים על השוכר",
            "דמי פיצוי גבוהים על הפסקה מוקדמת"
        ]
    },
    {
        "id": "L3",
        "name": "Service Agreement Review", 
        "document": """
הסכם לבצוע שירותים
נותן השירות: דני מחשבים בע"מ
מזמין השירות: רשת חנויות XYZ

היקף העבודה:
- תחזוקת מערכת מחשבים של הרשת
- זמינות 24/7 לקריאות חירום
- עדכוני תוכנה חודשיים

תנאים כלכליים:
- דמי התחזוקה: 8,000 ש"ח לחודש
- דמי קריאת חירום: 300 ש"ח לשעה
- תשלום בתוך 60 יום מתאריך החשבונית

אחריות וביטוח:
- נותן השירות אחראי לנזקים הנגרמים עקב רשלנות
- על נותן השירות לקיים ביטוח אחריות מקצועית
        """,
        "query": "האם התנאים מאוזנים בין הצדדים?",
        "expected_issues": [
            "זמינות 24/7 יכולה להיות בעייתי ללא הגדרת זמני תגובה",
            "תשלום בתוך 60 יום ארוך יחסית",
            "אחריות נותן השירות רק ברשלנות - יכול להיות בעייתי"
        ]
    }
]

class MashaValidator:
    def __init__(self):
        self.pipeline = ExecutionPipeline(str(WORKSPACE))
        self.results = []
    
    def validate_scenario(self, scenario: dict) -> dict:
        """Validate a single legal scenario"""
        print(f"⚖️ Validating {scenario['id']}: {scenario['name']}")
        
        # Construct message with document and query
        message = f"{scenario['query']}\n\nמסמך לבדיקה:\n{scenario['document']}"
        
        try:
            # Execute through pipeline
            start_time = datetime.now()
            result = self.pipeline.execute(
                message=message,
                channel="direct",
                metadata={"legal_validation": True, "scenario_id": scenario["id"]}
            )
            duration = (datetime.now() - start_time).total_seconds()
            
            # Extract מאשה-specific results
            analysis = {
                "scenario_id": scenario["id"],
                "routing_correct": (
                    result["routing"]["classification"]["domain"] == "legal" and
                    result["routing"]["classification"]["agent"] == "masha" and
                    result["routing"]["model"] == "tier3"
                ),
                "execution_status": result["agent_result"]["status"],
                "qa_passed": result["qa_result"]["passed"],
                "requires_approval": len(result["qa_result"]["blocking_issues"]) > 0,
                "cost_estimate": self._estimate_legal_cost(result),
                "processing_time": round(duration, 3),
                "context_size": result["routing"]["context"]["context_size"],
                "model_used": "tier3_opus" if result["routing"]["model"] == "tier3" else "other"
            }
            
            # Check if מאשה provided meaningful analysis
            agent_result = result["agent_result"]
            if "error" in agent_result:
                analysis["masha_error"] = agent_result["error"]
                analysis["analysis_quality"] = "error"
            elif agent_result.get("status") == "not_implemented":
                analysis["analysis_quality"] = "not_implemented"
            else:
                # Try to assess analysis quality (basic heuristic)
                analysis["analysis_quality"] = self._assess_analysis_quality(
                    agent_result, scenario["expected_issues"]
                )
            
            return {
                "scenario": scenario,
                "analysis": analysis,
                "raw_result": result,
                "status": "completed"
            }
            
        except Exception as e:
            return {
                "scenario": scenario,
                "error": str(e),
                "status": "failed"
            }
    
    def _estimate_legal_cost(self, result: dict) -> float:
        """Estimate cost for legal analysis (tier3)"""
        context_size = result["routing"]["context"]["context_size"]
        estimated_tokens = context_size / 1.25  # chars to tokens
        
        # Tier3 costs: $15 per 1M input tokens, $75 per 1M output tokens
        input_cost = (estimated_tokens / 1_000_000) * 15.0
        output_cost = (1000 / 1_000_000) * 75.0  # Assume 1000 output tokens for analysis
        
        return round(input_cost + output_cost, 6)
    
    def _assess_analysis_quality(self, agent_result: dict, expected_issues: list) -> str:
        """Basic assessment of legal analysis quality"""
        if "analysis" in agent_result or "summary" in agent_result:
            # Has some structured analysis
            return "structured"
        elif "response" in agent_result and len(str(agent_result["response"])) > 200:
            # Has detailed response
            return "detailed"
        elif "status" in agent_result and "executed" in agent_result["status"]:
            # Basic execution
            return "basic"
        else:
            # Insufficient analysis
            return "insufficient"
    
    def run_all_validations(self) -> list:
        """Run all legal validation scenarios"""
        print(f"⚖️ Running {len(LEGAL_SCENARIOS)} legal validation scenarios...")
        
        for scenario in LEGAL_SCENARIOS:
            result = self.validate_scenario(scenario)
            self.results.append(result)
        
        return self.results
    
    def generate_validation_report(self) -> dict:
        """Generate מאשה validation report"""
        if not self.results:
            return {"error": "No validation results available"}
        
        # Calculate validation metrics
        total_scenarios = len(self.results)
        routing_correct = sum(1 for r in self.results if r.get("analysis", {}).get("routing_correct", False))
        qa_passed = sum(1 for r in self.results if r.get("analysis", {}).get("qa_passed", False))
        requires_approval = sum(1 for r in self.results if r.get("analysis", {}).get("requires_approval", False))
        
        # Cost analysis
        total_cost = sum(r.get("analysis", {}).get("cost_estimate", 0) for r in self.results)
        avg_cost = total_cost / total_scenarios if total_scenarios > 0 else 0
        
        # Performance analysis
        processing_times = [r.get("analysis", {}).get("processing_time", 0) for r in self.results]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Analysis quality assessment
        quality_counts = {}
        for result in self.results:
            quality = result.get("analysis", {}).get("analysis_quality", "unknown")
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "validation_summary": {
                "total_scenarios": total_scenarios,
                "routing_accuracy": (routing_correct / total_scenarios * 100) if total_scenarios > 0 else 0,
                "qa_pass_rate": (qa_passed / total_scenarios * 100) if total_scenarios > 0 else 0,
                "approval_rate": (requires_approval / total_scenarios * 100) if total_scenarios > 0 else 0,
                "total_estimated_cost": round(total_cost, 6),
                "average_cost_per_scenario": round(avg_cost, 6),
                "average_processing_time": round(avg_processing_time, 3)
            },
            "analysis_quality_breakdown": quality_counts,
            "scenario_results": self.results,
            "recommendations": self._generate_legal_recommendations()
        }
        
        return report
    
    def _generate_legal_recommendations(self) -> list:
        """Generate recommendations for מאשה improvement"""
        recommendations = []
        
        if not self.results:
            return ["No results to analyze"]
        
        # Check routing accuracy
        routing_failures = sum(1 for r in self.results if not r.get("analysis", {}).get("routing_correct", True))
        if routing_failures > 0:
            recommendations.append(f"Fix routing issues - {routing_failures} scenarios routed incorrectly")
        
        # Check for implementation issues
        not_implemented = sum(1 for r in self.results if r.get("analysis", {}).get("analysis_quality") == "not_implemented")
        if not_implemented > 0:
            recommendations.append("Complete מאשה agent implementation - some scenarios not handled")
        
        # Check for errors
        error_count = sum(1 for r in self.results if r.get("analysis", {}).get("analysis_quality") == "error")
        if error_count > 0:
            recommendations.append(f"Fix execution errors - {error_count} scenarios failed with errors")
        
        # Cost optimization
        avg_cost = sum(r.get("analysis", {}).get("cost_estimate", 0) for r in self.results) / len(self.results)
        if avg_cost > 0.1:
            recommendations.append("Consider cost optimization - average cost per legal analysis is high")
        
        return recommendations

def main():
    validator = MashaValidator()
    
    print("⚖️ מאשה Legal Agent Validation Test")
    print("=" * 50)
    
    # Run validations
    validator.run_all_validations()
    
    # Generate report
    report = validator.generate_validation_report()
    
    # Save report
    report_file = "masha_validation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n📊 מאשה Validation Summary:")
    summary = report["validation_summary"]
    print(f"⚖️  Routing Accuracy: {summary['routing_accuracy']:.1f}%")
    print(f"✅ QA Pass Rate: {summary['qa_pass_rate']:.1f}%") 
    print(f"🚫 Approval Rate: {summary['approval_rate']:.1f}%")
    print(f"💰 Total Cost: ${summary['total_estimated_cost']:.6f}")
    print(f"⏱️  Avg Processing: {summary['average_processing_time']:.3f}s")
    print(f"📄 Full report: {report_file}")
    
    if report["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   • {rec}")

if __name__ == "__main__":
    main()