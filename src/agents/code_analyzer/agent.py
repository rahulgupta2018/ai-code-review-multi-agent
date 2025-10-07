"""
Google ADK Code Analyzer Agent

A comprehensive code analysis agent that orchestrates multiple quality assessment tools
following Google ADK patterns for multi-agent systems with orchestrator support.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path
import logging
import sys
import os
import yaml

# Add the src directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "..", "..", "..")
sys.path.insert(0, src_dir)

# Google ADK imports
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions

# Vertex AI imports for content generation
from vertexai.generative_models import Content, Part

# Base agent classes
from agents.base.base_classes import Finding, FindingSeverity, AnalysisContext, AnalysisResult

# Agent-specific quality tools (moved to agent's tools directory)
from .tools.complexity_analyzer import enhanced_complexity_analysis, complexity_analyzer_tool
from .tools.duplication_detector import enhanced_duplication_analysis, duplication_detector_tool
from .tools.maintainability_scorer import maintainability_scoring, maintainability_scorer_tool
from .tools.maintainability_assessor import maintainability_assessment, maintainability_assessor_tool
from agents.base.tools.tool_schemas import CodeFileInput, AnalysisLanguage
from agents.base.tools.llm_provider import get_llm_provider, LLMRequest

logger = logging.getLogger(__name__)


@dataclass
class CodeAnalysisConfig:
    """Configuration for code analysis operations"""
    enable_enhanced_analysis: bool = True
    max_file_size: int = 1024 * 1024  # 1MB
    supported_languages: List[str] = field(default_factory=lambda: [
        'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'go', 'rust'
    ])
    parallel_analysis: bool = True
    output_format: str = 'json'


class CodeAnalyzerAgent(BaseAgent):
    """
    Google ADK Code Analyzer Agent
    
    Orchestrates comprehensive code quality analysis using multiple specialized tools:
    - Complexity Analysis: Cyclomatic complexity, cognitive complexity, nesting depth
    - Duplication Detection: AST-based clone detection across files
    - Maintainability Scoring: Holistic quality metrics combining multiple factors
    
    Follows Google ADK patterns for multi-agent systems with proper event generation,
    session state management, and orchestrator communication.
    """
    
    # Define Pydantic model fields for the agent
    analysis_config: Optional[CodeAnalysisConfig] = None
    tools_initialized: bool = False
    agent_config: Dict[str, Any] = {}
    llm_config: Dict[str, Any] = {}
    tools: Dict[str, Any] = {}
    
    def __init__(self, config: Optional[CodeAnalysisConfig] = None, **kwargs):
        """Initialize the code analyzer agent"""
        # Set defaults for required BaseAgent fields if not provided
        if 'name' not in kwargs:
            kwargs['name'] = "code_analyzer"
        if 'description' not in kwargs:
            kwargs['description'] = "Code analysis agent for quality assessment using complexity analysis, duplication detection, and maintainability scoring"
        
        # Initialize BaseAgent
        super().__init__(**kwargs)
        
        # Set agent-specific configuration using model fields
        self.analysis_config = config or CodeAnalysisConfig()
        self.tools_initialized = False
        
        # Initialize agent components
        self._load_agent_config()
        self._initialize_tools()
        
        logger.info("Code Analyzer ADK Agent initialized")
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Main execution method following Google ADK BaseAgent pattern
        
        Processes user requests for code analysis and generates appropriate events
        for orchestrator communication and result delivery.
        """
        try:
            # Extract parameters from user content and session state
            user_content = self._extract_user_content(ctx)
            session_state = ctx.session.state if ctx.session else {}
            
            # Determine analysis parameters
            files_to_analyze = self._extract_files_parameter(user_content, session_state)
            analysis_mode = self._extract_analysis_mode(user_content, session_state)
            
            # Update session state with current analysis
            if ctx.session:
                ctx.session.state.update({
                    'current_agent': 'code_analyzer',
                    'analysis_mode': analysis_mode,
                    'files_count': len(files_to_analyze) if files_to_analyze else 0
                })
            
            # Yield initial event indicating analysis start
            yield Event(
                author='code_analyzer',
                content=Content(parts=[
                    Part.from_text(f"🔍 Starting code quality analysis{' with LLM enhancement' if analysis_mode == 'enhanced' else ''}")
                ])
            )
            
            # Perform the analysis
            if files_to_analyze:
                analysis_result = await self._perform_analysis(files_to_analyze, analysis_mode)
                
                # Generate summary event
                summary_text = self._format_analysis_summary(analysis_result)
                yield Event(
                    author='code_analyzer',
                    content=Content(parts=[Part.from_text(summary_text)]),
                    actions=EventActions(state_delta={
                        'last_analysis_result': {
                            'findings_count': len(analysis_result.findings),
                            'execution_time': analysis_result.execution_time,
                            'timestamp': time.time()
                        }
                    })
                )
                
                # Generate detailed findings event if any issues found
                if analysis_result.findings:
                    findings_text = self._format_findings_details(analysis_result.findings)
                    yield Event(
                        author='code_analyzer',
                        content=Content(parts=[Part.from_text(findings_text)])
                    )
            else:
                yield Event(
                    author='code_analyzer',
                    content=Content(parts=[
                        Part.from_text("❌ No files specified for analysis. Please provide file paths.")
                    ])
                )
        
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            yield Event(
                author='code_analyzer',
                content=Content(parts=[
                    Part.from_text(f"❌ Analysis failed: {str(e)}")
                ])
            )
    
    def _extract_user_content(self, ctx: InvocationContext) -> str:
        """Extract text content from user input"""
        if not ctx.user_input or not ctx.user_input.content or not ctx.user_input.content.parts:
            return ""
        
        text_parts = [part.text for part in ctx.user_input.content.parts if hasattr(part, 'text')]
        return " ".join(text_parts)
    
    def _extract_files_parameter(self, user_content: str, session_state: Dict[str, Any]) -> List[str]:
        """Extract file paths from user content or session state"""
        # Check session state first
        if 'target_files' in session_state:
            return session_state['target_files']
        
        # Parse from user content (simple implementation)
        files = []
        lines = user_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.endswith('.py') or line.endswith('.js') or line.endswith('.ts'):
                if Path(line).exists():
                    files.append(line)
        
        return files
    
    def _extract_analysis_mode(self, user_content: str, session_state: Dict[str, Any]) -> str:
        """Determine analysis mode from input"""
        if 'enhanced' in user_content.lower() or 'llm' in user_content.lower():
            return 'enhanced'
        return 'standard'
    
    async def _perform_analysis(self, files: List[str], mode: str) -> AnalysisResult:
        """Perform the actual code analysis"""
        start_time = time.time()
        all_findings: List[Finding] = []
        all_metrics: Dict[str, Any] = {}
        
        for file_path in files:
            try:
                file_findings, file_metrics = await self._analyze_single_file(file_path, mode)
                all_findings.extend(file_findings)
                all_metrics[file_path] = file_metrics
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                continue
        
        # Create analysis context
        files_dict = [{"file_path": f, "type": "source"} for f in files]
        context = AnalysisContext(
            files=files_dict,
            configuration={"mode": mode, "enhanced": mode == 'enhanced'},
            session_id=f"analysis_{int(time.time())}"
        )
        
        return AnalysisResult(
            agent_name=self.name,
            findings=all_findings,
            metrics=all_metrics,
            execution_time=time.time() - start_time,
            success=True,
            errors=[],
            metadata={"context": context, "mode": mode}
        )
    
    async def _analyze_single_file(self, file_path: str, mode: str) -> tuple[List[Finding], Dict[str, Any]]:
        """Analyze a single file with all available tools"""
        findings: List[Finding] = []
        metrics: Dict[str, Any] = {}
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create file input
            language = self._detect_language(file_path)
            file_input = CodeFileInput(
                file_path=file_path,
                content=content,
                language=language
            )
            
            # Run complexity analysis
            if mode == 'enhanced':
                complexity_result = await enhanced_complexity_analysis(file_input, True)
            else:
                complexity_result = complexity_analyzer_tool(file_input)
            
            # Process complexity results
            if isinstance(complexity_result, dict) and 'findings' in complexity_result:
                for finding_data in complexity_result['findings']:
                    finding = Finding(
                        title=finding_data.get('title', 'Complexity issue detected'),
                        description=finding_data.get('message', 'High complexity detected in code'),
                        severity=FindingSeverity.MEDIUM,
                        category='complexity',
                        file_path=file_path,
                        line_number=finding_data.get('line_number', 1),
                        recommendation=finding_data.get('suggestion', 'Consider refactoring to reduce complexity')
                    )
                    findings.append(finding)
                metrics['complexity'] = complexity_result.get('metrics', {})
            
            # Run duplication detection
            files_dict = [{"file_path": file_path, "content": content}]
            if mode == 'enhanced':
                duplication_result = await enhanced_duplication_analysis(files_dict, True)
            else:
                duplication_result = duplication_detector_tool(files_dict)
            
            # Process duplication results
            if isinstance(duplication_result, dict) and 'findings' in duplication_result:
                for finding_data in duplication_result['findings']:
                    finding = Finding(
                        title=finding_data.get('title', 'Code duplication detected'),
                        description=finding_data.get('message', 'Duplicate code patterns found'),
                        severity=FindingSeverity.MEDIUM,
                        category='duplication',
                        file_path=file_path,
                        line_number=finding_data.get('line_number', 1),
                        recommendation=finding_data.get('suggestion', 'Consider refactoring duplicate code')
                    )
                    findings.append(finding)
                metrics['duplication'] = duplication_result.get('metrics', {})
            
            # Run maintainability analysis - intelligent routing
            if mode == 'enhanced':
                # For enhanced mode, choose tool based on context
                if self._should_use_detailed_assessment(files_dict):
                    # Use assessor for single-file detailed analysis
                    maintainability_result = await maintainability_assessment(file_path, content)
                else:
                    # Use scorer for multi-file quantitative analysis
                    maintainability_result = await maintainability_scoring(files_dict, True)
            else:
                # Standard mode always uses scorer
                maintainability_result = maintainability_scorer_tool(files_dict)
            
            # Process maintainability results
            if isinstance(maintainability_result, dict) and 'findings' in maintainability_result:
                for finding_data in maintainability_result['findings']:
                    finding = Finding(
                        title=finding_data.get('title', 'Maintainability issue detected'),
                        description=finding_data.get('message', 'Code maintainability could be improved'),
                        severity=FindingSeverity.LOW,
                        category='maintainability',
                        file_path=file_path,
                        line_number=finding_data.get('line_number', 1),
                        recommendation=finding_data.get('suggestion', 'Review and refactor for better maintainability')
                    )
                    findings.append(finding)
                metrics['maintainability'] = maintainability_result.get('metrics', {})
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
        
        return findings, metrics
    
    def _should_use_detailed_assessment(self, files_dict: List[Dict[str, str]]) -> bool:
        """
        Determine whether to use detailed assessment vs quantitative scoring
        
        Args:
            files_dict: List of file dictionaries with content
            
        Returns:
            True if detailed assessment should be used, False for scoring
        """
        # Use detailed assessment for single file analysis
        if len(files_dict) == 1:
            return True
        
        # Use scoring for multi-file analysis
        return False
    
    def _detect_language(self, file_path: str) -> AnalysisLanguage:
        """Detect programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        
        language_mapping = {
            '.py': AnalysisLanguage.PYTHON,
            '.js': AnalysisLanguage.JAVASCRIPT,
            '.jsx': AnalysisLanguage.JAVASCRIPT,
            '.ts': AnalysisLanguage.TYPESCRIPT,
            '.tsx': AnalysisLanguage.TYPESCRIPT,
            '.java': AnalysisLanguage.JAVA,
            '.c': AnalysisLanguage.CPP,  # Treat C as CPP for analysis
            '.cpp': AnalysisLanguage.CPP,
            '.cc': AnalysisLanguage.CPP,
            '.cxx': AnalysisLanguage.CPP,
            '.go': AnalysisLanguage.GO,
            '.rs': AnalysisLanguage.RUST
        }
        
        return language_mapping.get(extension, AnalysisLanguage.PYTHON)
    
    def _format_analysis_summary(self, result: AnalysisResult) -> str:
        """Generate LLM-powered analysis summary"""
        try:
            # Use LLM for dynamic summary generation
            return asyncio.run(self._generate_llm_summary(result))
        except Exception as e:
            logger.warning(f"LLM summary generation failed, using fallback: {e}")
            return self._format_static_summary(result)
    
    async def _generate_llm_summary(self, result: AnalysisResult) -> str:
        """Generate analysis summary using LLM"""
        try:
            # Prepare analysis data for LLM
            analysis_data = {
                "files_analyzed": len(result.findings) if hasattr(result, 'findings') else 0,
                "total_findings": len(result.findings) if hasattr(result, 'findings') else 0,
                "execution_time": getattr(result, 'execution_time', 0),
                "findings_by_severity": self._categorize_findings(result.findings if hasattr(result, 'findings') else []),
                "findings_by_category": self._group_findings_by_category(result.findings if hasattr(result, 'findings') else []),
                "metrics": getattr(result, 'metrics', {})
            }
            
            # Get LLM provider
            llm_provider = get_llm_provider()
            
            # Get prompt template from config - required, no fallback
            prompt_template = self.llm_config.get('agent_llm', {}).get('response_generation', {}).get('prompt_template', '')
            if not prompt_template:
                raise ValueError("Missing required config: agent_llm.response_generation.prompt_template")
            
            # Use configured prompt template
            prompt = prompt_template.format(
                files_analyzed=analysis_data.get('files_analyzed', 0),
                issues_found=analysis_data.get('issues_found', 0),
                analysis_type=analysis_data.get('analysis_type', 'code_quality'),
                severity_breakdown=json.dumps(analysis_data.get('findings_by_severity', {}))
            )
            
            system_prompt = self.llm_config.get('agent_llm', {}).get('response_generation', {}).get('system_prompt', '')
            if not system_prompt:
                raise ValueError("Missing required config: agent_llm.response_generation.system_prompt")
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=2048
            )
            
            # Generate LLM response
            response = await llm_provider.generate_response(llm_request)
            return response.content if hasattr(response, 'content') else self._format_static_summary(result)
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return self._format_static_summary(result)
    
    def _categorize_findings(self, findings: List[Finding]) -> Dict[str, int]:
        """Categorize findings by severity"""
        categories = {"high": 0, "medium": 0, "low": 0}
        for finding in findings:
            if hasattr(finding, 'severity'):
                if finding.severity == FindingSeverity.HIGH:
                    categories["high"] += 1
                elif finding.severity == FindingSeverity.MEDIUM:
                    categories["medium"] += 1
                elif finding.severity == FindingSeverity.LOW:
                    categories["low"] += 1
        return categories
    
    def _group_findings_by_category(self, findings: List[Finding]) -> Dict[str, int]:
        """Group findings by category"""
        categories = {}
        for finding in findings:
            if hasattr(finding, 'category'):
                category = finding.category
                categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _format_static_summary(self, result: AnalysisResult) -> str:
        """Fallback static summary format"""
        findings_count = len(result.findings) if hasattr(result, 'findings') else 0
        execution_time = getattr(result, 'execution_time', 0)
        
        return f"""
