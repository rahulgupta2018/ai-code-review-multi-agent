"""
Google ADK Code Analyzer Agent

A comprehensive code analysis agent that orchestrates multiple quality assessment tools
following Google ADK patterns for multi-agent systems with orchestrator support.
"""

import asyncio
import time
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
from .tools.maintainability_scorer import enhanced_maintainability_analysis, maintainability_scorer_tool
from agents.base.tools.tool_schemas import CodeFileInput, AnalysisLanguage

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
        context = AnalysisContext(
            files=files,
            language=AnalysisLanguage.PYTHON,  # Default
            enhanced_mode=(mode == 'enhanced')
        )
        
        return AnalysisResult(
            context=context,
            findings=all_findings,
            metrics=all_metrics,
            analysis_time=time.time() - start_time
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
                complexity_result = enhanced_complexity_analysis(file_input, True)
            else:
                complexity_result = complexity_analyzer_tool(file_input)
            
            findings.extend(complexity_result.findings)
            metrics['complexity'] = complexity_result.metrics
            
            # Run duplication detection
            files_dict = [{"file_path": file_path, "content": content}]
            if mode == 'enhanced':
                duplication_result = enhanced_duplication_analysis(files_dict, True)
            else:
                duplication_result = duplication_detector_tool(files_dict)
            
            # Process duplication results
            if isinstance(duplication_result, dict) and 'findings' in duplication_result:
                for finding_data in duplication_result['findings']:
                    finding = Finding(
                        file_path=file_path,
                        line_number=finding_data.get('line_number', 1),
                        severity=FindingSeverity.MEDIUM,
                        category='duplication',
                        message=finding_data.get('message', 'Code duplication detected'),
                        suggestion=finding_data.get('suggestion', '')
                    )
                    findings.append(finding)
                metrics['duplication'] = duplication_result.get('metrics', {})
            
            # Run maintainability scoring
            if mode == 'enhanced':
                maintainability_result = enhanced_maintainability_analysis(files_dict, True)
            else:
                maintainability_result = maintainability_scorer_tool(files_dict)
            
            # Process maintainability results
            if isinstance(maintainability_result, dict) and 'findings' in maintainability_result:
                for finding_data in maintainability_result['findings']:
                    finding = Finding(
                        file_path=file_path,
                        line_number=finding_data.get('line_number', 1),
                        severity=FindingSeverity.LOW,
                        category='maintainability',
                        message=finding_data.get('message', 'Maintainability issue detected'),
                        suggestion=finding_data.get('suggestion', '')
                    )
                    findings.append(finding)
                metrics['maintainability'] = maintainability_result.get('metrics', {})
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
        
        return findings, metrics
    
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
            '.c': AnalysisLanguage.C,
            '.cpp': AnalysisLanguage.CPP,
            '.cc': AnalysisLanguage.CPP,
            '.cxx': AnalysisLanguage.CPP,
            '.go': AnalysisLanguage.GO,
            '.rs': AnalysisLanguage.RUST
        }
        
        return language_mapping.get(extension, AnalysisLanguage.PYTHON)
    
    def _format_analysis_summary(self, result: AnalysisResult) -> str:
        """Format analysis result summary for output"""
        return f"""
📊 **Code Analysis Complete**

- **Files Analyzed**: {len(result.context.files)}
- **Total Findings**: {len(result.findings)}
- **Analysis Time**: {result.analysis_time:.2f}s
- **Mode**: {'Enhanced (LLM)' if result.context.enhanced_mode else 'Standard'}

**Findings by Severity**:
- High: {len([f for f in result.findings if f.severity == FindingSeverity.HIGH])}
- Medium: {len([f for f in result.findings if f.severity == FindingSeverity.MEDIUM])}
- Low: {len([f for f in result.findings if f.severity == FindingSeverity.LOW])}
"""
    
    def _format_findings_details(self, findings: List[Finding]) -> str:
        """Format detailed findings for output"""
        if not findings:
            return ""
        
        details = "🔍 **Detailed Findings**:\n\n"
        
        # Group by category
        by_category = {}
        for finding in findings:
            if finding.category not in by_category:
                by_category[finding.category] = []
            by_category[finding.category].append(finding)
        
        for category, category_findings in by_category.items():
            details += f"**{category.title()}** ({len(category_findings)} issues):\n"
            for finding in category_findings[:5]:  # Limit to first 5 per category
                details += f"- Line {finding.line_number}: {finding.message}\n"
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
                'enhanced_maintainability_analysis': enhanced_maintainability_analysis,
            }
            self.tools_initialized = True
            logger.debug(f"Initialized {len(self.tools)} quality analysis tools")
    
    def _load_agent_config(self):
        """Load agent configuration from YAML file"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "agents" / "code_analyzer.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.agent_config = yaml.safe_load(f)
            logger.debug("Loaded code analyzer agent configuration")
        except Exception as e:
            logger.warning(f"Failed to load agent configuration: {e}")
            self.agent_config = {"agents": {"code_analyzer": {"enabled": True}}}


# Factory function for agent creation
def create_code_analyzer_agent(config: Optional[CodeAnalysisConfig] = None) -> CodeAnalyzerAgent:
    """Factory function to create a code analyzer agent"""
    return CodeAnalyzerAgent(config=config)


# Export classes and functions
__all__ = ['CodeAnalyzerAgent', 'CodeAnalysisConfig', 'create_code_analyzer_agent']