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
from .tools.maintainability_assessor import maintainability_assessor_tool
from agents.base.tools.tool_schemas import CodeFileInput, AnalysisLanguage
from agents.base.tools.llm_provider import get_llm_provider, LLMRequest
from agents.base.tools.llm_response_validator import validate_llm_response

logger = logging.getLogger(__name__)


@dataclass
class CodeAnalysisConfig:
    """Configuration for code analysis operations"""
    enable_enhanced_analysis: bool
    max_file_size: int  
    supported_languages: List[str]
    parallel_analysis: bool
    output_format: str
    
    @classmethod
    def from_yaml_config(cls, config_dict: Dict[str, Any]) -> 'CodeAnalysisConfig':
        """Create configuration from loaded YAML config"""
        analysis_config = config_dict['analysis']
        agent_config = config_dict['agent']
        
        # Extract values from config - no fallbacks, config is required
        enable_enhanced_analysis = analysis_config['enhanced_mode']
        max_file_size_mb = analysis_config['max_file_size_mb']
        max_file_size = max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        supported_languages = analysis_config['supported_languages']
        parallel_analysis = analysis_config['parallel_analysis']
        output_format = agent_config['output_format']
        
        return cls(
            enable_enhanced_analysis=enable_enhanced_analysis,
            max_file_size=max_file_size,
            supported_languages=supported_languages,
            parallel_analysis=parallel_analysis,
            output_format=output_format
        )


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
        # We'll load the config from YAML in _load_agent_config, not here
        self.analysis_config = config  # This will be None initially if not provided
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
            if hasattr(complexity_result, 'findings') and complexity_result.findings:
                for finding_data in complexity_result.findings:
                    # Handle both dict and AnalysisOutput object findings
                    if isinstance(finding_data, dict):
                        # Handle the key mapping from complexity analyzer format
                        title = finding_data.get('title', finding_data.get('type', 'Complexity Issue'))
                        line_number = finding_data.get('line_number', finding_data.get('line', 1))
                        finding = Finding(
                            title=title,
                            description=finding_data['message'],
                            severity=FindingSeverity.MEDIUM,
                            category='complexity',
                            file_path=file_path,
                            line_number=line_number,
                            recommendation=finding_data.get('suggestion', 'No recommendation available')
                        )
                        findings.append(finding)
                # Store metrics from AnalysisOutput object
                if hasattr(complexity_result, 'metrics'):
                    metrics['complexity'] = complexity_result.metrics
            
            # Run duplication detection
            files_dict = [{"file_path": file_path, "content": content}]
            if mode == 'enhanced':
                duplication_result = await enhanced_duplication_analysis(files_dict, True)
            else:
                duplication_result = duplication_detector_tool(files_dict)
            
            # Process duplication results
            if isinstance(duplication_result, dict):
                # Handle duplications key
                duplications = duplication_result['duplications']
                if duplications:
                    for dup_data in duplications:
                        finding = Finding(
                            title='Code duplication detected',
                            description=f"Duplicate code found: {dup_data['clone_type']} with {dup_data['similarity_score']:.2%} similarity",
                            severity=FindingSeverity.MEDIUM,
                            category='duplication',
                            file_path=file_path,
                            line_number=dup_data['block1']['start_line'],
                            recommendation='Consider refactoring duplicate code into shared functions'
                        )
                        findings.append(finding)
                
                # Store metrics
                metrics['duplication'] = {
                    'total_duplications': duplication_result['total_duplications'],
                    'duplication_percentage': duplication_result['duplication_percentage'],
                    'clone_type_distribution': duplication_result['clone_type_distribution'],
                    'processing_time': duplication_result['processing_time']
                }
            
            # Run maintainability analysis - use unified assessor tool
            maintainability_result = maintainability_assessor_tool(files_dict)
            
            # Process maintainability results
            if isinstance(maintainability_result, dict) and 'maintainability_index' in maintainability_result:
                # This is from unified maintainability_assessor_tool function
                metrics['maintainability'] = {
                    'score': maintainability_result['maintainability_index'],
                    'quality_level': maintainability_result['quality_level'],
                    'complexity_score': maintainability_result['scores']['complexity_score'],
                    'duplication_score': maintainability_result['scores']['duplication_score'],
                    'documentation_score': maintainability_result['scores']['documentation_score'],
                    'naming_score': maintainability_result['scores']['naming_score'],
                    'structure_score': maintainability_result['scores']['structure_score'],
                    'test_coverage_score': maintainability_result['scores']['test_coverage_score'],
                    'processing_time': maintainability_result['processing_time']
                }
                
                # Check for findings key
            else:
                # If no maintainability_index, log the unexpected format
                logger.warning(f"Unexpected maintainability result format: {maintainability_result}")
                
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
        
        return findings, metrics
    
    def _score_to_quality_level(self, score: float) -> str:
        """Convert maintainability score (0.0-1.0) to quality level"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        elif score >= 0.2:
            return "Poor"
        else:
            return "Critical"
    
    def _detect_language(self, file_path: str) -> AnalysisLanguage:
        """Detect programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        
        # Get language mapping from configuration
        language_extensions = self.agent_config['language_detection']['file_extensions']
        language_name = language_extensions[extension]
        
        # Get enum mapping from configuration
        enum_mapping = self.agent_config['language_detection']['enum_mapping']
        enum_value = enum_mapping[language_name]
        
        # Return the corresponding AnalysisLanguage enum
        return getattr(AnalysisLanguage, enum_value)
    
    def _format_analysis_summary(self, result: AnalysisResult) -> str:
        """Generate LLM-powered analysis summary"""
        return asyncio.run(self._generate_llm_summary(result))
    
    async def _generate_llm_summary(self, result: AnalysisResult) -> str:
        """Generate analysis summary using LLM with quality control"""
        try:
            # Prepare analysis data for LLM
            analysis_data = {
                "files_analyzed": len(result.findings),
                "total_findings": len(result.findings),
                "execution_time": result.execution_time,
                "findings_by_severity": self._categorize_findings(result.findings),
                "findings_by_category": self._group_findings_by_category(result.findings),
                "metrics": result.metrics
            }
            
            # Get prompt template from config - required, no fallback
            prompt_template = self.llm_config['agent_llm']['response_generation']['prompt_template']
            if not prompt_template:
                raise ValueError("Missing required config: agent_llm.response_generation.prompt_template")
            
            # Use configured prompt template
            prompt = prompt_template.format(
                files_analyzed=analysis_data['files_analyzed'],
                issues_found=analysis_data['total_findings'],
                analysis_type="comprehensive code quality analysis",
                severity_breakdown=json.dumps(analysis_data['findings_by_severity'])
            )
            
            system_prompt = self.llm_config['agent_llm']['response_generation']['system_prompt']
            if not system_prompt:
                raise ValueError("Missing required config: agent_llm.response_generation.system_prompt")
            
            # Get temperature and max_tokens from config
            temperature = self.llm_config['agent_llm']['response_generation']['temperature']
            max_tokens = self.llm_config['agent_llm']['response_generation']['max_tokens']
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Use quality-controlled LLM response with bias prevention and hallucination detection
            validation_result = await validate_llm_response(
                llm_request=llm_request,
                context_data={
                    'findings': result.findings,
                    'metrics': result.metrics,
                    'findings_by_severity': analysis_data['findings_by_severity'],
                    'findings_by_category': analysis_data['findings_by_category']
                },
                response_type="summary"
            )
            
            if validation_result.is_valid:
                # Log quality metrics for monitoring
                logger.info(f"LLM summary generated with confidence: {validation_result.confidence_score:.2f}, "
                           f"evidence: {validation_result.evidence_score:.2f}")
                
                # Log any warnings
                if validation_result.validation_warnings:
                    logger.warning(f"LLM summary warnings: {validation_result.validation_warnings}")
                
                return validation_result.cleaned_response
            else:
                # Fail fast - no fallback, configuration or validation must work
                logger.error(f"LLM summary validation failed: {validation_result.validation_errors}")
                raise ValueError(f"LLM summary validation failed: {validation_result.validation_errors}")
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            raise
    
    def _categorize_findings(self, findings: List[Finding]) -> Dict[str, int]:
        """Categorize findings by severity"""
        categories = {"high": 0, "medium": 0, "low": 0}
        for finding in findings:
            if finding.severity == FindingSeverity.HIGH:
                categories["high"] += 1
            elif finding.severity == FindingSeverity.MEDIUM:
                categories["medium"] += 1
            elif finding.severity == FindingSeverity.LOW:
                categories["low"] += 1
        return categories
    
    def _group_findings_by_severity(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Group findings by severity level"""
        groups = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for finding in findings:
            if finding.severity == FindingSeverity.HIGH:
                groups["HIGH"].append(finding)
            elif finding.severity == FindingSeverity.MEDIUM:
                groups["MEDIUM"].append(finding)
            elif finding.severity == FindingSeverity.LOW:
                groups["LOW"].append(finding)
        return groups
    
    def _group_findings_by_category(self, findings: List[Finding]) -> Dict[str, int]:
        """Group findings by category"""
        categories = {}
        for finding in findings:
            category = finding.category
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        return categories
    
    def _format_findings_details(self, findings: List[Finding]) -> str:
        """Generate LLM-powered findings details with JSON output option"""
        # Check if JSON output is requested
        output_format = self.llm_config['output']['format']
        
        if output_format == 'json':
            return self._generate_json_output(findings)
        else:
            # Use LLM for markdown format
            return asyncio.run(self._generate_llm_findings_details(findings))
    
    def _generate_json_output(self, findings: List[Finding]) -> str:
        """Generate structured JSON output"""
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
                "file_path": finding.file_path,
                "line_number": finding.line_number,
                "severity": str(finding.severity),
                "category": finding.category,
                "title": finding.title,
                "description": finding.description,
                "suggestion": finding.recommendation
            }
            output_data["analysis_results"]["detailed_findings"].append(finding_data)
        
        # Pretty print if configured
        if self.llm_config['output']['pretty_print']:
            return json.dumps(output_data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(output_data, ensure_ascii=False)
    
    async def _generate_llm_findings_details(self, findings: List[Finding]) -> str:
        """Generate detailed findings using LLM with quality control"""
        try:
            if not findings:
                return "✅ **No issues found** - Code quality looks good!"
            
            # Prepare findings data for LLM
            findings_data = []
            for finding in findings:
                finding_info = {
                    "file": finding.file_path,
                    "line": finding.line_number,
                    "severity": str(finding.severity),
                    "category": finding.category,
                    "title": finding.title,
                    "description": finding.description
                }
                findings_data.append(finding_info)
            
            # Get prompt template from config - required, no fallback
            prompt_template = self.llm_config['agent_llm']['findings_enhancement']['prompt_template']
            if not prompt_template:
                raise ValueError("Missing required config: agent_llm.findings_enhancement.prompt_template")
            
            # Use configured prompt template
            prompt = prompt_template.format(
                findings_data=json.dumps(findings_data[:10], indent=2)  # Limit to first 10 for prompt size
            )
            
            system_prompt = self.llm_config['agent_llm']['findings_enhancement']['system_prompt']
            if not system_prompt:
                raise ValueError("Missing required config: agent_llm.findings_enhancement.system_prompt")
            
            # Get temperature and max_tokens from config
            temperature = self.llm_config['agent_llm']['findings_enhancement']['temperature']
            max_tokens = self.llm_config['agent_llm']['findings_enhancement']['max_tokens']
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Use quality-controlled LLM response with bias prevention and hallucination detection
            validation_result = await validate_llm_response(
                llm_request=llm_request,
                context_data={
                    'findings': findings_data,
                    'findings_by_severity': self._categorize_findings(findings),
                    'findings_by_category': self._group_findings_by_category(findings)
                },
                response_type="findings_details"
            )
            
            if validation_result.is_valid:
                # Log quality metrics for monitoring
                logger.info(f"LLM findings generated with confidence: {validation_result.confidence_score:.2f}, "
                           f"evidence: {validation_result.evidence_score:.2f}")
                
                # Log any warnings
                if validation_result.validation_warnings:
                    logger.warning(f"LLM findings warnings: {validation_result.validation_warnings}")
                
                return validation_result.cleaned_response
            else:
                # Fail fast - no fallback, configuration or validation must work
                logger.error(f"LLM findings validation failed: {validation_result.validation_errors}")
                raise ValueError(f"LLM findings validation failed: {validation_result.validation_errors}")
            
        except Exception as e:
            logger.error(f"LLM findings generation failed: {e}")
            raise
    
    def _initialize_tools(self):
        """Initialize the quality analysis tools available to this agent"""
        if not self.tools_initialized:
            self.tools = {
                'complexity_analyzer': complexity_analyzer_tool,
                'enhanced_complexity_analysis': enhanced_complexity_analysis,
                'duplication_detector': duplication_detector_tool,
                'enhanced_duplication_analysis': enhanced_duplication_analysis,
                'maintainability_assessor': maintainability_assessor_tool,
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
            
            # Update analysis_config with values from YAML
            if self.analysis_config is None:
                self.analysis_config = CodeAnalysisConfig.from_yaml_config(self.agent_config)
            else:
                # Update existing config with YAML values
                updated_config = CodeAnalysisConfig.from_yaml_config(self.agent_config)
                self.analysis_config = updated_config
                
        except Exception as e:
            logger.error(f"Failed to load agent configuration: {e}")
            raise
        
        try:
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                self.llm_config = yaml.safe_load(f)
            logger.debug("Loaded shared LLM configuration from agents/configs/")
        except Exception as e:
            logger.error(f"Failed to load LLM configuration: {e}")
            raise


# Factory function for agent creation
def create_code_analyzer_agent(config: Optional[CodeAnalysisConfig] = None) -> CodeAnalyzerAgent:
    """Factory function to create a code analyzer agent"""
    return CodeAnalyzerAgent(config=config)


# Export classes and functions
__all__ = ['CodeAnalyzerAgent', 'CodeAnalysisConfig', 'create_code_analyzer_agent']