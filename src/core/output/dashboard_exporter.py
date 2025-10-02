"""
Dashboard Exporter

Dashboard-ready JSON export with metrics aggregation.
Generates structured data optimized for dashboard consumption.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Metrics formatted for dashboard display."""
    agent_name: str
    total_findings: int
    critical_findings: int
    warning_findings: int
    info_findings: int
    complexity_score: float
    quality_score: float
    trends: Dict[str, Any]
    timestamp: str


@dataclass
class DashboardData:
    """Complete dashboard data structure."""
    summary: Dict[str, Any]
    agent_metrics: List[DashboardMetrics]
    findings_by_category: Dict[str, int]
    trends: Dict[str, List[float]]
    generated_at: str


class DashboardExporter:
    """Exports analysis results in dashboard-ready format."""
    
    def __init__(self, output_dir: str = "outputs/consolidated"):
        """Initialize the dashboard exporter."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def export_dashboard_data(self, agent_results: Dict[str, Dict[str, Any]]) -> str:
        """Export comprehensive dashboard data."""
        try:
            dashboard_data = self._build_dashboard_data(agent_results)
            output_file = self.output_dir / f"metrics_dashboard_{self._get_timestamp()}.json"
            
            with open(output_file, 'w') as f:
                json.dump(dashboard_data.__dict__, f, indent=2, default=str)
                
            logger.info(f"Exported dashboard data: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to export dashboard data: {e}")
            raise
    
    def export_executive_summary(self, agent_results: Dict[str, Dict[str, Any]]) -> str:
        """Export executive summary for high-level dashboard."""
        try:
            summary = self._build_executive_summary(agent_results)
            output_file = self.output_dir / f"executive_summary_{self._get_timestamp()}.json"
            
            with open(output_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
            logger.info(f"Exported executive summary: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to export executive summary: {e}")
            raise
    
    def export_trends_analysis(self, historical_data: List[Dict[str, Any]]) -> str:
        """Export trends analysis for time-series visualization."""
        try:
            trends = self._analyze_trends(historical_data)
            output_file = self.output_dir / f"trends_analysis_{self._get_timestamp()}.json"
            
            with open(output_file, 'w') as f:
                json.dump(trends, f, indent=2)
                
            logger.info(f"Exported trends analysis: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to export trends analysis: {e}")
            raise
    
    def _build_dashboard_data(self, agent_results: Dict[str, Dict[str, Any]]) -> DashboardData:
        """Build comprehensive dashboard data structure."""
        agent_metrics = []
        total_findings = 0
        findings_by_category = {}
        
        for agent_name, results in agent_results.items():
            metrics = self._extract_agent_metrics(agent_name, results)
            agent_metrics.append(metrics)
            total_findings += metrics.total_findings
            
            # Aggregate findings by category
            for category in ["critical", "warning", "info"]:
                count = getattr(metrics, f"{category}_findings")
                findings_by_category[category] = findings_by_category.get(category, 0) + count
        
        summary = {
            "total_agents": len(agent_results),
            "total_findings": total_findings,
            "average_quality_score": self._calculate_average_quality(agent_metrics),
            "average_complexity_score": self._calculate_average_complexity(agent_metrics),
            "analysis_coverage": self._calculate_coverage(agent_results)
        }
        
        trends = self._extract_trends(agent_results)
        
        return DashboardData(
            summary=summary,
            agent_metrics=agent_metrics,
            findings_by_category=findings_by_category,
            trends=trends,
            generated_at=self._get_timestamp()
        )
    
    def _extract_agent_metrics(self, agent_name: str, results: Dict[str, Any]) -> DashboardMetrics:
        """Extract metrics for a specific agent."""
        findings = results.get("findings", [])
        
        # Count findings by severity
        critical_count = len([f for f in findings if f.get("severity") == "critical"])
        warning_count = len([f for f in findings if f.get("severity") == "warning"])
        info_count = len([f for f in findings if f.get("severity") == "info"])
        
        # Calculate scores (placeholder logic)
        complexity_score = results.get("complexity_score", 0.0)
        quality_score = results.get("quality_score", 0.0)
        
        # Extract trends
        trends = results.get("trends", {})
        
        return DashboardMetrics(
            agent_name=agent_name,
            total_findings=len(findings),
            critical_findings=critical_count,
            warning_findings=warning_count,
            info_findings=info_count,
            complexity_score=complexity_score,
            quality_score=quality_score,
            trends=trends,
            timestamp=self._get_timestamp()
        )
    
    def _build_executive_summary(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Build executive summary for high-level overview."""
        total_findings = sum(len(results.get("findings", [])) for results in agent_results.values())
        critical_issues = sum(
            len([f for f in results.get("findings", []) if f.get("severity") == "critical"])
            for results in agent_results.values()
        )
        
        # Calculate overall health score
        health_score = max(0, 100 - (critical_issues * 10) - (total_findings * 2))
        
        return {
            "health_score": health_score,
            "total_findings": total_findings,
            "critical_issues": critical_issues,
            "agents_analyzed": list(agent_results.keys()),
            "recommendations": self._generate_recommendations(agent_results),
            "generated_at": self._get_timestamp()
        }
    
    def _analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends from historical data."""
        if not historical_data:
            return {"trends": [], "insights": []}
        
        # TODO: Implement actual trend analysis
        return {
            "trends": {
                "quality_improvement": True,
                "complexity_trend": "stable",
                "finding_count_trend": "decreasing"
            },
            "insights": [
                "Code quality has improved over the last 3 analyses",
                "Security findings have decreased by 15%",
                "Performance optimizations are showing positive results"
            ],
            "data_points": len(historical_data)
        }
    
    def _calculate_average_quality(self, metrics: List[DashboardMetrics]) -> float:
        """Calculate average quality score across agents."""
        if not metrics:
            return 0.0
        return sum(m.quality_score for m in metrics) / len(metrics)
    
    def _calculate_average_complexity(self, metrics: List[DashboardMetrics]) -> float:
        """Calculate average complexity score across agents."""
        if not metrics:
            return 0.0
        return sum(m.complexity_score for m in metrics) / len(metrics)
    
    def _calculate_coverage(self, agent_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate analysis coverage percentage."""
        # TODO: Implement actual coverage calculation
        return 85.0  # Placeholder
    
    def _extract_trends(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, List[float]]:
        """Extract trend data for visualization."""
        # TODO: Implement trend extraction from historical data
        return {
            "quality_scores": [75.0, 78.0, 82.0, 85.0],
            "finding_counts": [45, 38, 32, 28],
            "complexity_scores": [6.2, 5.8, 5.5, 5.2]
        }
    
    def _generate_recommendations(self, agent_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate high-level recommendations."""
        recommendations = []
        
        # Analyze results and generate recommendations
        for agent_name, results in agent_results.items():
            findings = results.get("findings", [])
            critical_findings = [f for f in findings if f.get("severity") == "critical"]
            
            if critical_findings:
                recommendations.append(f"Address {len(critical_findings)} critical issues found by {agent_name}")
        
        if not recommendations:
            recommendations.append("Continue current development practices - no critical issues found")
            
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


# Global dashboard exporter instance
dashboard_exporter = DashboardExporter()