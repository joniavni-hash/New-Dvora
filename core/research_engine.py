#!/usr/bin/env python3
"""
Tzofit Research Engine - Proactive research and intelligence system
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class ResearchQuery:
    id: str
    topic: str
    query_type: str  # "trend", "opportunity", "competitive", "market"
    keywords: List[str]
    sources: List[str]
    frequency: str  # "daily", "weekly", "monthly", "one-time"
    priority: int  # 1-5
    created_at: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    active: bool = True

@dataclass
class ResearchResult:
    query_id: str
    timestamp: str
    findings: List[Dict[str, Any]]
    insights: List[str]
    actionable_items: List[Dict[str, Any]]
    confidence_score: float
    sources_used: List[str]
    processing_time_ms: float

class ResearchType(Enum):
    TREND_DETECTION = "trend"
    OPPORTUNITY_MINING = "opportunity" 
    COMPETITIVE_INTEL = "competitive"
    MARKET_ANALYSIS = "market"
    TECHNOLOGY_WATCH = "tech"

class TzofitResearchEngine:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE",
                                                             Path.home() / ".openclaw" / "workspace"))
        self.research_dir = self.workspace / "research"
        self.research_dir.mkdir(parents=True, exist_ok=True)
        
        # Research configuration files
        self.queries_file = self.research_dir / "active_queries.json"
        self.results_dir = self.research_dir / "results"
        self.insights_dir = self.research_dir / "insights"
        self.alerts_dir = self.research_dir / "alerts"
        
        for directory in [self.results_dir, self.insights_dir, self.alerts_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Load predefined research areas
        self._initialize_default_queries()
        
        # Active queries
        self.active_queries = self._load_queries()
    
    def _initialize_default_queries(self):
        """Initialize default research queries for Yoni's domains"""
        
        default_queries = [
            ResearchQuery(
                id="ai_trends_daily",
                topic="AI Industry Trends",
                query_type="trend",
                keywords=["artificial intelligence", "LLM", "Claude", "OpenAI", "Anthropic", "AI funding", "AI regulation"],
                sources=["techcrunch", "ycombinator", "arxiv", "twitter", "linkedin"],
                frequency="daily",
                priority=4,
                created_at=datetime.now().isoformat()
            ),
            ResearchQuery(
                id="investment_opportunities",
                topic="Investment Opportunities",
                query_type="opportunity",
                keywords=["seed funding", "series A", "Israeli startups", "tech IPO", "M&A deals"],
                sources=["crunchbase", "techaviv", "calcalist", "globes"],
                frequency="weekly",
                priority=3,
                created_at=datetime.now().isoformat()
            ),
            ResearchQuery(
                id="linear_motors_market",
                topic="Linear Motors & Automation Market",
                query_type="market",
                keywords=["linear motors", "industrial automation", "motion control", "servo systems"],
                sources=["industry_reports", "patents", "company_news"],
                frequency="weekly", 
                priority=3,
                created_at=datetime.now().isoformat()
            ),
            ResearchQuery(
                id="real_estate_greece",
                topic="Greek Real Estate & Tourism",
                query_type="market",
                keywords=["Greece real estate", "vacation rentals", "Porto Rafti", "Airbnb Greece"],
                sources=["property_sites", "tourism_data", "local_news"],
                frequency="monthly",
                priority=2,
                created_at=datetime.now().isoformat()
            ),
            ResearchQuery(
                id="legal_tech_innovations",
                topic="Legal Technology Innovations",
                query_type="tech",
                keywords=["legal AI", "contract automation", "legal research tools", "compliance tech"],
                sources=["legal_tech_news", "patents", "funding_news"],
                frequency="weekly",
                priority=2,
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Save if queries file doesn't exist
        if not self.queries_file.exists():
            self._save_queries(default_queries)
    
    def add_research_query(self, topic: str, query_type: str, keywords: List[str],
                          sources: List[str], frequency: str = "weekly", priority: int = 3) -> str:
        """Add new research query"""
        
        query_id = f"{query_type}_{hashlib.md5(topic.encode()).hexdigest()[:8]}"
        
        query = ResearchQuery(
            id=query_id,
            topic=topic,
            query_type=query_type,
            keywords=keywords,
            sources=sources,
            frequency=frequency,
            priority=priority,
            created_at=datetime.now().isoformat()
        )
        
        self.active_queries.append(query)
        self._save_queries(self.active_queries)
        
        return query_id
    
    def execute_research(self, query_id: str) -> ResearchResult:
        """Execute research for specific query"""
        
        query = next((q for q in self.active_queries if q.id == query_id), None)
        if not query:
            raise ValueError(f"Query {query_id} not found")
        
        start_time = time.time()
        
        # Execute research (placeholder - real implementation would use web search, APIs, etc.)
        findings = self._conduct_research(query)
        
        # Generate insights from findings
        insights = self._generate_insights(findings, query)
        
        # Extract actionable items
        actionable_items = self._extract_actionable_items(findings, insights, query)
        
        processing_time = (time.time() - start_time) * 1000
        
        result = ResearchResult(
            query_id=query_id,
            timestamp=datetime.now().isoformat(),
            findings=findings,
            insights=insights,
            actionable_items=actionable_items,
            confidence_score=self._calculate_confidence(findings),
            sources_used=query.sources,
            processing_time_ms=processing_time
        )
        
        # Save result
        self._save_result(result)
        
        # Update query last_run
        query.last_run = datetime.now().isoformat()
        query.next_run = self._calculate_next_run(query).isoformat()
        self._save_queries(self.active_queries)
        
        return result
    
    def _conduct_research(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Conduct actual research (placeholder implementation)"""
        
        # In real implementation, this would:
        # 1. Search web for keywords across specified sources
        # 2. Parse and extract relevant information
        # 3. Score relevance and importance
        # 4. Return structured findings
        
        # Placeholder findings based on query type
        if query.query_type == "trend":
            return [
                {
                    "title": "Claude 4 Surpasses GPT-5 in Reasoning Benchmarks",
                    "source": "techcrunch",
                    "url": "https://example.com/claude4-benchmark",
                    "summary": "Anthropic's Claude 4 shows 23% improvement in complex reasoning tasks",
                    "relevance_score": 0.9,
                    "publication_date": "2026-03-23",
                    "key_points": [
                        "23% improvement in reasoning benchmarks",
                        "Better performance on mathematical proofs",
                        "Enhanced code generation capabilities"
                    ]
                },
                {
                    "title": "$2.1B Funding Round for AI Infrastructure Startup",
                    "source": "crunchbase",
                    "url": "https://example.com/ai-funding",
                    "summary": "Scale AI raises largest Series E in AI infrastructure history",
                    "relevance_score": 0.8,
                    "publication_date": "2026-03-24",
                    "key_points": [
                        "$2.1B Series E funding",
                        "Focus on enterprise AI deployment",
                        "Valuation reaches $15.2B"
                    ]
                }
            ]
        
        elif query.query_type == "opportunity":
            return [
                {
                    "title": "Israeli AI Startup Raises $45M Series A",
                    "source": "techaviv",
                    "url": "https://example.com/israeli-ai-startup",
                    "summary": "Jerusalem-based AI company focusing on legal document analysis",
                    "relevance_score": 0.85,
                    "publication_date": "2026-03-23",
                    "key_points": [
                        "$45M Series A led by Insight Partners",
                        "Legal AI document analysis",
                        "Already serving 50+ law firms"
                    ],
                    "opportunity_type": "investment_target",
                    "risk_level": "medium"
                }
            ]
        
        elif query.query_type == "market":
            return [
                {
                    "title": "Linear Motors Market Expected to Grow 12% Annually",
                    "source": "industry_reports",
                    "url": "https://example.com/linear-motors-report",
                    "summary": "Global linear motors market driven by automation demand",
                    "relevance_score": 0.7,
                    "publication_date": "2026-03-20",
                    "key_points": [
                        "CAGR of 12% through 2030",
                        "Automotive and electronics driving growth",
                        "Asia-Pacific largest market"
                    ],
                    "market_size": "$2.1B by 2030",
                    "growth_drivers": ["Industrial automation", "Electric vehicles", "Robotics"]
                }
            ]
        
        else:
            return []
    
    def _generate_insights(self, findings: List[Dict[str, Any]], query: ResearchQuery) -> List[str]:
        """Generate insights from research findings"""
        
        insights = []
        
        if query.query_type == "trend" and findings:
            # AI trend insights
            if any("Claude" in str(finding) for finding in findings):
                insights.append("Anthropic is gaining competitive advantage with Claude 4 - consider implications for AI investment strategy")
            
            if any("funding" in str(finding).lower() for finding in findings):
                insights.append("AI funding remains strong despite market conditions - infrastructure layer attracting largest investments")
        
        elif query.query_type == "opportunity" and findings:
            # Investment opportunity insights
            high_relevance = [f for f in findings if f.get("relevance_score", 0) > 0.8]
            if high_relevance:
                insights.append(f"Found {len(high_relevance)} high-relevance investment opportunities in target sectors")
            
            legal_ai = [f for f in findings if "legal" in str(f).lower() and "ai" in str(f).lower()]
            if legal_ai:
                insights.append("Legal AI sector showing strong funding activity - potential synergy with existing legal domain expertise")
        
        elif query.query_type == "market" and findings:
            # Market analysis insights
            growth_data = [f for f in findings if "growth" in str(f).lower() or "CAGR" in str(f)]
            if growth_data:
                insights.append("Linear motors market showing strong growth trajectory - opportunity for market entry or expansion")
        
        # Generic insights
        if len(findings) > 3:
            insights.append(f"High activity in {query.topic} - {len(findings)} significant developments identified")
        
        return insights
    
    def _extract_actionable_items(self, findings: List[Dict[str, Any]], 
                                 insights: List[str], query: ResearchQuery) -> List[Dict[str, Any]]:
        """Extract actionable items from findings and insights"""
        
        actionable_items = []
        
        # Investment-related actions
        investment_findings = [f for f in findings if "funding" in str(f).lower() or "investment" in str(f).lower()]
        for finding in investment_findings:
            actionable_items.append({
                "type": "investigation",
                "priority": "medium",
                "action": f"Research company mentioned: {finding.get('title', 'Unknown')}",
                "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
                "context": finding.get("summary", ""),
                "source": finding.get("url", "")
            })
        
        # Market opportunity actions  
        if query.query_type == "opportunity":
            high_relevance = [f for f in findings if f.get("relevance_score", 0) > 0.8]
            for finding in high_relevance:
                actionable_items.append({
                    "type": "due_diligence",
                    "priority": "high",
                    "action": f"Deep dive analysis on {finding.get('title', 'opportunity')}",
                    "deadline": (datetime.now() + timedelta(days=3)).isoformat(),
                    "expected_outcome": "Investment thesis document",
                    "context": finding
                })
        
        # Technology trend actions
        if query.query_type == "trend":
            significant_trends = [f for f in findings if f.get("relevance_score", 0) > 0.85]
            for finding in significant_trends:
                actionable_items.append({
                    "type": "strategic_planning",
                    "priority": "medium",
                    "action": f"Assess impact of trend: {finding.get('title', 'trend')}",
                    "deadline": (datetime.now() + timedelta(days=14)).isoformat(),
                    "questions": [
                        "How does this affect current portfolio?",
                        "Are there investment implications?",
                        "Should we adjust strategy?"
                    ]
                })
        
        return actionable_items
    
    def _calculate_confidence(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for research results"""
        
        if not findings:
            return 0.0
        
        # Base confidence on source quality and relevance scores
        total_relevance = sum(f.get("relevance_score", 0.5) for f in findings)
        avg_relevance = total_relevance / len(findings)
        
        # Adjust for number of sources
        source_diversity = len(set(f.get("source", "unknown") for f in findings))
        diversity_bonus = min(source_diversity * 0.1, 0.3)
        
        # Adjust for recency
        recent_findings = sum(1 for f in findings 
                            if f.get("publication_date", "2020-01-01") >= "2026-03-20")
        recency_bonus = min(recent_findings * 0.05, 0.2)
        
        confidence = min(avg_relevance + diversity_bonus + recency_bonus, 1.0)
        return round(confidence, 2)
    
    def _calculate_next_run(self, query: ResearchQuery) -> datetime:
        """Calculate next run time for query based on frequency"""
        
        now = datetime.now()
        
        if query.frequency == "daily":
            return now + timedelta(days=1)
        elif query.frequency == "weekly":
            return now + timedelta(weeks=1)
        elif query.frequency == "monthly":
            return now + timedelta(days=30)
        else:  # one-time
            return now + timedelta(years=1)  # Far in the future
    
    def get_pending_queries(self) -> List[ResearchQuery]:
        """Get queries that are due to run"""
        
        now = datetime.now()
        pending = []
        
        for query in self.active_queries:
            if not query.active:
                continue
                
            if query.next_run is None or datetime.fromisoformat(query.next_run) <= now:
                pending.append(query)
        
        # Sort by priority (higher first)
        return sorted(pending, key=lambda q: q.priority, reverse=True)
    
    def process_pending_research(self, max_queries: int = 3) -> List[ResearchResult]:
        """Process pending research queries"""
        
        pending = self.get_pending_queries()
        results = []
        
        for query in pending[:max_queries]:
            try:
                result = self.execute_research(query.id)
                results.append(result)
            except Exception as e:
                print(f"Error processing query {query.id}: {e}")
                continue
        
        return results
    
    def generate_daily_briefing(self) -> Dict[str, Any]:
        """Generate daily research briefing"""
        
        # Get recent results (last 24 hours)
        recent_results = self._get_recent_results(hours=24)
        
        # Aggregate insights and actionable items
        all_insights = []
        all_actionable = []
        
        for result in recent_results:
            all_insights.extend(result.insights)
            all_actionable.extend(result.actionable_items)
        
        # Prioritize actionable items
        high_priority_actions = [a for a in all_actionable if a.get("priority") == "high"]
        medium_priority_actions = [a for a in all_actionable if a.get("priority") == "medium"]
        
        briefing = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": {
                "research_queries_processed": len(recent_results),
                "key_insights_found": len(all_insights),
                "actionable_items_identified": len(all_actionable),
                "high_priority_actions": len(high_priority_actions)
            },
            "key_insights": all_insights[:5],  # Top 5 insights
            "urgent_actions": high_priority_actions[:3],  # Top 3 urgent actions
            "important_actions": medium_priority_actions[:5],  # Top 5 important actions
            "research_areas_covered": list(set(r.query_id.split('_')[0] for r in recent_results))
        }
        
        return briefing
    
    def _get_recent_results(self, hours: int = 24) -> List[ResearchResult]:
        """Get research results from last N hours"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_results = []
        
        # Load results from files
        for result_file in self.results_dir.glob("*.json"):
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    result_time = datetime.fromisoformat(data["timestamp"])
                    if result_time >= cutoff_time:
                        recent_results.append(ResearchResult(**data))
            except:
                continue
        
        return recent_results
    
    def _load_queries(self) -> List[ResearchQuery]:
        """Load active queries from file"""
        
        if not self.queries_file.exists():
            return []
        
        try:
            with open(self.queries_file, 'r') as f:
                data = json.load(f)
                return [ResearchQuery(**q) for q in data]
        except:
            return []
    
    def _save_queries(self, queries: List[ResearchQuery]):
        """Save queries to file"""
        
        try:
            with open(self.queries_file, 'w') as f:
                json.dump([asdict(q) for q in queries], f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def _save_result(self, result: ResearchResult):
        """Save research result to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result.query_id}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def get_research_status(self) -> Dict[str, Any]:
        """Get research engine status"""
        
        total_queries = len(self.active_queries)
        active_queries = len([q for q in self.active_queries if q.active])
        pending_queries = len(self.get_pending_queries())
        
        recent_results = self._get_recent_results(hours=168)  # Last week
        
        return {
            "total_queries": total_queries,
            "active_queries": active_queries, 
            "pending_queries": pending_queries,
            "results_last_week": len(recent_results),
            "research_areas": list(set(q.query_type for q in self.active_queries)),
            "next_scheduled_runs": [
                {
                    "query_id": q.id,
                    "topic": q.topic,
                    "next_run": q.next_run,
                    "priority": q.priority
                }
                for q in sorted(self.active_queries, key=lambda x: x.next_run or "9999-12-31")[:5]
            ]
        }

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  research_engine.py status")
        print("  research_engine.py add-query '<topic>' <type> '<keywords_csv>' '<sources_csv>' [frequency] [priority]")
        print("  research_engine.py run <query_id>")
        print("  research_engine.py process-pending [max_count]")
        print("  research_engine.py daily-briefing")
        print("  research_engine.py list-queries")
        return
    
    engine = TzofitResearchEngine()
    command = sys.argv[1]
    
    if command == "status":
        status = engine.get_research_status()
        print("🔬 Research Engine Status:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif command == "add-query" and len(sys.argv) >= 6:
        topic = sys.argv[2]
        query_type = sys.argv[3]
        keywords = sys.argv[4].split(',')
        sources = sys.argv[5].split(',')
        frequency = sys.argv[6] if len(sys.argv) > 6 else "weekly"
        priority = int(sys.argv[7]) if len(sys.argv) > 7 else 3
        
        query_id = engine.add_research_query(topic, query_type, keywords, sources, frequency, priority)
        print(f"✅ Added research query: {query_id}")
    
    elif command == "run" and len(sys.argv) >= 3:
        query_id = sys.argv[2]
        
        try:
            result = engine.execute_research(query_id)
            print(f"🔍 Research completed for {query_id}:")
            print(f"   Findings: {len(result.findings)}")
            print(f"   Insights: {len(result.insights)}")
            print(f"   Actionable items: {len(result.actionable_items)}")
            print(f"   Confidence: {result.confidence_score}")
            print(f"   Processing time: {result.processing_time_ms:.1f}ms")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "process-pending":
        max_count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        
        results = engine.process_pending_research(max_count)
        print(f"🔄 Processed {len(results)} pending research queries:")
        
        for result in results:
            print(f"  📊 {result.query_id}: {len(result.findings)} findings, {len(result.insights)} insights")
    
    elif command == "daily-briefing":
        briefing = engine.generate_daily_briefing()
        
        print(f"📋 Daily Research Briefing — {briefing['date']}")
        print("=" * 50)
        
        summary = briefing['summary']
        print(f"📊 Research queries processed: {summary['research_queries_processed']}")
        print(f"💡 Key insights found: {summary['key_insights_found']}")
        print(f"🎯 Actionable items: {summary['actionable_items_identified']}")
        print(f"🔴 High priority actions: {summary['high_priority_actions']}")
        print()
        
        if briefing['key_insights']:
            print("💡 Key Insights:")
            for i, insight in enumerate(briefing['key_insights'], 1):
                print(f"  {i}. {insight}")
            print()
        
        if briefing['urgent_actions']:
            print("🔴 Urgent Actions:")
            for i, action in enumerate(briefing['urgent_actions'], 1):
                print(f"  {i}. {action['action']}")
            print()
    
    elif command == "list-queries":
        print("📋 Active Research Queries:")
        for query in engine.active_queries:
            status = "🟢" if query.active else "🔴"
            print(f"  {status} {query.id} ({query.query_type})")
            print(f"      Topic: {query.topic}")
            print(f"      Frequency: {query.frequency}, Priority: {query.priority}")
            print(f"      Next run: {query.next_run}")
            print()
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()