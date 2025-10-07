"""
Code Analysis Toolset for Google ADK
Provides tree-sitter based code parsing and analysis capabilities
"""

from google.cloud.aiplatform.adk.toolsets import BaseToolset
from google.cloud.aiplatform.adk.tools import FunctionTool
from typing import Any, Dict, List, Optional
import tree_sitter_python as tsp
import tree_sitter_javascript as tsjs
import tree_sitter_java as tsjava
import tree_sitter_go as tsgo
import tree_sitter_rust as tsrust
import tree_sitter
import logging

logger = logging.getLogger(__name__)


class CodeAnalysisToolset(BaseToolset):
    """Toolset for comprehensive code analysis using tree-sitter parsing"""
    
    def __init__(self):
        super().__init__()
        self._setup_parsers()
        
        # Register all analysis tools
        self.tools = [
            FunctionTool(
                name="parse_code_structure",
                description="Parse code file and extract structural information (classes, functions, imports)",
                function=self.parse_code_structure
            ),
            FunctionTool(
                name="analyze_complexity",
                description="Analyze code complexity metrics (cyclomatic, cognitive, nesting depth)",
                function=self.analyze_complexity
            ),
            FunctionTool(
                name="detect_code_patterns",
                description="Detect common code patterns, anti-patterns, and design patterns",
                function=self.detect_code_patterns
            ),
            FunctionTool(
                name="assess_maintainability",
                description="Assess code maintainability factors (coupling, cohesion, readability)",
                function=self.assess_maintainability
            ),
            FunctionTool(
                name="analyze_dependencies",
                description="Analyze import dependencies and dependency relationships",
                function=self.analyze_dependencies
            ),
            FunctionTool(
                name="extract_documentation",
                description="Extract and analyze code documentation (docstrings, comments)",
                function=self.extract_documentation
            )
        ]
    
    def _setup_parsers(self):
        """Setup tree-sitter parsers for supported languages"""
        self.parsers = {}
        
        # Python parser
        python_language = tree_sitter.Language(tsp.language(), "python")
        python_parser = tree_sitter.Parser()
        python_parser.set_language(python_language)
        self.parsers['python'] = python_parser
        
        # JavaScript parser
        js_language = tree_sitter.Language(tsjs.language(), "javascript")
        js_parser = tree_sitter.Parser()
        js_parser.set_language(js_language)
        self.parsers['javascript'] = js_parser
        self.parsers['typescript'] = js_parser  # TypeScript uses JS parser
        
        # Java parser
        java_language = tree_sitter.Language(tsjava.language(), "java")
        java_parser = tree_sitter.Parser()
        java_parser.set_language(java_language)
        self.parsers['java'] = java_parser
        
        # Go parser
        go_language = tree_sitter.Language(tsgo.language(), "go")
        go_parser = tree_sitter.Parser()
        go_parser.set_language(go_language)
        self.parsers['go'] = go_parser
        
        # Rust parser
        rust_language = tree_sitter.Language(tsrust.language(), "rust")
        rust_parser = tree_sitter.Parser()
        rust_parser.set_language(rust_language)
        self.parsers['rust'] = rust_parser
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        
        return 'unknown'
    
    def parse_code_structure(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        Parse code structure and extract key components
        
        Args:
            file_path: Path to the code file
            code_content: Content of the code file
            
        Returns:
            Dictionary containing structural information
        """
        language = self._detect_language(file_path)
        
        if language not in self.parsers:
            return {
                "error": f"Unsupported language: {language}",
                "file_path": file_path
            }
        
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code_content, "utf8"))
            root_node = tree.root_node
            
            result = {
                "file_path": file_path,
                "language": language,
                "classes": self._extract_classes(root_node, language),
                "functions": self._extract_functions(root_node, language),
                "imports": self._extract_imports(root_node, language),
                "constants": self._extract_constants(root_node, language),
                "line_count": len(code_content.split('\n')),
                "parse_errors": [str(error) for error in tree.root_node.children if error.type == "ERROR"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing code structure: {str(e)}")
            return {
                "error": str(e),
                "file_path": file_path
            }
    
    def analyze_complexity(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        Analyze code complexity metrics
        
        Args:
            file_path: Path to the code file
            code_content: Content of the code file
            
        Returns:
            Dictionary containing complexity metrics
        """
        structure = self.parse_code_structure(file_path, code_content)
        
        if "error" in structure:
            return structure
        
        try:
            complexity_metrics = {
                "file_path": file_path,
                "cyclomatic_complexity": self._calculate_cyclomatic_complexity(structure),
                "cognitive_complexity": self._calculate_cognitive_complexity(code_content),
                "nesting_depth": self._calculate_nesting_depth(code_content),
                "function_complexity": self._analyze_function_complexity(structure),
                "class_complexity": self._analyze_class_complexity(structure),
                "overall_rating": "low"  # Will be calculated based on metrics
            }
            
            # Calculate overall complexity rating
            complexity_metrics["overall_rating"] = self._calculate_overall_complexity_rating(complexity_metrics)
            
            return complexity_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing complexity: {str(e)}")
            return {"error": str(e), "file_path": file_path}
    
    def detect_code_patterns(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        Detect code patterns, anti-patterns, and design patterns
        
        Args:
            file_path: Path to the code file
            code_content: Content of the code file
            
        Returns:
            Dictionary containing detected patterns
        """
        structure = self.parse_code_structure(file_path, code_content)
        
        if "error" in structure:
            return structure
        
        try:
            patterns = {
                "file_path": file_path,
                "design_patterns": self._detect_design_patterns(structure, code_content),
                "anti_patterns": self._detect_anti_patterns(structure, code_content),
                "code_smells": self._detect_code_smells(structure, code_content),
                "best_practices": self._check_best_practices(structure, code_content),
                "refactoring_suggestions": []
            }
            
            # Generate refactoring suggestions based on detected issues
            patterns["refactoring_suggestions"] = self._generate_refactoring_suggestions(patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {str(e)}")
            return {"error": str(e), "file_path": file_path}
    
    def assess_maintainability(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        Assess code maintainability factors
        
        Args:
            file_path: Path to the code file
            code_content: Content of the code file
            
        Returns:
            Dictionary containing maintainability assessment
        """
        try:
            structure = self.parse_code_structure(file_path, code_content)
            complexity = self.analyze_complexity(file_path, code_content)
            patterns = self.detect_code_patterns(file_path, code_content)
            
            maintainability = {
                "file_path": file_path,
                "readability_score": self._calculate_readability_score(code_content),
                "modularity_score": self._calculate_modularity_score(structure),
                "testability_score": self._calculate_testability_score(structure, code_content),
                "documentation_score": self._calculate_documentation_score(structure, code_content),
                "coupling_assessment": self._assess_coupling(structure),
                "cohesion_assessment": self._assess_cohesion(structure),
                "overall_maintainability": "medium"  # Will be calculated
            }
            
            # Calculate overall maintainability score
            maintainability["overall_maintainability"] = self._calculate_overall_maintainability(maintainability)
            
            return maintainability
            
        except Exception as e:
            logger.error(f"Error assessing maintainability: {str(e)}")
            return {"error": str(e), "file_path": file_path}
    
    def analyze_dependencies(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        Analyze import dependencies and relationships
        
        Args:
            file_path: Path to the code file
            code_content: Content of the code file
            
        Returns:
            Dictionary containing dependency analysis
        """
        structure = self.parse_code_structure(file_path, code_content)
        
        if "error" in structure:
            return structure
        
        try:
            dependencies = {
                "file_path": file_path,
                "imports": structure.get("imports", []),
                "internal_dependencies": [],
                "external_dependencies": [],
                "circular_dependencies": [],
                "unused_imports": [],
                "dependency_graph": {},
                "recommendations": []
            }
            
            # Categorize dependencies
            dependencies.update(self._categorize_dependencies(dependencies["imports"]))
            
            # Check for potential issues
            dependencies["circular_dependencies"] = self._detect_circular_dependencies(file_path, dependencies)
            dependencies["unused_imports"] = self._detect_unused_imports(code_content, dependencies["imports"])
            
            # Generate recommendations
            dependencies["recommendations"] = self._generate_dependency_recommendations(dependencies)
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {str(e)}")
            return {"error": str(e), "file_path": file_path}
    
    def extract_documentation(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        Extract and analyze code documentation
        
        Args:
            file_path: Path to the code file
            code_content: Content of the code file
            
        Returns:
            Dictionary containing documentation analysis
        """
        structure = self.parse_code_structure(file_path, code_content)
        
        if "error" in structure:
            return structure
        
        try:
            documentation = {
                "file_path": file_path,
                "module_docstring": self._extract_module_docstring(code_content),
                "function_docstrings": self._extract_function_docstrings(structure, code_content),
                "class_docstrings": self._extract_class_docstrings(structure, code_content),
                "inline_comments": self._extract_inline_comments(code_content),
                "todo_comments": self._extract_todo_comments(code_content),
                "documentation_coverage": 0.0,
                "quality_assessment": {},
                "improvement_suggestions": []
            }
            
            # Calculate documentation coverage
            documentation["documentation_coverage"] = self._calculate_documentation_coverage(documentation)
            
            # Assess documentation quality
            documentation["quality_assessment"] = self._assess_documentation_quality(documentation)
            
            # Generate improvement suggestions
            documentation["improvement_suggestions"] = self._generate_documentation_suggestions(documentation)
            
            return documentation
            
        except Exception as e:
            logger.error(f"Error extracting documentation: {str(e)}")
            return {"error": str(e), "file_path": file_path}
    
    # Helper methods (simplified implementations - would be more comprehensive in production)
    
    def _extract_classes(self, root_node, language: str) -> List[Dict[str, Any]]:
        """Extract class definitions from AST"""
        # Simplified implementation
        return []
    
    def _extract_functions(self, root_node, language: str) -> List[Dict[str, Any]]:
        """Extract function definitions from AST"""
        # Simplified implementation
        return []
    
    def _extract_imports(self, root_node, language: str) -> List[Dict[str, Any]]:
        """Extract import statements from AST"""
        # Simplified implementation
        return []
    
    def _extract_constants(self, root_node, language: str) -> List[Dict[str, Any]]:
        """Extract constant definitions from AST"""
        # Simplified implementation
        return []
    
    def _calculate_cyclomatic_complexity(self, structure: Dict) -> int:
        """Calculate cyclomatic complexity"""
        # Simplified implementation
        return len(structure.get("functions", [])) + 1
    
    def _calculate_cognitive_complexity(self, code_content: str) -> int:
        """Calculate cognitive complexity"""
        # Simplified implementation
        return code_content.count("if") + code_content.count("while") + code_content.count("for")
    
    def _calculate_nesting_depth(self, code_content: str) -> int:
        """Calculate maximum nesting depth"""
        # Simplified implementation
        max_depth = 0
        current_depth = 0
        for line in code_content.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith(('if', 'for', 'while', 'with', 'try', 'def', 'class')):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif line.strip() == '' or not line.startswith(' '):
                current_depth = 0
        return max_depth
    
    def _analyze_function_complexity(self, structure: Dict) -> List[Dict]:
        """Analyze complexity of individual functions"""
        # Simplified implementation
        return []
    
    def _analyze_class_complexity(self, structure: Dict) -> List[Dict]:
        """Analyze complexity of individual classes"""
        # Simplified implementation
        return []
    
    def _calculate_overall_complexity_rating(self, metrics: Dict) -> str:
        """Calculate overall complexity rating"""
        cyclomatic = metrics.get("cyclomatic_complexity", 0)
        cognitive = metrics.get("cognitive_complexity", 0)
        
        if cyclomatic > 15 or cognitive > 20:
            return "high"
        elif cyclomatic > 10 or cognitive > 15:
            return "medium"
        else:
            return "low"
    
    def _detect_design_patterns(self, structure: Dict, code_content: str) -> List[str]:
        """Detect design patterns in code"""
        # Simplified implementation
        patterns = []
        if "factory" in code_content.lower():
            patterns.append("Factory Pattern")
        if "singleton" in code_content.lower():
            patterns.append("Singleton Pattern")
        return patterns
    
    def _detect_anti_patterns(self, structure: Dict, code_content: str) -> List[str]:
        """Detect anti-patterns in code"""
        # Simplified implementation
        anti_patterns = []
        if "god" in code_content.lower():
            anti_patterns.append("God Object")
        return anti_patterns
    
    def _detect_code_smells(self, structure: Dict, code_content: str) -> List[str]:
        """Detect code smells"""
        # Simplified implementation
        smells = []
        if len(code_content.split('\n')) > 500:
            smells.append("Long File")
        return smells
    
    def _check_best_practices(self, structure: Dict, code_content: str) -> List[str]:
        """Check adherence to best practices"""
        # Simplified implementation
        practices = []
        if '"""' in code_content:
            practices.append("Uses docstrings")
        return practices
    
    def _generate_refactoring_suggestions(self, patterns: Dict) -> List[str]:
        """Generate refactoring suggestions"""
        # Simplified implementation
        return ["Consider breaking down large functions", "Add more comprehensive documentation"]
    
    def _calculate_readability_score(self, code_content: str) -> float:
        """Calculate readability score"""
        # Simplified implementation
        lines = code_content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        avg_line_length = sum(len(line) for line in non_empty_lines) / max(len(non_empty_lines), 1)
        
        if avg_line_length < 80:
            return 0.8
        elif avg_line_length < 120:
            return 0.6
        else:
            return 0.4
    
    def _calculate_modularity_score(self, structure: Dict) -> float:
        """Calculate modularity score"""
        # Simplified implementation
        num_functions = len(structure.get("functions", []))
        num_classes = len(structure.get("classes", []))
        
        if num_functions + num_classes > 0:
            return min(1.0, (num_functions + num_classes) / 10)
        return 0.0
    
    def _calculate_testability_score(self, structure: Dict, code_content: str) -> float:
        """Calculate testability score"""
        # Simplified implementation
        if "test" in code_content.lower():
            return 0.8
        return 0.5
    
    def _calculate_documentation_score(self, structure: Dict, code_content: str) -> float:
        """Calculate documentation score"""
        # Simplified implementation
        docstring_count = code_content.count('"""') + code_content.count("'''")
        comment_count = code_content.count('#')
        
        total_elements = len(structure.get("functions", [])) + len(structure.get("classes", []))
        if total_elements > 0:
            return min(1.0, (docstring_count + comment_count * 0.5) / total_elements)
        return 0.0
    
    def _assess_coupling(self, structure: Dict) -> str:
        """Assess coupling level"""
        # Simplified implementation
        import_count = len(structure.get("imports", []))
        if import_count > 20:
            return "high"
        elif import_count > 10:
            return "medium"
        else:
            return "low"
    
    def _assess_cohesion(self, structure: Dict) -> str:
        """Assess cohesion level"""
        # Simplified implementation
        return "medium"
    
    def _calculate_overall_maintainability(self, maintainability: Dict) -> str:
        """Calculate overall maintainability score"""
        scores = [
            maintainability.get("readability_score", 0),
            maintainability.get("modularity_score", 0),
            maintainability.get("testability_score", 0),
            maintainability.get("documentation_score", 0)
        ]
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score > 0.7:
            return "high"
        elif avg_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _categorize_dependencies(self, imports: List) -> Dict:
        """Categorize dependencies as internal vs external"""
        # Simplified implementation
        return {
            "internal_dependencies": [],
            "external_dependencies": imports
        }
    
    def _detect_circular_dependencies(self, file_path: str, dependencies: Dict) -> List[str]:
        """Detect circular dependencies"""
        # Simplified implementation
        return []
    
    def _detect_unused_imports(self, code_content: str, imports: List) -> List[str]:
        """Detect unused imports"""
        # Simplified implementation
        return []
    
    def _generate_dependency_recommendations(self, dependencies: Dict) -> List[str]:
        """Generate dependency recommendations"""
        # Simplified implementation
        return ["Consider reducing external dependencies", "Group related imports"]
    
    def _extract_module_docstring(self, code_content: str) -> Optional[str]:
        """Extract module-level docstring"""
        # Simplified implementation
        lines = code_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('"""'):
                # Find closing docstring
                for j in range(i + 1, len(lines)):
                    if '"""' in lines[j]:
                        return '\n'.join(lines[i:j+1])
        return None
    
    def _extract_function_docstrings(self, structure: Dict, code_content: str) -> List[Dict]:
        """Extract function docstrings"""
        # Simplified implementation
        return []
    
    def _extract_class_docstrings(self, structure: Dict, code_content: str) -> List[Dict]:
        """Extract class docstrings"""
        # Simplified implementation
        return []
    
    def _extract_inline_comments(self, code_content: str) -> List[str]:
        """Extract inline comments"""
        # Simplified implementation
        comments = []
        for line in code_content.split('\n'):
            if '#' in line:
                comment = line.split('#', 1)[1].strip()
                if comment:
                    comments.append(comment)
        return comments
    
    def _extract_todo_comments(self, code_content: str) -> List[str]:
        """Extract TODO comments"""
        # Simplified implementation
        todos = []
        for line in code_content.split('\n'):
            if 'TODO' in line.upper():
                todos.append(line.strip())
        return todos
    
    def _calculate_documentation_coverage(self, documentation: Dict) -> float:
        """Calculate documentation coverage percentage"""
        # Simplified implementation
        total_docstrings = len(documentation.get("function_docstrings", [])) + len(documentation.get("class_docstrings", []))
        if documentation.get("module_docstring"):
            total_docstrings += 1
        
        # This is a simplified calculation
        return min(1.0, total_docstrings / 10)
    
    def _assess_documentation_quality(self, documentation: Dict) -> Dict:
        """Assess documentation quality"""
        # Simplified implementation
        return {
            "completeness": "medium",
            "clarity": "medium",
            "usefulness": "medium"
        }
    
    def _generate_documentation_suggestions(self, documentation: Dict) -> List[str]:
        """Generate documentation improvement suggestions"""
        # Simplified implementation
        suggestions = []
        if not documentation.get("module_docstring"):
            suggestions.append("Add module-level docstring")
        if documentation.get("documentation_coverage", 0) < 0.5:
            suggestions.append("Increase documentation coverage")
        return suggestions