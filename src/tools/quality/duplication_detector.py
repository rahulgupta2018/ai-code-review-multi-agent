"""
Duplication Detection Tool for Google ADK
Real AST-based code duplication detection across files using Tree-sitter parsing
"""

from google.cloud.aiplatform.adk.tools import FunctionTool
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import logging
import os
import yaml
from pathlib import Path
import time

# Tree-sitter imports
import tree_sitter
import tree_sitter_python as tsp
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts
import tree_sitter_java as tsjava
import tree_sitter_go as tsgo
import tree_sitter_rust as tsrust
import tree_sitter_cpp as tscpp
import tree_sitter_c_sharp as tscs

logger = logging.getLogger(__name__)


class DuplicationDetector:
    """
    AST-based code duplication detection tool using Tree-sitter parsing.
    
    Detects:
    - Exact code clones (Type 1)
    - Parameterized clones (Type 2) 
    - Near-miss clones (Type 3)
    - Semantic clones (Type 4)
    
    Supports multiple languages with configurable similarity thresholds.
    """
    
    def __init__(self):
        self.parsers = {}
        self.config = {}
        self._setup_parsers()
        self._load_configuration()
        
    def _setup_parsers(self):
        """Initialize Tree-sitter parsers for supported languages"""
        try:
            # Python parser
            python_language = tree_sitter.Language(tsp.language())
            python_parser = tree_sitter.Parser()
            python_parser.set_language(python_language)
            self.parsers['python'] = python_parser
            
            # JavaScript parser
            js_language = tree_sitter.Language(tsjs.language())
            js_parser = tree_sitter.Parser()
            js_parser.set_language(js_language)
            self.parsers['javascript'] = js_parser
            
            # TypeScript parser
            ts_language = tree_sitter.Language(tsts.language())
            ts_parser = tree_sitter.Parser()
            ts_parser.set_language(ts_language)
            self.parsers['typescript'] = ts_parser
            
            # Java parser
            java_language = tree_sitter.Language(tsjava.language())
            java_parser = tree_sitter.Parser()
            java_parser.set_language(java_language)
            self.parsers['java'] = java_parser
            
            # Go parser
            go_language = tree_sitter.Language(tsgo.language())
            go_parser = tree_sitter.Parser()
            go_parser.set_language(go_language)
            self.parsers['go'] = go_parser
            
            # Rust parser
            rust_language = tree_sitter.Language(tsrust.language())
            rust_parser = tree_sitter.Parser()
            rust_parser.set_language(rust_language)
            self.parsers['rust'] = rust_parser
            
            # C++ parser
            cpp_language = tree_sitter.Language(tscpp.language())
            cpp_parser = tree_sitter.Parser()
            cpp_parser.set_language(cpp_language)
            self.parsers['cpp'] = cpp_parser
            self.parsers['c++'] = cpp_parser
            
            # C# parser
            cs_language = tree_sitter.Language(tscs.language())
            cs_parser = tree_sitter.Parser()
            cs_parser.set_language(cs_language)
            self.parsers['csharp'] = cs_parser
            self.parsers['c#'] = cs_parser
            
            logger.info(f"Initialized Tree-sitter parsers for {len(self.parsers)} languages")
            
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter parsers: {str(e)}")
            # Continue with available parsers
    
    def _load_configuration(self):
        """Load duplication detection configuration from YAML file"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "tools" / "duplication_detector.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded duplication detector configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension using configuration"""
        file_ext = Path(file_path).suffix.lower()
        language_map = self.config.get("language_detection", {})
        return language_map.get(file_ext)
    
    def _parse_file(self, file_path: str, content: str) -> Optional[tree_sitter.Tree]:
        """Parse a file using appropriate Tree-sitter parser"""
        language = self._detect_language(file_path)
        
        if not language or language not in self.parsers:
            logger.warning(f"Unsupported language for file: {file_path}")
            return None
        
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(content, 'utf8'))
            return tree
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            return None
    
    def _extract_code_blocks(self, tree: tree_sitter.Tree, language: str) -> List[Dict]:
        """Extract code blocks (functions, classes, methods) from AST"""
        if not tree or not tree.root_node:
            return []
        
        language_config = self.config.get("language_settings", {}).get(language, {})
        function_nodes = language_config.get("function_nodes", [])
        class_nodes = language_config.get("class_nodes", [])
        block_nodes = language_config.get("block_nodes", [])
        
        all_node_types = function_nodes + class_nodes + block_nodes
        blocks = []
        
        def traverse_node(node, parent_type=""):
            if node.type in all_node_types:
                block_info = {
                    "type": node.type,
                    "parent_type": parent_type,
                    "start_point": node.start_point,
                    "end_point": node.end_point,
                    "text": node.text.decode('utf8') if node.text else "",
                    "hash": self._calculate_node_hash(node),
                    "normalized_hash": self._calculate_normalized_hash(node),
                    "structure_hash": self._calculate_structure_hash(node),
                    "token_count": self._count_tokens(node),
                    "node_count": self._count_nodes(node)
                }
                blocks.append(block_info)
                parent_type = node.type
            
            for child in node.children:
                traverse_node(child, parent_type)
        
        traverse_node(tree.root_node)
        return blocks
    
    def _calculate_node_hash(self, node: tree_sitter.Node) -> str:
        """Calculate exact hash of node text (Type 1 clones)"""
        text = node.text.decode('utf8') if node.text else ""
        return hashlib.md5(text.encode('utf8')).hexdigest()
    
    def _calculate_normalized_hash(self, node: tree_sitter.Node) -> str:
        """Calculate hash of normalized node text (Type 2 clones)"""
        text = node.text.decode('utf8') if node.text else ""
        
        # Normalize: remove whitespace, standardize variable names
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode('utf8')).hexdigest()
    
    def _calculate_structure_hash(self, node: tree_sitter.Node) -> str:
        """Calculate hash of node structure (Type 3/4 clones)"""
        structure = self._extract_structure(node)
        return hashlib.md5(structure.encode('utf8')).hexdigest()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for parameterized clone detection"""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Replace variable names with placeholder
        text = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', 'VAR', text)
        
        # Replace string literals with placeholder
        text = re.sub(r'"[^"]*"', '"STRING"', text)
        text = re.sub(r"'[^']*'", "'STRING'", text)
        
        # Replace numeric literals with placeholder
        text = re.sub(r'\b\d+(\.\d+)?\b', 'NUM', text)
        
        return text
    
    def _extract_structure(self, node: tree_sitter.Node) -> str:
        """Extract structural representation of node"""
        def node_structure(n):
            if not n.children:
                return n.type
            
            children_structure = [node_structure(child) for child in n.children 
                                if child.type not in self.config.get("ignore_patterns", [])]
            
            if children_structure:
                return f"{n.type}({','.join(children_structure)})"
            else:
                return n.type
        
        return node_structure(node)
    
    def _count_tokens(self, node: tree_sitter.Node) -> int:
        """Count tokens in node"""
        text = node.text.decode('utf8') if node.text else ""
        import re
        tokens = re.findall(r'\b\w+\b', text)
        return len(tokens)
    
    def _count_nodes(self, node: tree_sitter.Node) -> int:
        """Count AST nodes in subtree"""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def _calculate_similarity(self, block1: Dict, block2: Dict) -> float:
        """Calculate similarity between two code blocks"""
        # Exact match (Type 1)
        if block1["hash"] == block2["hash"]:
            return 1.0
        
        # Parameterized match (Type 2)
        if block1["normalized_hash"] == block2["normalized_hash"]:
            return 0.95
        
        # Structural similarity (Type 3/4)
        if block1["structure_hash"] == block2["structure_hash"]:
            return 0.85
        
        # Text-based similarity for near-miss clones
        text1 = block1["text"]
        text2 = block2["text"]
        
        # Calculate Jaccard similarity on tokens
        import re
        tokens1 = set(re.findall(r'\b\w+\b', text1.lower()))
        tokens2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not tokens1 and not tokens2:
            return 0.0
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    def _meets_minimum_size(self, block: Dict) -> bool:
        """Check if code block meets minimum size requirements"""
        min_config = self.config.get("minimum_clone_size", {})
        
        # Check line count
        line_count = block["end_point"][0] - block["start_point"][0] + 1
        if line_count < min_config.get("lines", 5):
            return False
        
        # Check token count
        if block["token_count"] < min_config.get("tokens", 50):
            return False
        
        # Check node count
        if block["node_count"] < min_config.get("nodes", 10):
            return False
        
        return True
    
    def _determine_clone_type(self, similarity: float) -> str:
        """Determine clone type based on similarity score"""
        thresholds = self.config.get("similarity_thresholds", {})
        
        if similarity >= thresholds.get("exact_clone", 1.0):
            return "Type 1 (Exact)"
        elif similarity >= thresholds.get("parameterized_clone", 0.9):
            return "Type 2 (Parameterized)"
        elif similarity >= thresholds.get("near_miss_clone", 0.8):
            return "Type 3 (Near-miss)"
        elif similarity >= thresholds.get("semantic_clone", 0.7):
            return "Type 4 (Semantic)"
        else:
            return "No Clone"
    
    def detect_duplications(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Detect code duplications across multiple files
        
        Args:
            files: List of dictionaries with 'path' and 'content' keys
            
        Returns:
            Dictionary containing duplication analysis results
        """
        start_time = time.time()
        
        try:
            all_blocks = []
            file_blocks = {}
            
            # Parse all files and extract code blocks
            for file_info in files:
                file_path = file_info["path"]
                content = file_info["content"]
                
                tree = self._parse_file(file_path, content)
                if not tree:
                    continue
                
                language = self._detect_language(file_path)
                if not language:
                    logger.warning(f"Unsupported file extension for: {file_path}")
                    continue
                    
                blocks = self._extract_code_blocks(tree, language)
                
                # Filter blocks by minimum size
                valid_blocks = [block for block in blocks if self._meets_minimum_size(block)]
                
                # Add file information to blocks
                for block in valid_blocks:
                    block["file_path"] = file_path
                    block["language"] = language
                
                all_blocks.extend(valid_blocks)
                file_blocks[file_path] = valid_blocks
            
            # Find duplications
            duplications = []
            processed_pairs = set()
            
            for i, block1 in enumerate(all_blocks):
                for j, block2 in enumerate(all_blocks[i+1:], i+1):
                    # Skip same file comparisons if configured
                    if block1["file_path"] == block2["file_path"]:
                        continue
                    
                    # Skip if already processed
                    pair_key = tuple(sorted([i, j]))
                    if pair_key in processed_pairs:
                        continue
                    processed_pairs.add(pair_key)
                    
                    # Calculate similarity
                    similarity = self._calculate_similarity(block1, block2)
                    clone_type = self._determine_clone_type(similarity)
                    
                    # Check if similarity meets threshold
                    min_threshold = self.config.get("similarity_thresholds", {}).get("semantic_clone", 0.7)
                    if similarity >= min_threshold:
                        duplication = {
                            "clone_type": clone_type,
                            "similarity_score": similarity,
                            "block1": {
                                "file": block1["file_path"],
                                "type": block1["type"],
                                "start_line": block1["start_point"][0] + 1,
                                "end_line": block1["end_point"][0] + 1,
                                "token_count": block1["token_count"],
                                "language": block1["language"]
                            },
                            "block2": {
                                "file": block2["file_path"],
                                "type": block2["type"],
                                "start_line": block2["start_point"][0] + 1,
                                "end_line": block2["end_point"][0] + 1,
                                "token_count": block2["token_count"],
                                "language": block2["language"]
                            }
                        }
                        duplications.append(duplication)
            
            # Calculate summary statistics
            total_files = len(files)
            files_with_duplications = len(set(d["block1"]["file"] for d in duplications) | 
                                        set(d["block2"]["file"] for d in duplications))
            
            clone_type_counts = {}
            for dup in duplications:
                clone_type = dup["clone_type"]
                clone_type_counts[clone_type] = clone_type_counts.get(clone_type, 0) + 1
            
            # Generate recommendations
            recommendations = self._generate_recommendations(duplications)
            
            processing_time = time.time() - start_time
            
            return {
                "analysis_type": "code_duplication",
                "total_files_analyzed": total_files,
                "files_with_duplications": files_with_duplications,
                "total_duplications": len(duplications),
                "duplication_percentage": round((files_with_duplications / total_files * 100) if total_files > 0 else 0, 2),
                "clone_type_distribution": clone_type_counts,
                "duplications": duplications,
                "recommendations": recommendations,
                "processing_time": processing_time,
                "configuration": {
                    "similarity_thresholds": self.config.get("similarity_thresholds", {}),
                    "minimum_clone_size": self.config.get("minimum_clone_size", {}),
                    "languages_supported": list(self.parsers.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Error detecting duplications: {str(e)}")
            return {
                "error": str(e),
                "analysis_type": "code_duplication",
                "processing_time": time.time() - start_time
            }
    
    def _generate_recommendations(self, duplications: List[Dict]) -> List[str]:
        """Generate recommendations based on duplication analysis"""
        recommendations = []
        
        if not duplications:
            recommendations.append("✅ No significant code duplications detected")
            return recommendations
        
        # Count by clone type
        type1_count = sum(1 for d in duplications if "Type 1" in d["clone_type"])
        type2_count = sum(1 for d in duplications if "Type 2" in d["clone_type"])
        type3_count = sum(1 for d in duplications if "Type 3" in d["clone_type"])
        type4_count = sum(1 for d in duplications if "Type 4" in d["clone_type"])
        
        # Type 1 (Exact) recommendations
        if type1_count > 0:
            recommendations.append(
                f"🔴 {type1_count} exact code duplications found - Extract to common functions/modules immediately"
            )
        
        # Type 2 (Parameterized) recommendations  
        if type2_count > 0:
            recommendations.append(
                f"🟡 {type2_count} parameterized duplications found - Consider using generic functions or templates"
            )
        
        # Type 3 (Near-miss) recommendations
        if type3_count > 0:
            recommendations.append(
                f"🟠 {type3_count} near-miss duplications found - Review for potential refactoring opportunities"
            )
        
        # Type 4 (Semantic) recommendations
        if type4_count > 0:
            recommendations.append(
                f"🔵 {type4_count} semantic duplications found - Consider design patterns or shared abstractions"
            )
        
        # General recommendations
        if len(duplications) > 10:
            recommendations.append("📊 High duplication detected - Consider implementing coding standards and review processes")
        
        # File-specific recommendations
        file_duplication_count = {}
        for dup in duplications:
            file1 = dup["block1"]["file"]
            file2 = dup["block2"]["file"]
            file_duplication_count[file1] = file_duplication_count.get(file1, 0) + 1
            file_duplication_count[file2] = file_duplication_count.get(file2, 0) + 1
        
        high_dup_files = [f for f, count in file_duplication_count.items() if count > 3]
        if high_dup_files:
            recommendations.append(
                f"📁 Files with high duplication: {', '.join(high_dup_files[:3])}{'...' if len(high_dup_files) > 3 else ''}"
            )
        
        return recommendations


# Create analyzer instance
_duplication_detector = DuplicationDetector()

def duplication_detector_tool(files: List[Dict[str, str]]) -> Dict[str, Any]:
    """Detect code duplication across multiple files using AST analysis"""
    return _duplication_detector.detect_duplications(files)

# ADK FunctionTool for duplication detection
DuplicationDetectorTool = FunctionTool(
    name="duplication_detector",
    description="Detect code duplication across files using AST-based analysis with Tree-sitter parsing",
    function=duplication_detector_tool
)