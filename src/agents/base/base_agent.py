"""
Base Agent - Comprehensive Foundation

Enhanced foundation class for all analysis agents with memory integration,
AGDK support, and advanced learning capabilities. Provides a unified interface
for specialized agents with configurable feature sets.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FindingSeverity(Enum):
    """Severity levels for analysis findings."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class Finding:
    """Represents an analysis finding."""
    id: str
    title: str
    description: str
    severity: FindingSeverity
    category: str
    file_path: str
    line_number: Optional[int]
    column_number: Optional[int]
    code_snippet: Optional[str]
    recommendation: str
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class AnalysisContext:
    """Context for analysis execution."""
    files: List[Dict[str, Any]]
    configuration: Dict[str, Any]
    session_id: str
    metadata: Dict[str, Any]


@dataclass
class AnalysisResult:
    """Result of agent analysis."""
    agent_name: str
    findings: List[Finding]
    metrics: Dict[str, float]
    execution_time: float
    success: bool
    errors: List[str]
    metadata: Dict[str, Any]


class BaseAgent(ABC):
    """
    Enhanced base class for all analysis agents with memory integration and AGDK support.
    
    Features:
    - Memory-aware analysis with pattern learning
    - AGDK integration for tool-based execution
    - Configurable feature enablement
    - Comprehensive quality control and bias prevention
    - Historical accuracy tracking and confidence calibration
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the enhanced base agent."""
        self.name = name
        self.config = config or {}
        self.version = "2.0.0"  # Enhanced version with memory + AGDK
        
        # Agent capabilities
        self.capabilities = self._define_capabilities()
        
        # Analysis state
        self._current_context: Optional[AnalysisContext] = None
        self._findings: List[Finding] = []
        
        # Memory integration components (configurable)
        self.memory_enabled = self.config.get("memory", {}).get("enabled", True)
        self._memory_retriever = None
        self._pattern_recognizer = None
        self._confidence_scorer = None
        
        # AGDK integration (configurable)
        self.agdk_enabled = self.config.get("agdk", {}).get("enabled", False)
        
        # Learning state
        self._learned_patterns: List[Dict[str, Any]] = []
        self._historical_accuracy: Dict[str, float] = {}
        
        # Initialize components based on configuration
        if self.memory_enabled:
            self._initialize_memory_components()
        
        if self.agdk_enabled:
            self._initialize_agdk_components()
    
    def _initialize_memory_components(self):
        """Initialize memory integration components."""
        # TODO: Initialize actual memory components when implemented
        logger.debug(f"Memory components initialized for {self.name}")
    
    def _initialize_agdk_components(self):
        """Initialize AGDK integration components."""
        # TODO: Initialize actual AGDK components when implemented
        logger.debug(f"AGDK components initialized for {self.name}")
    
    @abstractmethod
    def _define_capabilities(self) -> List[str]:
        """Define the capabilities of this agent."""
        pass
    
    @abstractmethod
    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        """Perform basic analysis on the given context."""
        pass
    
    def analyze_with_memory(self, context: AnalysisContext) -> AnalysisResult:
        """Perform memory-enhanced analysis."""
        try:
            # Store current context
            self._current_context = context
            self.clear_findings()
            
            # Retrieve relevant memory context
            memory_context = self._retrieve_memory_context(context)
            
            # Enhance context with memory
            enhanced_context = self._enhance_context_with_memory(context, memory_context)
            
            # Perform core analysis
            result = self.analyze(enhanced_context)
            
            # Learn from analysis results
            self._learn_from_analysis(context, result)
            
            # Enhance findings with memory insights
            enhanced_findings = self._enhance_findings_with_memory(result.findings, memory_context)
            
            # Update result with enhanced findings
            result.findings = enhanced_findings
            result.metadata.update({
                "memory_enhanced": True,
                "learned_patterns_count": len(self._learned_patterns),
                "memory_context_items": len(memory_context)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Memory-enhanced analysis failed for {self.name}: {e}")
            # Fallback to regular analysis
            return self.analyze(context)
    
    def execute_analysis(self, context: AnalysisContext) -> AnalysisResult:
        """Main analysis entry point with intelligent routing."""
        if self.memory_enabled:
            return self.analyze_with_memory(context)
        else:
            return self.analyze(context)
    
    # AGDK Integration Methods
    def on_session_started(self, session_data: Dict[str, Any]):
        """Handle AGDK session start event."""
        if self.agdk_enabled:
            logger.info(f"AGDK session started for {self.name}: {session_data.get('session_id')}")
            # TODO: Implement AGDK session initialization
    
    def on_session_finished(self, session_data: Dict[str, Any]):
        """Handle AGDK session finish event."""
        if self.agdk_enabled:
            logger.info(f"AGDK session finished for {self.name}: {session_data.get('session_id')}")
            # TODO: Implement AGDK session cleanup
    
    def handle_agdk_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle AGDK events."""
        if self.agdk_enabled:
            # TODO: Implement AGDK event handling
            logger.debug(f"Handling AGDK event {event_type} for {self.name}")
    
    def get_agdk_tools(self) -> List[str]:
        """Get list of AGDK tools provided by this agent."""
        # To be implemented by specific agents
        return []
    
    # Memory Enhancement Methods
    def _retrieve_memory_context(self, context: AnalysisContext) -> List[Dict[str, Any]]:
        """Retrieve relevant memory context for analysis."""
        if not self.memory_enabled:
            return []
        
        # TODO: Implement memory retrieval using MemoryRetrievalCoordinator
        logger.debug(f"Retrieving memory context for {self.name}")
        
        # Placeholder memory context
        return [
            {
                "type": "similar_pattern",
                "pattern": "high_complexity_function",
                "confidence": 0.85,
                "historical_accuracy": 0.92
            },
            {
                "type": "learned_threshold",
                "metric": "complexity_score",
                "threshold": 7.5,
                "accuracy": 0.88
            }
        ]
    
    def _enhance_context_with_memory(self, context: AnalysisContext, 
                                   memory_context: List[Dict[str, Any]]) -> AnalysisContext:
        """Enhance analysis context with memory insights."""
        enhanced_metadata = context.metadata.copy()
        enhanced_metadata["memory_context"] = memory_context
        enhanced_metadata["learned_patterns"] = self._learned_patterns
        
        return AnalysisContext(
            files=context.files,
            configuration=context.configuration,
            session_id=context.session_id,
            metadata=enhanced_metadata
        )
    
    def _enhance_findings_with_memory(self, findings: List[Finding], 
                                    memory_context: List[Dict[str, Any]]) -> List[Finding]:
        """Enhance findings with memory-based insights."""
        if not self.memory_enabled:
            return findings
        
        enhanced_findings = []
        
        for finding in findings:
            # Apply confidence calibration based on historical accuracy
            calibrated_confidence = self._calibrate_confidence(finding, memory_context)
            
            # Add supporting patterns from memory
            supporting_patterns = self._find_supporting_patterns(finding, memory_context)
            
            # Create enhanced finding
            enhanced_metadata = finding.metadata.copy()
            enhanced_metadata.update({
                "original_confidence": finding.confidence,
                "calibrated_confidence": calibrated_confidence,
                "supporting_patterns": supporting_patterns,
                "memory_enhanced": True
            })
            
            enhanced_finding = Finding(
                id=finding.id,
                title=finding.title,
                description=finding.description,
                severity=finding.severity,
                category=finding.category,
                file_path=finding.file_path,
                line_number=finding.line_number,
                column_number=finding.column_number,
                code_snippet=finding.code_snippet,
                recommendation=self._enhance_recommendation(finding, memory_context),
                confidence=calibrated_confidence,
                metadata=enhanced_metadata
            )
            
            enhanced_findings.append(enhanced_finding)
        
        return enhanced_findings
    
    def _calibrate_confidence(self, finding: Finding, 
                            memory_context: List[Dict[str, Any]]) -> float:
        """Calibrate finding confidence based on historical accuracy."""
        if not self.memory_enabled:
            return finding.confidence
        
        # TODO: Implement confidence calibration using ConfidenceScorer
        
        # Simple calibration based on historical accuracy
        category_accuracy = self._historical_accuracy.get(finding.category, 0.5)
        calibrated = finding.confidence * category_accuracy
        
        return min(max(calibrated, 0.0), 1.0)  # Clamp to [0, 1]
    
    def _find_supporting_patterns(self, finding: Finding, 
                                memory_context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find supporting patterns from memory for a finding."""
        supporting_patterns = []
        
        for context_item in memory_context:
            if context_item.get("type") == "similar_pattern":
                # Check if pattern supports this finding
                if self._pattern_matches_finding(context_item, finding):
                    supporting_patterns.append(context_item)
        
        return supporting_patterns
    
    def _pattern_matches_finding(self, pattern: Dict[str, Any], finding: Finding) -> bool:
        """Check if a memory pattern matches a finding."""
        # TODO: Implement sophisticated pattern matching
        # For now, simple category matching
        return finding.category.lower() in pattern.get("pattern", "").lower()
    
    def _enhance_recommendation(self, finding: Finding, 
                              memory_context: List[Dict[str, Any]]) -> str:
        """Enhance recommendation with memory-based insights."""
        base_recommendation = finding.recommendation
        
        # Find relevant historical solutions
        historical_solutions = [
            ctx for ctx in memory_context 
            if ctx.get("type") == "successful_solution"
        ]
        
        if historical_solutions:
            enhancement = "\n\nBased on historical data: "
            enhancement += "Similar issues were successfully resolved using these approaches."
            return base_recommendation + enhancement
        
        return base_recommendation
    
    def _learn_from_analysis(self, context: AnalysisContext, result: AnalysisResult):
        """Learn from analysis results to improve future analyses."""
        if not self.memory_enabled:
            return
        
        # TODO: Implement learning using PatternRecognitionEngine
        
        # Extract patterns from this analysis
        patterns = self._extract_patterns_from_analysis(context, result)
        self._learned_patterns.extend(patterns)
        
        # Update historical accuracy metrics
        self._update_accuracy_metrics(result)
        
        logger.debug(f"Learned {len(patterns)} new patterns from analysis")
    
    def _extract_patterns_from_analysis(self, context: AnalysisContext, 
                                      result: AnalysisResult) -> List[Dict[str, Any]]:
        """Extract learnable patterns from analysis results."""
        patterns = []
        
        for finding in result.findings:
            pattern = {
                "type": "finding_pattern",
                "category": finding.category,
                "severity": finding.severity.value,
                "confidence": finding.confidence,
                "file_context": {
                    "language": self._detect_file_language(finding.file_path),
                    "size": len(finding.code_snippet or "")
                },
                "timestamp": self._get_timestamp()
            }
            patterns.append(pattern)
        
        return patterns
    
    def _update_accuracy_metrics(self, result: AnalysisResult):
        """Update historical accuracy metrics."""
        # TODO: Implement accuracy tracking based on validation feedback
        for finding in result.findings:
            category = finding.category
            current_accuracy = self._historical_accuracy.get(category, 0.5)
            
            # Simple accuracy update (placeholder)
            # In real implementation, this would be based on user feedback
            updated_accuracy = (current_accuracy + 0.01) if current_accuracy < 0.95 else current_accuracy
            self._historical_accuracy[category] = updated_accuracy
    
    def _detect_file_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file path."""
        try:
            from ...core.config.language_config import language_config
            file_ext = Path(file_path).suffix
            return language_config.detect_language_from_extension(file_ext)
        except ImportError:
            # Fallback to simple extension mapping
            extension_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.java': 'java',
                '.go': 'go',
                '.rs': 'rust',
                '.cpp': 'cpp',
                '.c': 'c',
                '.cs': 'csharp',
                '.swift': 'swift'
            }
            return extension_map.get(Path(file_path).suffix.lower())
    
    # Learning and Memory Access Methods
    def get_learned_patterns(self) -> List[Dict[str, Any]]:
        """Get all learned patterns."""
        return self._learned_patterns.copy()
    
    def get_accuracy_metrics(self) -> Dict[str, float]:
        """Get historical accuracy metrics."""
        return self._historical_accuracy.copy()
    
    def reset_learning_state(self):
        """Reset learning state (for testing/debugging)."""
        self._learned_patterns.clear()
        self._historical_accuracy.clear()
        logger.info(f"Reset learning state for {self.name}")
    
    # Enhanced Feature Status Methods
    def is_memory_enabled(self) -> bool:
        """Check if memory features are enabled."""
        return self.memory_enabled
    
    def is_agdk_enabled(self) -> bool:
        """Check if AGDK features are enabled."""
        return self.agdk_enabled
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get status of all optional features."""
        return {
            "memory_enabled": self.memory_enabled,
            "agdk_enabled": self.agdk_enabled,
            "learning_active": len(self._learned_patterns) > 0,
            "accuracy_tracking": len(self._historical_accuracy) > 0
        }
    
    # Core Agent Interface Methods (preserved from original)
    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        return self.capabilities.copy()
    
    def get_name(self) -> str:
        """Get the name of this agent."""
        return self.name
    
    def get_version(self) -> str:
        """Get the version of this agent."""
        return self.version
    
    def validate_context(self, context: AnalysisContext) -> bool:
        """Validate that the context is suitable for this agent."""
        if not context.files:
            logger.warning(f"No files provided for analysis in {self.name}")
            return False
            
        return True
    
    def create_finding(
        self,
        title: str,
        description: str,
        severity: FindingSeverity,
        category: str,
        file_path: str,
        recommendation: str,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Finding:
        """Create a new finding."""
        finding_id = f"{self.name}_{len(self._findings) + 1}_{self._get_timestamp()}"
        
        return Finding(
            id=finding_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            code_snippet=code_snippet,
            recommendation=recommendation,
            confidence=confidence,
            metadata=metadata or {}
        )
    
    def add_finding(self, finding: Finding):
        """Add a finding to the current analysis."""
        self._findings.append(finding)
        logger.debug(f"Added finding: {finding.title} [{finding.severity.value}]")
    
    def get_findings(self) -> List[Finding]:
        """Get all findings from the current analysis."""
        return self._findings.copy()
    
    def clear_findings(self):
        """Clear all findings."""
        self._findings.clear()
    
    def filter_findings_by_severity(self, severity: FindingSeverity) -> List[Finding]:
        """Filter findings by severity level."""
        return [f for f in self._findings if f.severity == severity]
    
    def get_metrics(self) -> Dict[str, float]:
        """Get enhanced analysis metrics with memory insights."""
        total_findings = len(self._findings)
        
        base_metrics = {
            "total_findings": float(total_findings),
            "critical_findings": float(len(self.filter_findings_by_severity(FindingSeverity.CRITICAL))),
            "warning_findings": float(len(self.filter_findings_by_severity(FindingSeverity.WARNING))),
            "info_findings": float(len(self.filter_findings_by_severity(FindingSeverity.INFO))),
            "average_confidence": self._calculate_average_confidence(),
            "analysis_coverage": self._calculate_coverage()
        }
        
        # Add memory-enhanced metrics if enabled
        if self.memory_enabled:
            base_metrics.update({
                "learned_patterns_count": float(len(self._learned_patterns)),
                "average_historical_accuracy": self._get_average_accuracy(),
                "memory_enhanced_findings": float(sum(1 for f in self._findings 
                                                   if f.metadata.get("memory_enhanced", False)))
            })
        
        return base_metrics
    
    def _get_average_accuracy(self) -> float:
        """Get average historical accuracy across all categories."""
        if not self._historical_accuracy:
            return 0.0
        return sum(self._historical_accuracy.values()) / len(self._historical_accuracy)
    
    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence across all findings."""
        if not self._findings:
            return 0.0
        return sum(f.confidence for f in self._findings) / len(self._findings)
    
    def _calculate_coverage(self) -> float:
        """Calculate analysis coverage percentage."""
        # TODO: Implement actual coverage calculation
        return 100.0  # Placeholder
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def __str__(self) -> str:
        """Enhanced string representation of the agent."""
        feature_status = []
        if self.memory_enabled:
            feature_status.append("Memory")
        if self.agdk_enabled:
            feature_status.append("AGDK")
        
        features = f" [{', '.join(feature_status)}]" if feature_status else ""
        return f"{self.name} v{self.version} ({len(self.capabilities)} capabilities){features}"
    
    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return (f"BaseAgent(name='{self.name}', version='{self.version}', "
                f"capabilities={self.capabilities}, memory_enabled={self.memory_enabled}, "
                f"agdk_enabled={self.agdk_enabled})")