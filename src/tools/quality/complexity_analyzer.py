"""
Complexity Analyzer FunctionTool
Analyzes code complexity using Tree-sitter AST parsing
"""

from tree_sitter import Parser, Query, Language
from typing import Dict, List, Any, Optional, Callable
from ..base.tool_schemas import CodeFileInput, AnalysisOutput, QualityMetric
import logging
import os
import time
import yaml
import importlib
from pathlib import Path

logger = logging.getLogger(__name__)


def load_language_config() -> Dict[str, Any]:
    """Load language configuration from YAML file"""
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "tools" / "complexity_analyzer.yaml"
    
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
                if hasattr(parser_module, 'language') and callable(parser_module.language):
                    language_capsule = parser_module.language()
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
                    logger.info(f"Initialized Tree-sitter parser for {config['name']}")
                else:
                    logger.warning(f"Language module {config['name']} doesn't have callable language attribute")
            except Exception as e:
                logger.warning(f"Failed to initialize parser for {ext}: {e}")
    
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
    from ..base.tool_schemas import CodeFileInput, AnalysisLanguage
    
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