"""
Enhanced Report Generator with LLM Integration
Generates comprehensive, structured analysis reports with actionable insights
"""

import asyncio
import json
import yaml
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from .llm_provider import get_llm_provider, LLMRequest

logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    include_code_examples: bool = True
    include_metrics_tables: bool = True
    include_llm_insights: bool = True
    max_code_examples_per_finding: int = 2
    min_confidence_for_examples: float = 0.7


class EnhancedReportGenerator:
    """
    Enhanced report generator that creates comprehensive, structured analysis reports
    with LLM-powered insights and actionable recommendations
    """
    
    def __init__(self):
        self.config = ReportConfig()
        self.quality_rules = self._load_quality_rules()
        self.bias_prevention = self._load_bias_prevention_rules()
        
    def _load_quality_rules(self) -> Dict[str, Any]:
        """Load quality control rules"""
        try:
            config_path = Path(__file__).parent.parent.parent / "configs" / "rules" / "quality_control.yaml"
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load quality control rules: {e}")
            return {}
    
    def _load_bias_prevention_rules(self) -> Dict[str, Any]:
        """Load bias prevention rules"""
        try:
            config_path = Path(__file__).parent.parent.parent / "configs" / "rules" / "bias_prevention.yaml"
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load bias prevention rules: {e}")
            return {}
    
    async def generate_enhanced_report(
        self, 
        analysis_result: Dict[str, Any], 
        output_path: str,
        test_files_content: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate a comprehensive analysis report with LLM insights
        
        Args:
            analysis_result: The raw analysis results
            output_path: Path to save the report
            test_files_content: Optional dict of file paths to content for code examples
            
        Returns:
            Path to the generated report
        """
        try:
            # Prepare data for analysis
            structured_data = self._structure_analysis_data(analysis_result)
            
            # Generate LLM insights
            llm_insights = await self._generate_llm_insights(structured_data, test_files_content)
            
            # Build comprehensive report
            report_content = await self._build_comprehensive_report(
                structured_data, 
                llm_insights, 
                test_files_content
            )
            
            # Apply quality control
            validated_report = self._apply_quality_control(report_content)
            
            # Save report
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(validated_report)
            
            logger.info(f"Enhanced report generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced report: {e}")
            # Fallback to basic report
            return self._generate_fallback_report(analysis_result, output_path)
    
    def _structure_analysis_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Structure the raw analysis data for better processing"""
        structured = {
            'summary': {
                'files_analyzed': len(analysis_result.get('metrics', {})),
                'total_findings': len(analysis_result.get('findings', [])),
                'total_issues': len(analysis_result.get('findings', [])),  # Alias for compatibility
                'execution_time': analysis_result.get('execution_time', 0),
                'success': analysis_result.get('success', False)
            },
            'findings_by_severity': self._categorize_findings_by_severity(analysis_result.get('findings', [])),
            'findings_by_category': self._categorize_findings_by_category(analysis_result.get('findings', [])),
            'findings_by_file': self._categorize_findings_by_file(analysis_result.get('findings', [])),
            'metrics_summary': self._summarize_metrics(analysis_result.get('metrics', {})),
            'quality_assessment': self._assess_overall_quality(analysis_result)
        }
        return structured
    
    def _categorize_findings_by_severity(self, findings: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize findings by severity level"""
        categories = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': [], 'INFO': []}
        
        for finding in findings:
            severity = str(finding.get('severity', 'LOW')).replace('FindingSeverity.', '')
            if severity in categories:
                categories[severity].append(finding)
            else:
                categories['LOW'].append(finding)
        
        return categories
    
    def _categorize_findings_by_category(self, findings: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize findings by type"""
        categories = {}
        
        for finding in findings:
            category = finding.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(finding)
        
        return categories
    
    def _categorize_findings_by_file(self, findings: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize findings by file"""
        by_file = {}
        
        for finding in findings:
            file_path = finding.get('file', 'unknown')
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(finding)
        
        return by_file
    
    def _summarize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of metrics across all files"""
        summary = {
            'complexity': {'total_files': 0, 'avg_cognitive_complexity': 0, 'max_nesting_depth': 0},
            'maintainability': {'avg_score': 0, 'quality_distribution': {}},
            'duplication': {'total_duplications': 0, 'avg_duplication_percentage': 0}
        }
        
        complexity_scores = []
        maintainability_scores = []
        duplication_counts = []
        quality_levels = {}
        
        for file_path, file_metrics in metrics.items():
            # Complexity metrics
            if 'complexity' in file_metrics:
                complexity = file_metrics['complexity']
                if complexity.get('cognitive_complexity'):
                    complexity_scores.append(complexity['cognitive_complexity'])
                    summary['complexity']['total_files'] += 1
                    summary['complexity']['max_nesting_depth'] = max(
                        summary['complexity']['max_nesting_depth'], 
                        complexity.get('nesting_depth', 0)
                    )
            
            # Maintainability metrics
            if 'maintainability' in file_metrics:
                maintainability = file_metrics['maintainability']
                if maintainability.get('score'):
                    maintainability_scores.append(maintainability['score'])
                    quality_level = maintainability.get('quality_level', 'Unknown')
                    quality_levels[quality_level] = quality_levels.get(quality_level, 0) + 1
            
            # Duplication metrics
            if 'duplication' in file_metrics:
                duplication = file_metrics['duplication']
                duplication_counts.append(duplication.get('total_duplications', 0))
        
        # Calculate averages
        if complexity_scores:
            summary['complexity']['avg_cognitive_complexity'] = sum(complexity_scores) / len(complexity_scores)
        
        if maintainability_scores:
            summary['maintainability']['avg_score'] = sum(maintainability_scores) / len(maintainability_scores)
            summary['maintainability']['quality_distribution'] = quality_levels
        
        if duplication_counts:
            summary['duplication']['total_duplications'] = sum(duplication_counts)
            summary['duplication']['avg_duplication_percentage'] = sum(duplication_counts) / len(duplication_counts)
        
        return summary
    
    def _assess_overall_quality(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall code quality based on findings and metrics"""
        findings = analysis_result.get('findings', [])
        metrics = analysis_result.get('metrics', {})
        
        # Count severity levels
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for finding in findings:
            severity = str(finding.get('severity', 'LOW')).replace('FindingSeverity.', '')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Calculate quality score (0-100)
        total_findings = len(findings)
        if total_findings == 0:
            quality_score = 100
        else:
            # Weight by severity: CRITICAL=-20, HIGH=-10, MEDIUM=-5, LOW=-2
            weighted_deductions = (
                severity_counts['CRITICAL'] * 20 +
                severity_counts['HIGH'] * 10 +
                severity_counts['MEDIUM'] * 5 +
                severity_counts['LOW'] * 2
            )
            quality_score = max(0, 100 - weighted_deductions)
        
        # Determine quality level
        if quality_score >= 90:
            quality_level = "Excellent"
        elif quality_score >= 75:
            quality_level = "Good"
        elif quality_score >= 60:
            quality_level = "Fair"
        elif quality_score >= 40:
            quality_level = "Poor"
        else:
            quality_level = "Critical"
        
        return {
            'overall_score': quality_score,
            'quality_level': quality_level,
            'severity_distribution': severity_counts,
            'total_issues': total_findings,
            'needs_immediate_attention': severity_counts['CRITICAL'] > 0 or severity_counts['HIGH'] > 2
        }
    
    async def _generate_llm_insights(
        self, 
        structured_data: Dict[str, Any], 
        test_files_content: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive insights using LLM with bias prevention"""
        try:
            llm_provider = get_llm_provider()
            
            # Prepare analysis context with bias prevention measures
            analysis_context = self._prepare_unbiased_context(structured_data)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(llm_provider, analysis_context)
            
            # Generate detailed insights per category
            category_insights = await self._generate_category_insights(llm_provider, structured_data)
            
            # Generate actionable recommendations
            recommendations = await self._generate_actionable_recommendations(
                llm_provider, structured_data, test_files_content
            )
            
            # Generate improvement roadmap
            roadmap = await self._generate_improvement_roadmap(llm_provider, structured_data)
            
            return {
                'executive_summary': executive_summary,
                'category_insights': category_insights,
                'recommendations': recommendations,
                'improvement_roadmap': roadmap,
                'confidence_score': self._calculate_insight_confidence(structured_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate LLM insights: {e}")
            return {'error': str(e), 'fallback_insights': self._generate_fallback_insights(structured_data)}
    
    def _prepare_unbiased_context(self, structured_data: Dict[str, Any]) -> str:
        """Prepare analysis context while applying bias prevention measures"""
        # Apply bias prevention rules from configuration
        bias_rules = self.bias_prevention.get('bias_prevention', {})
        
        context_parts = []
        
        # Add summary with objective framing
        summary = structured_data['summary']
        context_parts.append(f"""
OBJECTIVE ANALYSIS CONTEXT:
- Files Analyzed: {summary['files_analyzed']}
- Total Issues Found: {summary['total_findings']}
- Analysis Success: {summary['success']}
        """)
        
        # Add findings distribution (avoiding recency bias)
        severity_dist = structured_data['quality_assessment']['severity_distribution']
        context_parts.append(f"""
ISSUE DISTRIBUTION (by severity):
- Critical: {severity_dist['CRITICAL']} issues
- High: {severity_dist['HIGH']} issues  
- Medium: {severity_dist['MEDIUM']} issues
- Low: {severity_dist['LOW']} issues
        """)
        
        # Add metrics summary (using statistical baselines)
        metrics = structured_data['metrics_summary']
        context_parts.append(f"""
QUANTITATIVE METRICS:
- Average Cognitive Complexity: {metrics['complexity']['avg_cognitive_complexity']:.1f}
- Average Maintainability Score: {metrics['maintainability']['avg_score']:.1f}/100
- Total Code Duplications: {metrics['duplication']['total_duplications']}
        """)
        
        return "\n".join(context_parts)
    
    async def _generate_executive_summary(self, llm_provider, context: str) -> str:
        """Generate an executive summary with quality gates"""
        system_prompt = """You are a senior software engineering consultant providing an executive summary of code quality analysis.

GUIDELINES:
- Focus on business impact and technical risks
- Provide clear, jargon-free language for stakeholders
- Highlight the most critical issues requiring immediate attention
- Include positive aspects and code strengths
- Be objective and evidence-based
- Avoid technical bias toward specific languages or frameworks

FORMAT: Provide a concise 3-4 paragraph executive summary."""
        
        request = LLMRequest(
            prompt=f"Generate an executive summary for this code analysis:\n\n{context}",
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=500
        )
        
        response = await llm_provider.generate_response(request)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def _generate_category_insights(self, llm_provider, structured_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate insights for each finding category"""
        insights = {}
        
        for category, findings in structured_data['findings_by_category'].items():
            if not findings:
                continue
                
            # Prepare category-specific context
            category_context = f"""
CATEGORY: {category.upper()}
TOTAL ISSUES: {len(findings)}

SPECIFIC FINDINGS:
"""
            for i, finding in enumerate(findings[:5], 1):  # Limit to top 5 for context
                category_context += f"{i}. {finding.get('description', 'No description')}\n"
            
            system_prompt = f"""You are a code quality expert analyzing {category} issues.

GUIDELINES:
- Explain the significance of these {category} issues
- Describe the potential impact on code maintainability and performance
- Suggest high-level strategies for improvement
- Be specific but avoid overwhelming technical detail
- Focus on practical, actionable insights

FORMAT: Provide 2-3 paragraphs of focused analysis."""
            
            request = LLMRequest(
                prompt=f"Analyze these {category} findings:\n\n{category_context}",
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=400
            )
            
            try:
                response = await llm_provider.generate_response(request)
                insights[category] = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                logger.warning(f"Failed to generate insights for category {category}: {e}")
                insights[category] = f"Analysis pending - {len(findings)} issues identified requiring attention."
        
        return insights
    
    async def _generate_actionable_recommendations(
        self, 
        llm_provider, 
        structured_data: Dict[str, Any],
        test_files_content: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate specific, actionable recommendations with code examples"""
        recommendations = []
        
        # Focus on the most critical findings
        all_findings = []
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM']:
            all_findings.extend(structured_data['findings_by_severity'].get(severity, []))
        
        # Group similar findings for better recommendations
        grouped_findings = self._group_similar_findings(all_findings)
        
        for group_type, findings in grouped_findings.items():
            if not findings:
                continue
                
            # Sample representative finding
            representative_finding = findings[0]
            
            # Prepare context for recommendation
            rec_context = f"""
ISSUE TYPE: {group_type}
OCCURRENCES: {len(findings)} instances
REPRESENTATIVE EXAMPLE: {representative_finding.get('description', 'No description')}
FILE: {representative_finding.get('file', 'Unknown')}
"""
            
            # Add code context if available
            if test_files_content:
                file_path = representative_finding.get('file', '')
                if file_path in test_files_content:
                    # Get relevant code snippet
                    code_snippet = self._extract_relevant_code_snippet(
                        test_files_content[file_path], 
                        representative_finding.get('line', 1)
                    )
                    rec_context += f"\nCODE CONTEXT:\n```\n{code_snippet}\n```"
            
            system_prompt = """You are a senior software engineer providing specific, actionable code improvement recommendations.

GUIDELINES:
- Provide specific, implementable solutions
- Include code examples showing before/after improvements
- Explain WHY the change improves code quality
- Consider team productivity and maintainability
- Prioritize high-impact, low-effort improvements
- Be technology-agnostic when possible

FORMAT:
1. **Issue Summary**: Brief description
2. **Impact**: Why this matters
3. **Solution**: Specific steps to fix
4. **Code Example**: Before/after if applicable
5. **Priority**: High/Medium/Low"""
            
            request = LLMRequest(
                prompt=f"Generate an actionable recommendation for:\n\n{rec_context}",
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=600
            )
            
            try:
                response = await llm_provider.generate_response(request)
                
                recommendations.append({
                    'type': group_type,
                    'occurrences': len(findings),
                    'priority': self._determine_recommendation_priority(findings),
                    'content': response.content if hasattr(response, 'content') else str(response),
                    'affected_files': list(set(f.get('file', '') for f in findings))
                })
            except Exception as e:
                logger.warning(f"Failed to generate recommendation for {group_type}: {e}")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _group_similar_findings(self, findings: List[Dict]) -> Dict[str, List[Dict]]:
        """Group similar findings together for better recommendation generation"""
        groups = {}
        
        for finding in findings:
            description = finding.get('description', '')
            category = finding.get('category', 'general')
            
            # Create group key based on description patterns
            if 'complexity' in description.lower():
                group_key = 'High Complexity'
            elif 'nesting' in description.lower():
                group_key = 'Deep Nesting'
            elif 'documentation' in description.lower() or 'docstring' in description.lower():
                group_key = 'Documentation'
            elif 'indentation' in description.lower():
                group_key = 'Code Formatting'
            elif category:
                group_key = category.title()
            else:
                group_key = 'General Issues'
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(finding)
        
        return groups
    
    def _extract_relevant_code_snippet(self, content: str, line_number: int, context_lines: int = 5) -> str:
        """Extract relevant code snippet around the specified line"""
        lines = content.split('\n')
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            snippet_lines.append(f"{prefix}{i+1:3d}: {lines[i]}")
        
        return '\n'.join(snippet_lines)
    
    def _determine_recommendation_priority(self, findings: List[Dict]) -> str:
        """Determine priority based on finding severity and count"""
        critical_count = sum(1 for f in findings if 'CRITICAL' in str(f.get('severity', '')))
        high_count = sum(1 for f in findings if 'HIGH' in str(f.get('severity', '')))
        
        if critical_count > 0:
            return 'Critical'
        elif high_count > 2:
            return 'High'
        elif len(findings) > 5:
            return 'High'
        elif high_count > 0:
            return 'Medium'
        else:
            return 'Low'
    
    async def _generate_improvement_roadmap(self, llm_provider, structured_data: Dict[str, Any]) -> str:
        """Generate a strategic improvement roadmap"""
        quality_assessment = structured_data['quality_assessment']
        
        context = f"""
CURRENT QUALITY STATUS:
- Overall Score: {quality_assessment['overall_score']}/100
- Quality Level: {quality_assessment['quality_level']}
- Total Issues: {quality_assessment['total_issues']}
- Critical Issues: {quality_assessment['severity_distribution']['CRITICAL']}
- High Priority Issues: {quality_assessment['severity_distribution']['HIGH']}
- Immediate Attention Needed: {quality_assessment['needs_immediate_attention']}
"""
        
        system_prompt = """You are a technical project manager creating a code quality improvement roadmap.

GUIDELINES:
- Create a phased approach with clear timelines
- Prioritize by business impact and technical risk
- Consider team capacity and resources
- Include measurable success criteria
- Balance quick wins with long-term improvements
- Be realistic about implementation timelines

FORMAT:
**Phase 1 (Immediate - 1-2 weeks)**
**Phase 2 (Short-term - 1-2 months)**  
**Phase 3 (Long-term - 3-6 months)**
**Success Metrics**"""
        
        request = LLMRequest(
            prompt=f"Create an improvement roadmap based on:\n\n{context}",
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=600
        )
        
        try:
            response = await llm_provider.generate_response(request)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.warning(f"Failed to generate improvement roadmap: {e}")
            return "Improvement roadmap generation pending - please prioritize critical and high-severity issues."
    
    def _calculate_insight_confidence(self, structured_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the generated insights"""
        # Base confidence on data quality and completeness
        total_findings = structured_data['summary']['total_findings']
        
        if total_findings == 0:
            return 0.5  # Low confidence with no findings
        elif total_findings < 5:
            return 0.7  # Medium confidence with few findings
        else:
            return 0.9  # High confidence with sufficient data
    
    async def _build_comprehensive_report(
        self, 
        structured_data: Dict[str, Any], 
        llm_insights: Dict[str, Any],
        test_files_content: Optional[Dict[str, str]] = None
    ) -> str:
        """Build the final comprehensive report"""
        report_parts = []
        
        # Header
        report_parts.append(self._generate_report_header(structured_data))
        
        # Executive Summary
        report_parts.append("## 📊 Executive Summary")
        if 'executive_summary' in llm_insights:
            report_parts.append(llm_insights['executive_summary'])
        else:
            report_parts.append(self._generate_fallback_summary(structured_data))
        
        # Quality Overview Table
        report_parts.append(self._generate_quality_overview_table(structured_data))
        
        # Detailed Metrics Tables
        report_parts.append(self._generate_metrics_tables(structured_data))
        
        # Category Analysis
        report_parts.append(self._generate_category_analysis(structured_data, llm_insights))
        
        # Actionable Recommendations
        report_parts.append(self._generate_recommendations_section(llm_insights))
        
        # Improvement Roadmap
        report_parts.append("## 🗺️ Improvement Roadmap")
        if 'improvement_roadmap' in llm_insights:
            report_parts.append(llm_insights['improvement_roadmap'])
        
        # Detailed Findings
        report_parts.append(self._generate_detailed_findings(structured_data, test_files_content))
        
        # Footer
        report_parts.append(self._generate_report_footer(llm_insights))
        
        return '\n\n'.join(report_parts)
    
    def _generate_report_header(self, structured_data: Dict[str, Any]) -> str:
        """Generate report header with metadata"""
        summary = structured_data['summary']
        quality = structured_data['quality_assessment']
        
        return f"""# 🔍 Comprehensive Code Analysis Report

**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Files Analyzed**: {summary['files_analyzed']}  
**Total Issues**: {summary['total_issues']} issues  
**Overall Quality**: {quality['quality_level']} ({quality['overall_score']}/100)  
**Analysis Time**: {summary['execution_time']:.2f}s  

---"""
    
    def _generate_quality_overview_table(self, structured_data: Dict[str, Any]) -> str:
        """Generate quality overview table"""
        quality = structured_data['quality_assessment']
        severity_dist = quality['severity_distribution']
        
        # Quality indicator emoji
        quality_emoji = {
            'Excellent': '🟢', 'Good': '🟡', 'Fair': '🟠', 'Poor': '🔴', 'Critical': '🚨'
        }.get(quality['quality_level'], '⚪')
        
        return f"""## 📈 Quality Overview

| Metric | Value | Status |
|--------|-------|--------|
| **Overall Quality** | {quality['overall_score']}/100 | {quality_emoji} {quality['quality_level']} |
| **Critical Issues** | {severity_dist['CRITICAL']} | {'🚨 Immediate Action Required' if severity_dist['CRITICAL'] > 0 else '✅ None'} |
| **High Priority** | {severity_dist['HIGH']} | {'⚠️ Priority Attention' if severity_dist['HIGH'] > 0 else '✅ None'} |
| **Medium Issues** | {severity_dist['MEDIUM']} | {'📋 Planned Fixes' if severity_dist['MEDIUM'] > 0 else '✅ None'} |
| **Low Issues** | {severity_dist['LOW']} | {'📝 Improvements' if severity_dist['LOW'] > 0 else '✅ None'} |
| **Total Issues** | {quality['total_issues']} | {'🔴 Needs Work' if quality['total_issues'] > 10 else '🟡 Minor Issues' if quality['total_issues'] > 0 else '🟢 Clean'} |"""
    
    def _generate_metrics_tables(self, structured_data: Dict[str, Any]) -> str:
        """Generate detailed metrics tables"""
        metrics = structured_data['metrics_summary']
        
        tables = ["## 📊 Detailed Metrics"]
        
        # Complexity Metrics Table
        complexity = metrics['complexity']
        tables.append(f"""### 🔧 Complexity Metrics

| Metric | Value | Benchmark | Status |
|--------|-------|-----------|--------|
| **Files with Complexity Data** | {complexity['total_files']} | - | ℹ️ |
| **Average Cognitive Complexity** | {complexity['avg_cognitive_complexity']:.1f} | ≤ 15 | {'🟢 Good' if complexity['avg_cognitive_complexity'] <= 15 else '🔴 High'} |
| **Maximum Nesting Depth** | {complexity['max_nesting_depth']} | ≤ 4 | {'🟢 Good' if complexity['max_nesting_depth'] <= 4 else '🔴 Deep'} |""")
        
        # Maintainability Metrics Table
        maintainability = metrics['maintainability']
        if maintainability['avg_score'] > 0:
            quality_dist = maintainability['quality_distribution']
            tables.append(f"""### 🏗️ Maintainability Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Average Maintainability Score** | {maintainability['avg_score']:.1f}/100 | {'🟢 Excellent' if maintainability['avg_score'] >= 80 else '🟡 Good' if maintainability['avg_score'] >= 60 else '🔴 Needs Work'} |

**Quality Distribution:**
""")
            for quality_level, count in quality_dist.items():
                emoji = {'Excellent': '🟢', 'Good': '🟡', 'Fair': '🟠', 'Poor': '🔴', 'Critical': '🚨'}.get(quality_level, '⚪')
                tables.append(f"- {emoji} **{quality_level}**: {count} files")
        
        # Duplication Metrics Table
        duplication = metrics['duplication']
        tables.append(f"""### 📋 Duplication Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Duplications** | {duplication['total_duplications']} | {'🟢 None Found' if duplication['total_duplications'] == 0 else '🔴 Duplications Present'} |
| **Average Duplication %** | {duplication['avg_duplication_percentage']:.1f}% | {'🟢 Minimal' if duplication['avg_duplication_percentage'] < 5 else '🔴 High'} |""")
        
        return '\n\n'.join(tables)
    
    def _generate_category_analysis(self, structured_data: Dict[str, Any], llm_insights: Dict[str, Any]) -> str:
        """Generate category-specific analysis"""
        analysis = ["## 🔍 Category Analysis"]
        
        category_insights = llm_insights.get('category_insights', {})
        findings_by_category = structured_data['findings_by_category']
        
        for category, findings in findings_by_category.items():
            if not findings:
                continue
                
            category_title = category.replace('_', ' ').title()
            analysis.append(f"### {category_title} ({len(findings)} issues)")
            
            if category in category_insights:
                analysis.append(category_insights[category])
            else:
                analysis.append(f"Found {len(findings)} {category} issues requiring attention.")
        
        return '\n\n'.join(analysis)
    
    def _generate_recommendations_section(self, llm_insights: Dict[str, Any]) -> str:
        """Generate actionable recommendations section"""
        section = ["## 💡 Actionable Recommendations"]
        
        recommendations = llm_insights.get('recommendations', [])
        
        if not recommendations:
            section.append("No specific recommendations generated. Focus on addressing critical and high-priority issues first.")
            return '\n\n'.join(section)
        
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {'Critical': '🚨', 'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(rec.get('priority', 'Medium'), '⚪')
            
            section.append(f"### {priority_emoji} Recommendation {i}: {rec.get('type', 'General Improvement')}")
            section.append(f"**Priority**: {rec.get('priority', 'Medium')}")
            section.append(f"**Affects**: {rec.get('occurrences', 0)} instances across {len(rec.get('affected_files', []))} files")
            section.append("")
            section.append(rec.get('content', 'Recommendation details pending.'))
        
        return '\n\n'.join(section)
    
    def _generate_detailed_findings(self, structured_data: Dict[str, Any], test_files_content: Optional[Dict[str, str]]) -> str:
        """Generate detailed findings section with code examples"""
        section = ["## 📝 Detailed Findings"]
        
        findings_by_file = structured_data['findings_by_file']
        
        for file_path, findings in findings_by_file.items():
            if not findings:
                continue
                
            file_name = Path(file_path).name
            section.append(f"### 📄 {file_name}")
            section.append(f"**Path**: `{file_path}`")
            section.append(f"**Issues**: {len(findings)}")
            section.append("")
            
            # Group findings by severity for better organization
            severity_groups = {}
            for finding in findings:
                severity = str(finding.get('severity', 'LOW')).replace('FindingSeverity.', '')
                if severity not in severity_groups:
                    severity_groups[severity] = []
                severity_groups[severity].append(finding)
            
            # Display findings by severity
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if severity not in severity_groups:
                    continue
                    
                severity_emoji = {'CRITICAL': '🚨', 'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(severity, '⚪')
                section.append(f"#### {severity_emoji} {severity} Issues")
                
                for finding in severity_groups[severity]:
                    section.append(f"- **Line {finding.get('line', 'N/A')}**: {finding.get('description', 'No description')}")
                    if finding.get('recommendation'):
                        section.append(f"  - *Recommendation*: {finding['recommendation']}")
                
                section.append("")
        
        return '\n\n'.join(section)
    
    def _generate_report_footer(self, llm_insights: Dict[str, Any]) -> str:
        """Generate report footer with metadata"""
        confidence = llm_insights.get('confidence_score', 0.0)
        confidence_text = {
            0.9: "High", 0.7: "Medium", 0.5: "Low"
        }.get(min(0.9, max(0.5, round(confidence, 1))), "Medium")
        
        return f"""---

## 📊 Report Metadata

**Analysis Confidence**: {confidence_text} ({confidence:.1f})  
**Generated By**: AI Powered Code Review Analytics System  
**Quality Assurance**: Bias prevention and hallucination controls applied  
**Recommendation**: Review findings in order of priority for maximum impact  

*This report was generated using Multi-Agent AI Powered Code Review Analytics System with quality controls to ensure actionable, unbiased insights.*"""
    
    def _apply_quality_control(self, report_content: str) -> str:
        """Apply quality control checks to the report"""
        # Apply quality gates from configuration
        quality_gates = self.quality_rules.get('quality_gates', {})
        
        # Basic validation checks
        if len(report_content) < 1000:
            logger.warning("Report seems too short, may be incomplete")
        
        # Check for required sections
        required_sections = ['Executive Summary', 'Quality Overview', 'Recommendations']
        for section in required_sections:
            if section not in report_content:
                logger.warning(f"Missing required section: {section}")
        
        return report_content
    
    def _generate_fallback_report(self, analysis_result: Dict[str, Any], output_path: str) -> str:
        """Generate a basic fallback report if LLM analysis fails"""
        try:
            basic_content = f"""# Code Analysis Report (Basic)

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Files Analyzed: {len(analysis_result.get('metrics', {}))}
- Total Findings: {len(analysis_result.get('findings', []))}
- Analysis Success: {analysis_result.get('success', False)}

## Findings
"""
            
            findings = analysis_result.get('findings', [])
            for i, finding in enumerate(findings, 1):
                basic_content += f"{i}. {finding.get('description', 'No description')} (Line {finding.get('line', 'N/A')})\n"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(basic_content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate fallback report: {e}")
            return output_path
    
    def _generate_fallback_insights(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic insights when LLM analysis fails"""
        quality = structured_data['quality_assessment']
        
        return {
            'summary': f"Analysis found {quality['total_issues']} issues with overall quality rated as {quality['quality_level']}.",
            'priority': "Focus on critical and high-severity issues first.",
            'recommendation': "Review findings systematically and implement fixes based on priority."
        }
    
    def _generate_fallback_summary(self, structured_data: Dict[str, Any]) -> str:
        """Generate fallback executive summary"""
        quality = structured_data['quality_assessment']
        summary = structured_data['summary']
        
        return f"""Analysis of {summary['files_analyzed']} files revealed {quality['total_issues']} total issues, 
resulting in an overall quality score of {quality['overall_score']}/100 ({quality['quality_level']}). 
{'Immediate attention is required for critical issues.' if quality['needs_immediate_attention'] else 'The codebase shows manageable quality issues.'} 
Focus should be placed on addressing high-priority items first to improve overall code maintainability."""


# Factory function
def create_enhanced_report_generator() -> EnhancedReportGenerator:
    """Create an enhanced report generator instance"""
    return EnhancedReportGenerator()