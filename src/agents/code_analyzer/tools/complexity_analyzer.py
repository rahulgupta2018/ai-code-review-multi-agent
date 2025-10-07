"""
Complexity Analyzer FunctionTool
Analyzes code complexity using Tree-sitter AST parsing with LLM enhancement
"""

from tree_sitter import Parser, Query, Language
from typing import Dict, List, Any, Optional, Callable
from agents.base.tools.tool_schemas import CodeFileInput, AnalysisOutput, QualityMetric
from agents.base.tools.llm_provider import get_llm_provider, LLMRequest
import logging
import os
import time
import yaml
import importlib
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


def load_language_config() -> Dict[str, Any]:
    """Load language configuration from YAML file"""
    # Look for config in the agent's configs directory first, then fallback to old path
    config_paths = [
        Path(__file__).parent.parent / "configs" / "complexity_analyzer.yaml",  # New agent-specific path
        Path("/app/config/tools/complexity_analyzer.yaml"),  # Old fallback path
    ]
    
    config_path = None
    for path in config_paths:
        if path.exists():
            config_path = path
            break
    
    if not config_path:
        raise RuntimeError(f"Configuration file not found in any of these locations: {[str(p) for p in config_paths]}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Convert parser module names to actual imported modules
        language_config = {}
        for ext, lang_conf in config['language_config'].items():
            parser_module_name = lang_conf['parser']
            try:
                # Dynamically import the parser module
                parser_module = importlib.import_module(parser_module_name)
                lang_conf['parser'] = parser_module
                language_config[ext] = lang_conf
                logger.debug(f"Loaded configuration for {lang_conf['name']} ({ext})")
            except ImportError as e:
                logger.warning(f"Failed to import {parser_module_name}: {e}")
                continue
        
        return {
            'language_config': language_config,
            'complexity_thresholds': config.get('complexity_thresholds', {}),
            'parser_modules': config.get('parser_modules', {}),
            'language_mapping': config.get('language_mapping', {}),
            'extension_to_language': config.get('extension_to_language', {})
        }
    except Exception as e:
        logger.error(f"Failed to load language configuration: {e}")
        
        raise RuntimeError(f"Critical error: Unable to load complexity analyzer configuration from {config_path}: {e}")


# Load configuration at module level
CONFIG = load_language_config()
LANGUAGE_CONFIG = CONFIG['language_config']
COMPLEXITY_THRESHOLDS = CONFIG['complexity_thresholds']
LANGUAGE_MAPPING = CONFIG['language_mapping']
EXTENSION_TO_LANGUAGE = CONFIG['extension_to_language']


class ComplexityAnalyzer:
    """Real Tree-sitter based complexity analyzer"""
    
    def __init__(self):
        self.parsers = {}
        self._initialize_parsers()
    
    @property
    def LANGUAGE_PARSERS(self) -> Dict[str, str]:
        """Return mapping of languages to their status"""
        return {config['name']: 'available' if ext in self.parsers else 'failed' 
                for ext, config in LANGUAGE_CONFIG.items()}
    
    def _initialize_parsers(self):
        """Initialize Tree-sitter parsers for supported languages"""
        for ext, config in LANGUAGE_CONFIG.items():
            try:
                # Get the language capsule from the tree-sitter language module
                parser_module = config['parser']
                language_capsule = None
                
                # Different Tree-sitter modules have different API patterns
                if hasattr(parser_module, 'language') and callable(parser_module.language):
                    # Pattern: module.language() -> returns language capsule
                    language_capsule = parser_module.language()
                elif hasattr(parser_module, 'Language'):
                    # Pattern: module.Language -> class, need to instantiate
                    language_capsule = parser_module.Language()
                elif hasattr(parser_module, 'LANGUAGE'):
                    # Pattern: module.LANGUAGE -> direct language capsule
                    language_capsule = parser_module.LANGUAGE
                elif config['name'] == 'typescript' and hasattr(parser_module, 'language_typescript'):
                    # Special case: TypeScript modules often have language_typescript() and language_tsx()
                    language_capsule = parser_module.language_typescript()
                else:
                    # For debugging: log available attributes
                    attrs = [attr for attr in dir(parser_module) if not attr.startswith('_')]
                    logger.debug(f"Available attributes in {config['name']}: {attrs}")
                    
                    # Try to find any callable that might return a language
                    for attr_name in attrs:
                        attr = getattr(parser_module, attr_name)
                        if callable(attr):
                            try:
                                result = attr()
                                # Check if it looks like a language capsule (basic type check)
                                if result is not None and hasattr(result, '__class__'):
                                    # Simple test - try to create a Language object
                                    test_lang = Language(result)
                                    language_capsule = result
                                    logger.debug(f"Found language capsule via {attr_name}() for {config['name']}")
                                    break
                            except Exception as test_error:
                                logger.debug(f"Failed to test {attr_name}() for {config['name']}: {test_error}")
                                continue
                
                if language_capsule is None:
                    logger.warning(f"Could not find language capsule in module {config['name']}")
                    continue
                
                # Create Language object from capsule
                language = Language(language_capsule)
                
                # Create parser and set language
                parser = Parser()
                parser.language = language
                
                self.parsers[ext] = {
                    'parser': parser,
                    'language': language,
                    'config': config
                }
                logger.info(f"Successfully initialized Tree-sitter parser for {config['name']}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize parser for {config['name']} ({ext}): {e}")
                # Continue with other parsers
                continue
    
    def get_file_extension(self, file_path: str) -> str:
        """Get normalized file extension"""
        return Path(file_path).suffix.lower()
    
    def is_supported_language(self, file_path: str) -> bool:
        """Check if file language is supported"""
        ext = self.get_file_extension(file_path)
        return ext in self.parsers
    
    def parse_code(self, code: str, file_path: str) -> Optional[Any]:
        """Parse code using appropriate Tree-sitter parser"""
        ext = self.get_file_extension(file_path)
        if ext not in self.parsers:
            logger.warning(f"Unsupported file extension: {ext}")
            return None
        
        try:
            parser = self.parsers[ext]['parser']
            tree = parser.parse(bytes(code, 'utf8'))
            return tree
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def calculate_cyclomatic_complexity(self, tree, file_path: str) -> int:
        """Calculate cyclomatic complexity using Tree-sitter AST"""
        ext = self.get_file_extension(file_path)
        if ext not in self.parsers:
            return 0
        
        config = self.parsers[ext]['config']
        language = self.parsers[ext]['language']
        
        # Start with complexity of 1 (base path)
        complexity = 1
        
        # Define decision point queries
        decision_queries = []
        for query_name in ['if_query', 'while_query', 'for_query', 'try_query', 'switch_query', 'match_query']:
            if query_name in config:
                decision_queries.append(config[query_name])
        
        # Count decision points
        root_node = tree.root_node
        for query_text in decision_queries:
            try:
                # Create query using the language object
                query = Query(language, query_text)
                matches = query.matches(root_node)
                complexity += len(matches)
            except Exception as e:
                logger.debug(f"Query failed for {query_text}: {e}")
        
        return complexity
    
    def calculate_cognitive_complexity(self, tree, file_path: str) -> int:
        """Calculate cognitive complexity (approximate)"""
        # Simplified cognitive complexity - weights nested structures more heavily
        ext = self.get_file_extension(file_path)
        if ext not in self.parsers:
            return 0
        
        complexity = 0
        root_node = tree.root_node
        
        def traverse_node(node, nesting_level=0):
            nonlocal complexity
            
            # Increment complexity based on node type and nesting level
            decision_nodes = ['if_statement', 'while_statement', 'for_statement', 
                            'switch_statement', 'try_statement', 'match_statement']
            
            if node.type in decision_nodes:
                # Cognitive complexity increases with nesting level
                complexity += 1 + nesting_level
                nesting_level += 1
            
            # Recursively traverse child nodes
            for child in node.children:
                traverse_node(child, nesting_level)
        
        traverse_node(root_node)
        return complexity
    
    def calculate_nesting_depth(self, tree) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0
        
        def traverse_node(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            # Increment depth for block structures
            block_nodes = ['if_statement', 'while_statement', 'for_statement', 
                          'function_definition', 'class_definition', 'try_statement']
            
            next_depth = current_depth + 1 if node.type in block_nodes else current_depth
            
            for child in node.children:
                traverse_node(child, next_depth)
        
        traverse_node(tree.root_node)
        return max_depth
    
    def count_lines_of_code(self, code: str) -> Dict[str, int]:
        """Count different types of lines"""
        lines = code.split('\n')
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//', '/*', '*', '*/')))
        code_lines = total_lines - blank_lines - comment_lines
        
        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'blank_lines': blank_lines,
            'comment_lines': comment_lines
        }
    
    def analyze_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """
        Simple interface to analyze code complexity
        
        Args:
            code: Source code to analyze
            language: Programming language name
            
        Returns:
            Dictionary with complexity metrics
        """
        # Use configuration-based language mapping
        ext = LANGUAGE_MAPPING.get(language.lower())
        if not ext:
            return {
                'error': f'Unsupported language: {language}',
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'max_nesting_depth': 0,
                'total_functions': 0
            }
        
        # Create a dummy file path with the correct extension
        dummy_path = f"temp{ext}"
        
        # Parse the code
        tree = self.parse_code(code, dummy_path)
        if not tree:
            return {
                'error': 'Failed to parse code',
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'max_nesting_depth': 0,
                'total_functions': 0
            }
        
        # Calculate metrics
        cyclomatic = self.calculate_cyclomatic_complexity(tree, dummy_path)
        cognitive = self.calculate_cognitive_complexity(tree, dummy_path)
        nesting = self.calculate_nesting_depth(tree)
        functions = self.extract_functions(tree, dummy_path)
        
        return {
            'cyclomatic_complexity': cyclomatic,
            'cognitive_complexity': cognitive,
            'max_nesting_depth': nesting,
            'total_functions': len(functions),
            'functions': functions
        }

    def extract_functions(self, tree, file_path: str) -> List[Dict[str, Any]]:
        """Extract function information from AST"""
        ext = self.get_file_extension(file_path)
        if ext not in self.parsers:
            return []
        
        config = self.parsers[ext]['config']
        language = self.parsers[ext]['language']
        
        functions = []
        
        if 'function_query' in config:
            try:
                query = Query(language, config['function_query'])
                matches = query.matches(tree.root_node)
                
                for match in matches:
                    for capture in match.captures:
                        node = capture.node
                        function_info = {
                            'name': node.text.decode('utf8'),
                            'start_line': node.start_point[0] + 1,
                            'end_line': node.end_point[0] + 1,
                            'lines': node.end_point[0] - node.start_point[0] + 1
                        }
                        functions.append(function_info)
            except Exception as e:
                logger.debug(f"Function extraction failed: {e}")
        
        return functions


# Global analyzer instance
analyzer = ComplexityAnalyzer()


def complexity_analyzer_tool(file_input: CodeFileInput) -> AnalysisOutput:
    """
    Analyze code complexity metrics using Tree-sitter parsing
    
    Args:
        file_input: Code file to analyze for complexity
        
    Returns:
        Analysis output with complexity metrics
    """
    start_time = time.time()
    findings = []
    
    try:
        # Check if language is supported
        if not analyzer.is_supported_language(file_input.file_path):
            ext = analyzer.get_file_extension(file_input.file_path)
            return AnalysisOutput(
                file_path=file_input.file_path,
                findings=[{
                    'type': 'warning',
                    'message': f'Unsupported file type: {ext}',
                    'line': 1,
                    'severity': 'low'
                }],
                metrics={'supported': False},
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"tool": "complexity_analyzer", "version": "1.0.0", "error": "unsupported_language"}
            )
        
        # Read code content
        if file_input.content:
            code = file_input.content
        else:
            # Try to read from file path if content not provided
            try:
                with open(file_input.file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_input.file_path}: {e}")
                return AnalysisOutput(
                    file_path=file_input.file_path,
                    findings=[{
                        'type': 'error',
                        'message': f'Failed to read file: {str(e)}',
                        'line': 1,
                        'severity': 'high'
                    }],
                    metrics={'error': True},
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    metadata={"tool": "complexity_analyzer", "version": "1.0.0", "error": "file_read_failed"}
                )
        
        # Parse code with Tree-sitter
        tree = analyzer.parse_code(code, file_input.file_path)
        if not tree:
            return AnalysisOutput(
                file_path=file_input.file_path,
                findings=[{
                    'type': 'error',
                    'message': 'Failed to parse code with Tree-sitter',
                    'line': 1,
                    'severity': 'high'
                }],
                metrics={'parse_error': True},
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"tool": "complexity_analyzer", "version": "1.0.0", "error": "parse_failed"}
            )
        
        # Calculate complexity metrics
        cyclomatic_complexity = analyzer.calculate_cyclomatic_complexity(tree, file_input.file_path)
        cognitive_complexity = analyzer.calculate_cognitive_complexity(tree, file_input.file_path)
        nesting_depth = analyzer.calculate_nesting_depth(tree)
        line_counts = analyzer.count_lines_of_code(code)
        functions = analyzer.extract_functions(tree, file_input.file_path)
        
        # Generate findings based on complexity thresholds
        cyclomatic_thresholds = COMPLEXITY_THRESHOLDS.get('cyclomatic_complexity', {})
        if cyclomatic_complexity > cyclomatic_thresholds.get('medium', 10):
            severity = 'high' if cyclomatic_complexity > cyclomatic_thresholds.get('high', 20) else 'medium'
            findings.append({
                'type': 'complexity_issue',
                'message': f'High cyclomatic complexity: {cyclomatic_complexity} (threshold: {cyclomatic_thresholds.get("medium", 10)})',
                'line': 1,
                'severity': severity,
                'suggestion': 'Consider breaking down complex logic into smaller functions'
            })
        
        cognitive_thresholds = COMPLEXITY_THRESHOLDS.get('cognitive_complexity', {})
        if cognitive_complexity > cognitive_thresholds.get('medium', 15):
            severity = 'high' if cognitive_complexity > cognitive_thresholds.get('high', 25) else 'medium'
            findings.append({
                'type': 'complexity_issue',
                'message': f'High cognitive complexity: {cognitive_complexity} (threshold: {cognitive_thresholds.get("medium", 15)})',
                'line': 1,
                'severity': severity,
                'suggestion': 'Reduce nesting and simplify control flow'
            })
        
        nesting_thresholds = COMPLEXITY_THRESHOLDS.get('nesting_depth', {})
        if nesting_depth > nesting_thresholds.get('medium', 4):
            findings.append({
                'type': 'complexity_issue',
                'message': f'Deep nesting detected: {nesting_depth} levels (threshold: {nesting_thresholds.get("medium", 4)})',
                'line': 1,
                'severity': 'medium',
                'suggestion': 'Extract nested logic into separate functions'
            })
        
        # Analyze individual functions
        function_thresholds = COMPLEXITY_THRESHOLDS.get('function_length', {})
        for func in functions:
            medium_threshold = function_thresholds.get('medium', 50)
            high_threshold = function_thresholds.get('high', 100)
            if func['lines'] > medium_threshold:
                severity = 'high' if func['lines'] > high_threshold else 'medium'
                findings.append({
                    'type': 'function_length',
                    'message': f'Long function "{func["name"]}": {func["lines"]} lines (threshold: {medium_threshold})',
                    'line': func['start_line'],
                    'severity': severity,
                    'suggestion': f'Consider breaking down function "{func["name"]}" into smaller functions'
                })
        
        # Calculate confidence based on parsing success and language support
        confidence = 0.95 if tree and len(findings) >= 0 else 0.5
        
        metrics = {
            "cyclomatic_complexity": cyclomatic_complexity,
            "cognitive_complexity": cognitive_complexity,
            "nesting_depth": nesting_depth,
            "function_count": len(functions),
            **line_counts,
            "supported": True
        }
        
        processing_time = time.time() - start_time
        
        logger.info(f"Analyzed complexity in {file_input.file_path}: "
                   f"CC={cyclomatic_complexity}, CogC={cognitive_complexity}, "
                   f"depth={nesting_depth}, functions={len(functions)}")
        
        return AnalysisOutput(
            file_path=file_input.file_path,
            findings=findings,
            metrics=metrics,
            confidence=confidence,
            processing_time=processing_time,
            metadata={
                "tool": "complexity_analyzer", 
                "version": "1.0.0",
                "language": analyzer.get_file_extension(file_input.file_path),
                "tree_sitter": True,
                "functions_analyzed": len(functions)
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in complexity analysis: {e}")
        return AnalysisOutput(
            file_path=file_input.file_path,
            findings=[{
                'type': 'error',
                'message': f'Analysis failed: {str(e)}',
                'line': 1,
                'severity': 'high'
            }],
            metrics={'error': True},
            confidence=0.0,
            processing_time=time.time() - start_time,
            metadata={"tool": "complexity_analyzer", "version": "1.0.0", "error": "unexpected_error"}
        )


# Create a simple function interface for now (will integrate with Google Cloud AI Platform later)
def ComplexityAnalyzerTool(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """
    Complexity analyzer tool interface
    
    Args:
        file_path: Path to the file to analyze
        content: Optional file content (if not provided, will read from file_path)
        
    Returns:
        Analysis results dictionary
    """
    # Import here to avoid circular imports
    from agents.base.tools.tool_schemas import CodeFileInput, AnalysisLanguage
    
    # Use configuration-based extension to language mapping
    ext = analyzer.get_file_extension(file_path)
    language_name = EXTENSION_TO_LANGUAGE.get(ext, 'PYTHON')  # Default to Python
    
    # Get the AnalysisLanguage enum value
    language = getattr(AnalysisLanguage, language_name, AnalysisLanguage.PYTHON)
    
    file_input = CodeFileInput(file_path=file_path, content=content or "", language=language)
    result = complexity_analyzer_tool(file_input)
    
    return {
        "file_path": result.file_path,
        "findings": result.findings,
        "metrics": result.metrics,
        "confidence": result.confidence,
        "processing_time": result.processing_time,
        "metadata": result.metadata
    }


async def enhanced_complexity_analysis(file_input: CodeFileInput, include_llm_insights: bool = True) -> AnalysisOutput:
    """
    Enhanced complexity analysis with LLM-powered insights
    
    Args:
        file_input: Input file information
        include_llm_insights: Whether to include LLM-generated insights
        
    Returns:
        Enhanced analysis results with LLM recommendations
    """
    start_time = time.time()
    
    try:
        # First, perform standard Tree-sitter analysis
        base_result = complexity_analyzer_tool(file_input)
        
        if not include_llm_insights or not file_input.content:
            return base_result
        
        # Get LLM provider for enhanced analysis
        llm_provider = get_llm_provider()
        
        # Create context from base analysis
        analysis_context = {
            "metrics": base_result.metrics,
            "high_complexity_functions": [
                finding for finding in base_result.findings 
                if finding.get('severity') in ['high', 'critical']
            ],
            "language": file_input.language.value,
            "file_path": file_input.file_path
        }
        
        # Generate LLM insights
        llm_analysis = await llm_provider.analyze_code_patterns(
            code=file_input.content,
            language=file_input.language.value,
            analysis_type="complexity"
        )
        
        # Enhance findings with LLM insights
        enhanced_findings = base_result.findings.copy()
        
        # Add LLM-generated insights as findings
        if llm_analysis.get("insights"):
            for insight in llm_analysis["insights"]:
                enhanced_findings.append({
                    'type': 'llm_insight',
                    'message': insight,
                    'line': 1,  # General insight
                    'severity': 'info',
                    'source': 'llm',
                    'confidence': llm_analysis.get("confidence", 0.8)
                })
        
        # Add LLM recommendations
        if llm_analysis.get("recommendations"):
            for recommendation in llm_analysis["recommendations"]:
                enhanced_findings.append({
                    'type': 'llm_recommendation',
                    'message': recommendation,
                    'line': 1,  # General recommendation
                    'severity': 'suggestion',
                    'source': 'llm',
                    'confidence': llm_analysis.get("confidence", 0.8)
                })
        
        # Enhanced metrics
        enhanced_metrics = base_result.metrics.copy()
        enhanced_metrics.update({
            "llm_analysis_confidence": llm_analysis.get("confidence", 0.0),
            "llm_provider": llm_analysis.get("provider", "unknown"),
            "llm_insights_count": len(llm_analysis.get("insights", [])),
            "llm_recommendations_count": len(llm_analysis.get("recommendations", []))
        })
        
        # Enhanced metadata
        enhanced_metadata = base_result.metadata.copy() if base_result.metadata else {}
        enhanced_metadata.update({
            "llm_enhanced": True,
            "llm_analysis": {
                "provider": llm_analysis.get("provider"),
                "confidence": llm_analysis.get("confidence"),
                "analysis_type": "complexity"
            }
        })
        
        processing_time = time.time() - start_time
        
        return AnalysisOutput(
            file_path=file_input.file_path,
            findings=enhanced_findings,
            metrics=enhanced_metrics,
            confidence=min(base_result.confidence + (llm_analysis.get("confidence", 0.0) * 0.2), 1.0),
            processing_time=processing_time,
            metadata=enhanced_metadata
        )
        
    except Exception as e:
        logger.error(f"Enhanced complexity analysis failed: {e}")
        # Fallback to base analysis
        base_result = complexity_analyzer_tool(file_input)
        base_result.metadata = base_result.metadata or {}
        base_result.metadata["llm_enhancement_failed"] = str(e)
        return base_result


def EnhancedComplexityAnalyzerTool(file_path: str, content: Optional[str] = None, include_llm_insights: bool = True) -> Dict[str, Any]:
    """
    Enhanced complexity analyzer tool interface with LLM integration
    
    Args:
        file_path: Path to the file to analyze
        content: Optional file content (if not provided, will read from file_path)
        include_llm_insights: Whether to include LLM-generated insights
        
    Returns:
        Enhanced analysis results dictionary
    """
    # Import here to avoid circular imports
    from agents.base.tools.tool_schemas import CodeFileInput, AnalysisLanguage
    
    # Use configuration-based extension to language mapping
    ext = analyzer.get_file_extension(file_path)
    language_name = EXTENSION_TO_LANGUAGE.get(ext, 'PYTHON')  # Default to Python
    
    # Get the AnalysisLanguage enum value
    language = getattr(AnalysisLanguage, language_name, AnalysisLanguage.PYTHON)
    
    file_input = CodeFileInput(file_path=file_path, content=content or "", language=language)
    
    # Run async analysis
    result = asyncio.run(enhanced_complexity_analysis(file_input, include_llm_insights))
    
    return {
        "file_path": result.file_path,
        "findings": result.findings,
        "metrics": result.metrics,
        "confidence": result.confidence,
        "processing_time": result.processing_time,
        "metadata": result.metadata
    }