📊 **Code Analysis Complete**

- **Total Findings**: {findings_count}
- **Analysis Time**: {execution_time:.2f}s
- **Mode**: Enhanced (LLM)

**Summary**: Analysis completed successfully with {findings_count} findings identified.
"""
    
    def _format_findings_details(self, findings: List[Finding]) -> str:
        """Generate LLM-powered findings details with JSON output option"""
        try:
            # Check if JSON output is requested
            output_format = self.llm_config.get('output', {}).get('format', 'markdown')
            
            if output_format == 'json':
                return self._generate_json_output(findings)
            else:
                # Use LLM for markdown format
                return asyncio.run(self._generate_llm_findings_details(findings))
        except Exception as e:
            logger.warning(f"LLM findings generation failed, using fallback: {e}")
            return self._format_static_findings(findings)
    
    def _generate_json_output(self, findings: List[Finding]) -> str:
        """Generate structured JSON output"""
        try:
            output_data = {
                "analysis_results": {
                    "timestamp": time.time(),
                    "agent": "code_analyzer",
                    "total_findings": len(findings),
                    "findings_by_severity": self._categorize_findings(findings),
                    "findings_by_category": self._group_findings_by_category(findings),
                    "detailed_findings": []
                }
            }
            
            # Add detailed findings
            for finding in findings:
                finding_data = {
                    "file_path": getattr(finding, 'file_path', ''),
                    "line_number": getattr(finding, 'line_number', 0),
                    "severity": str(getattr(finding, 'severity', 'unknown')),
                    "category": getattr(finding, 'category', 'general'),
                    "title": getattr(finding, 'title', ''),
                    "description": getattr(finding, 'description', ''),
                    "suggestion": getattr(finding, 'suggestion', '')
                }
                output_data["analysis_results"]["detailed_findings"].append(finding_data)
            
            # Pretty print if configured
            if self.llm_config.get('output', {}).get('pretty_print', True):
                return json.dumps(output_data, indent=2, ensure_ascii=False)
            else:
                return json.dumps(output_data, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"JSON output generation failed: {e}")
            return json.dumps({"error": f"Failed to generate JSON output: {str(e)}"}, indent=2)
    
    async def _generate_llm_findings_details(self, findings: List[Finding]) -> str:
        """Generate detailed findings using LLM"""
        try:
            if not findings:
                return "✅ **No issues found** - Code quality looks good!"
            
            # Prepare findings data for LLM
            findings_data = []
            for finding in findings:
                finding_info = {
                    "file": getattr(finding, 'file_path', ''),
                    "line": getattr(finding, 'line_number', 0),
                    "severity": str(getattr(finding, 'severity', 'unknown')),
                    "category": getattr(finding, 'category', 'general'),
                    "title": getattr(finding, 'title', ''),
                    "description": getattr(finding, 'description', '')
                }
                findings_data.append(finding_info)
            
            # Get LLM provider
            llm_provider = get_llm_provider()
            
            # Get prompt template from config - required, no fallback
            prompt_template = self.llm_config.get('agent_llm', {}).get('findings_enhancement', {}).get('prompt_template', '')
            if not prompt_template:
                raise ValueError("Missing required config: agent_llm.findings_enhancement.prompt_template")
            
            # Use configured prompt template
            prompt = prompt_template.format(
                findings_data=json.dumps(findings_data[:10], indent=2)  # Limit to first 10 for prompt size
            )
            
            system_prompt = self.llm_config.get('agent_llm', {}).get('findings_enhancement', {}).get('system_prompt', '')
            if not system_prompt:
                raise ValueError("Missing required config: agent_llm.findings_enhancement.system_prompt")
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=1024
            )
            
            # Generate LLM response
            response = await llm_provider.generate_response(llm_request)
            return response.content if hasattr(response, 'content') else self._format_static_findings(findings)
            
        except Exception as e:
            logger.error(f"LLM findings generation failed: {e}")
            return self._format_static_findings(findings)
    
    def _format_static_findings(self, findings: List[Finding]) -> str:
        """Fallback static findings format"""
        if not findings:
            return "✅ **No issues found** - Code quality looks good!"
        
        details = "🔍 **Detailed Findings**:\n\n"
        
        # Group by category
        by_category = {}
        for finding in findings:
            category = getattr(finding, 'category', 'general')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(finding)
        
        for category, category_findings in by_category.items():
            details += f"**{category.title()}** ({len(category_findings)} issues):\n"
            for finding in category_findings[:5]:  # Limit to first 5 per category
                line_num = getattr(finding, 'line_number', 0)
                title = getattr(finding, 'title', 'Issue found')
                details += f"- Line {line_num}: {title}\n"
            if len(category_findings) > 5:
                details += f"  ... and {len(category_findings) - 5} more\n"
            details += "\n"
        
        return details
    
    def _initialize_tools(self):
        """Initialize the quality analysis tools available to this agent"""
        if not self.tools_initialized:
            self.tools = {
                'complexity_analyzer': complexity_analyzer_tool,
                'enhanced_complexity_analysis': enhanced_complexity_analysis,
                'duplication_detector': duplication_detector_tool,
                'enhanced_duplication_analysis': enhanced_duplication_analysis,
                'maintainability_scorer': maintainability_scorer_tool,
                'maintainability_scoring': maintainability_scoring,
                'maintainability_assessor': maintainability_assessor_tool,
                'maintainability_assessment': maintainability_assessment,
            }
            self.tools_initialized = True
            logger.debug(f"Initialized {len(self.tools)} quality analysis tools")
    
    def _load_agent_config(self):
        """Load agent configuration from YAML file"""
        config_path = Path(__file__).parent / "configs" / "code_analyzer.yaml"
        # Load shared LLM config from agents level
        llm_config_path = Path(__file__).parent.parent / "configs" / "llm_config.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.agent_config = yaml.safe_load(f)
            logger.debug("Loaded code analyzer agent configuration")
        except Exception as e:
            logger.warning(f"Failed to load agent configuration: {e}")
            self.agent_config = {"agents": {"code_analyzer": {"enabled": True}}}
        
        try:
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                self.llm_config = yaml.safe_load(f)
            logger.debug("Loaded shared LLM configuration from agents/configs/")
        except Exception as e:
            logger.warning(f"Failed to load LLM configuration: {e}")
            self.llm_config = {"output": {"format": "json"}, "agent_llm": {"response_generation": {"system_prompt": "You are a code analysis assistant."}}}


# Factory function for agent creation
def create_code_analyzer_agent(config: Optional[CodeAnalysisConfig] = None) -> CodeAnalyzerAgent:
    """Factory function to create a code analyzer agent"""
    return CodeAnalyzerAgent(config=config)


# Export classes and functions
__all__ = ['CodeAnalyzerAgent', 'CodeAnalysisConfig', 'create_code_analyzer_agent']