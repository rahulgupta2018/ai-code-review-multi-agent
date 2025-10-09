"""
LLM Response Validator with Quality Control, Bias Prevention, Hallucination Detection, and Security Controls

This module provides centralized validation for LLM responses at the individual agent level,
applying rigorous quality controls, security protections against prompt injection, input/output
sanitization, and prevention of self-destructive behaviors to ensure consistency, reliability,
and security across all agent interactions.
"""

import asyncio
import re
import yaml
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from .llm_provider import get_llm_provider, LLMRequest

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of LLM response validation"""
    is_valid: bool
    confidence_score: float
    validation_errors: List[str]
    validation_warnings: List[str]
    cleaned_response: str
    evidence_score: float
    bias_indicators: List[str]
    hallucination_indicators: List[str]
    security_threats: List[str]
    injection_attempts: List[str]
    sanitization_applied: bool


@dataclass
class SecurityValidationResult:
    """Result of security validation"""
    is_secure: bool
    security_score: float
    threats_detected: List[str]
    injection_attempts: List[str]
    sanitized_input: str
    sanitized_output: str
    risk_level: str  # low, medium, high, critical


class LLMResponseValidator:
    """
    Centralized LLM response validator that applies quality control, bias prevention,
    hallucination detection, and comprehensive security controls to individual agent LLM responses.
    """
    
    def __init__(self):
        """Initialize validator with rule configurations and security controls"""
        self.quality_rules = self._load_quality_rules()
        self.bias_rules = self._load_bias_prevention_rules()
        self.hallucination_rules = self._load_hallucination_prevention_rules()
        self.validator_config = self._load_validator_config()
        self.security_config = self._load_security_config()
        
        logger.info("LLM Response Validator initialized with quality control and security rules")
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load LLM security configuration"""
        try:
            config_path = Path(__file__).parent.parent.parent / "configs" / "llm_security.yaml"
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load security config: {e}")
            raise ValueError(f"Security configuration loading failed: {e}")
    
    def _load_validator_config(self) -> Dict[str, Any]:
        """Load LLM response validator configuration"""
        try:
            config_path = Path(__file__).parent.parent.parent / "configs" / "llm_response_validator.yaml"
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load validator configuration: {e}")
            raise ValueError(f"Missing required validator configuration: {e}")
    
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
    
    def _load_hallucination_prevention_rules(self) -> Dict[str, Any]:
        """Load hallucination prevention rules"""
        try:
            config_path = Path(__file__).parent.parent.parent / "configs" / "rules" / "hallucination_prevention.yaml"
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load hallucination prevention rules: {e}")
            return {}
    
    async def validate_and_improve_llm_response(
        self,
        llm_request: LLMRequest,
        context_data: Dict[str, Any],
        response_type: str = "general"
    ) -> ValidationResult:
        """
        Generate LLM response with comprehensive validation and quality control
        
        Args:
            llm_request: The LLM request to execute
            context_data: Context data for validation (findings, metrics, etc.)
            response_type: Type of response (summary, findings, recommendation)
            
        Returns:
            ValidationResult with validated and improved response
        """
        try:
            # SECURITY VALIDATION: Validate input security first
            input_text = f"{llm_request.system_prompt or ''} {llm_request.prompt}"
            input_security = self.validate_input_security(input_text, context_data)
            
            if not input_security.is_secure:
                logger.error(f"Input security validation failed: {input_security.threats_detected}")
                return ValidationResult(
                    is_valid=False,
                    confidence_score=0.0,
                    validation_errors=[f"Security threats detected: {', '.join(input_security.threats_detected)}"],
                    validation_warnings=[],
                    cleaned_response="",
                    evidence_score=0.0,
                    bias_indicators=[],
                    hallucination_indicators=[],
                    security_threats=input_security.threats_detected,
                    injection_attempts=input_security.injection_attempts,
                    sanitization_applied=True
                )
            
            # Get LLM provider
            llm_provider = get_llm_provider()
            
            # Apply bias prevention to the request (with sanitized input)
            sanitized_request = LLMRequest(
                prompt=input_security.sanitized_input,
                system_prompt=llm_request.system_prompt,
                temperature=llm_request.temperature,
                max_tokens=llm_request.max_tokens
            )
            improved_request = self._apply_bias_prevention_to_request(sanitized_request, context_data)
            
            # Generate initial response
            response = await llm_provider.generate_response(improved_request)
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # SECURITY VALIDATION: Validate output security
            output_security = self.validate_output_security(response_content, context_data)
            
            # Use sanitized output if security issues detected
            if not output_security.is_secure:
                logger.warning(f"Output security issues detected, using sanitized version: {output_security.threats_detected}")
                response_content = output_security.sanitized_output
            
            # Apply comprehensive validation
            validation_result = await self._validate_response(
                response_content, 
                context_data, 
                response_type
            )
            
            # Update validation result with security information
            validation_result.security_threats = input_security.threats_detected + output_security.threats_detected
            validation_result.injection_attempts = input_security.injection_attempts
            validation_result.sanitization_applied = (not input_security.is_secure) or (not output_security.is_secure)
            
            # If validation fails, attempt to improve response
            if not validation_result.is_valid:
                improved_response = await self._improve_response(
                    llm_request,
                    response_content,
                    validation_result,
                    context_data
                )
                
                # Re-validate improved response
                validation_result = await self._validate_response(
                    improved_response,
                    context_data,
                    response_type
                )
                validation_result.cleaned_response = improved_response
            
            return validation_result
            
        except Exception as e:
            logger.error(f"LLM response validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_errors=[f"Validation process failed: {str(e)}"],
                validation_warnings=[],
                cleaned_response="",
                evidence_score=0.0,
                bias_indicators=[],
                hallucination_indicators=[],
                security_threats=[],
                injection_attempts=[],
                sanitization_applied=False
            )
    
    def _apply_bias_prevention_to_request(
        self, 
        llm_request: LLMRequest, 
        context_data: Dict[str, Any]
    ) -> LLMRequest:
        """Apply bias prevention measures to LLM request"""
        
        # Get bias prevention rules - no fallbacks, configuration is required
        bias_prevention = self.bias_rules['bias_prevention']
        bias_prompts = self.validator_config['bias_prevention_prompts']
        
        # Improve system prompt to reduce bias
        # Improve prompt if quality is below threshold
        improved_system_prompt = llm_request.system_prompt
        
        # Add cognitive bias prevention instructions
        if bias_prevention['cognitive_bias']['confirmation_bias']['require_alternative_perspectives']:
            improved_system_prompt += bias_prompts['cognitive_bias']['confirmation_bias_prompt']
        
        if bias_prevention['cognitive_bias']['anchoring_bias']['avoid_initial_assumption_persistence']:
            improved_system_prompt += bias_prompts['cognitive_bias']['anchoring_bias_prompt']
        
        # Add technical bias prevention
        if bias_prevention['technical_bias']['language_bias']['apply_consistent_standards']:
            improved_system_prompt += bias_prompts['technical_bias']['language_bias_prompt']
        
        # Add contextual bias prevention  
        if bias_prevention['contextual_bias']['team_context']['consider_team_experience_level']:
            improved_system_prompt += bias_prompts['contextual_bias']['team_context_prompt']
        
        # Improve prompt to include unbiased analysis context
        improved_prompt = self._prepare_unbiased_prompt(llm_request.prompt, context_data)
        
        return LLMRequest(
            prompt=improved_prompt,
            system_prompt=improved_system_prompt,
            temperature=llm_request.temperature,
            max_tokens=llm_request.max_tokens
        )
    
    def _prepare_unbiased_prompt(self, original_prompt: str, context_data: Dict[str, Any]) -> str:
        """Prepare prompt with bias prevention measures"""
        
        # Add statistical context to prevent availability heuristic
        if 'findings_by_severity' in context_data:
            severity_stats = context_data['findings_by_severity']
            total_findings = sum(len(findings) for findings in severity_stats.values())
            
            if total_findings > 0:
                context_addition = f"\n\nSTATISTICAL CONTEXT:\n"
                context_addition += f"- Total findings: {total_findings}\n"
                for severity, findings in severity_stats.items():
                    percentage = (len(findings) / total_findings) * 100
                    context_addition += f"- {severity}: {len(findings)} ({percentage:.1f}%)\n"
                
                original_prompt += context_addition
        
        # Add instruction to avoid recency bias
        original_prompt += "\n\nANALYSIS INSTRUCTION: Base your analysis on the complete data set provided, not just recent or prominent examples. Consider patterns across all findings equally."
        
        return original_prompt
    
    async def _validate_response(
        self, 
        response_content: str, 
        context_data: Dict[str, Any],
        response_type: str
    ) -> ValidationResult:
        """Validate LLM response against quality, bias, and hallucination rules"""
        
        validation_errors = []
        validation_warnings = []
        bias_indicators = []
        hallucination_indicators = []
        
        # Quality control validation
        quality_result = self._validate_quality_control(response_content)
        validation_errors.extend(quality_result['errors'])
        validation_warnings.extend(quality_result['warnings'])
        
        # Bias detection
        bias_result = self._detect_bias_indicators(response_content, context_data)
        bias_indicators.extend(bias_result['indicators'])
        validation_warnings.extend(bias_result['warnings'])
        
        # Hallucination detection
        hallucination_result = self._detect_hallucination_indicators(response_content, context_data)
        hallucination_indicators.extend(hallucination_result['indicators'])
        validation_errors.extend(hallucination_result['errors'])
        
        # Calculate confidence and evidence scores
        confidence_score = self._calculate_confidence_score(response_content, context_data)
        evidence_score = self._calculate_evidence_score(response_content, context_data)
        
        # Apply quality gates
        is_valid = self._apply_quality_gates(
            response_content, 
            confidence_score, 
            evidence_score, 
            len(validation_errors)
        )
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            cleaned_response=response_content,
            evidence_score=evidence_score,
            bias_indicators=bias_indicators,
            hallucination_indicators=hallucination_indicators,
            security_threats=[],
            injection_attempts=[],
            sanitization_applied=False
        )
    
    def _validate_quality_control(self, response_content: str) -> Dict[str, List[str]]:
        """Apply quality control validation rules"""
        errors = []
        warnings = []
        
        # Get validation thresholds from config - no fallbacks, configuration is required
        content_validation = self.validator_config['validation_thresholds']['content_validation']
        technical_jargon = self.validator_config['technical_jargon']
        context_validation = self.validator_config['context_validation']
        
        # Check minimum content length
        min_length = content_validation['min_response_length']
        if len(response_content.strip()) < min_length:
            errors.append(f"Response too short - insufficient detail provided (minimum {min_length} characters)")
        
        # Check for required information based on formatting rules
        required_keywords = context_validation['required_context_keywords']
        if required_keywords and not any(word in response_content.lower() for word in required_keywords):
            warnings.append("Response lacks contextual code analysis information")
        
        # Check for accessibility requirements
        jargon_patterns = technical_jargon['jargon_patterns']
        max_jargon = content_validation['max_jargon_count']
        
        if jargon_patterns:
            jargon_pattern = '|'.join(jargon_patterns)
            jargon_count = len(re.findall(jargon_pattern, response_content, re.IGNORECASE))
            if jargon_count > max_jargon:
                warnings.append(f"Response contains excessive technical jargon ({jargon_count} instances, max {max_jargon})")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _detect_bias_indicators(self, response_content: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential bias indicators in the response"""
        indicators = []
        warnings = []
        
        # Get bias detection config - no fallbacks, configuration is required
        bias_detection = self.validator_config['bias_detection']
        content_validation = self.validator_config['validation_thresholds']['content_validation']
        
        # Language bias detection
        language_preferences = bias_detection['language_preferences']
        for preference in language_preferences:
            if preference.lower() in response_content.lower():
                indicators.append(f"Language bias detected: {preference}")
        
        # Confirmation bias detection (overly confident statements without evidence)
        confident_words = bias_detection['confident_statement_words']
        if confident_words:
            confident_pattern = '|'.join(re.escape(word) for word in confident_words)
            confident_statements = re.findall(f'\\b(?:{confident_pattern})\\b', response_content, re.IGNORECASE)
            max_confident = content_validation['max_confident_statements']
            if len(confident_statements) > max_confident:
                indicators.append(f"Potential confirmation bias: excessive confident statements without evidence ({len(confident_statements)} > {max_confident})")
        
        # Availability heuristic (focusing on recent/memorable patterns)
        recency_indicators = bias_detection['recency_indicators']
        recent_keywords = recency_indicators['recent_focus_keywords']
        historical_keywords = recency_indicators['historical_balance_keywords']
        
        has_recent = any(keyword in response_content.lower() for keyword in recent_keywords)
        has_historical = any(keyword in response_content.lower() for keyword in historical_keywords)
        
        if has_recent and not has_historical:
            warnings.append("Potential recency bias: focus on recent patterns without historical context")
        
        # Pattern bias (over-interpretation)
        pattern_words = bias_detection['pattern_generalization_words']
        if pattern_words:
            pattern_pattern = '|'.join(re.escape(word) for word in pattern_words)
            found_pattern_words = re.findall(f'\\b(?:{pattern_pattern})\\b', response_content, re.IGNORECASE)
            max_pattern_words = content_validation['max_pattern_words']
            if len(found_pattern_words) > max_pattern_words:
                indicators.append(f"Potential pattern over-generalization detected ({len(found_pattern_words)} > {max_pattern_words})")
        
        return {'indicators': indicators, 'warnings': warnings}
    
    def _detect_hallucination_indicators(self, response_content: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential hallucination indicators in the response"""
        indicators = []
        errors = []
        
        # Get hallucination detection config - no fallbacks, configuration is required
        hallucination_detection = self.validator_config['hallucination_detection']
        
        # Check for specific code references that might be fabricated
        line_pattern = hallucination_detection['line_reference_pattern']
        line_references = re.findall(line_pattern, response_content, re.IGNORECASE)
        
        if line_references:
            # If we have context data with actual line numbers, validate them
            if 'findings' in context_data:
                actual_lines = set()
                for finding in context_data['findings']:
                    if isinstance(finding, dict) and 'line_number' in finding:
                        actual_lines.add(str(finding['line_number']))
                    elif isinstance(finding, dict) and 'line' in finding:
                        actual_lines.add(str(finding['line']))
                
                for line_ref in line_references:
                    if line_ref not in actual_lines and actual_lines:
                        indicators.append(f"Potential hallucination: Referenced line {line_ref} not found in actual findings")
        
        # Check for specific method/function names that might be fabricated
        method_pattern = hallucination_detection['method_reference_pattern']
        method_references = re.findall(method_pattern, response_content, re.IGNORECASE)
        max_method_refs = hallucination_detection['max_method_references_warning']
        
        if len(method_references) > max_method_refs:
            warnings = [f"High number of specific code references ({len(method_references)}) - verify accuracy"]
        
        # Check for contradictory statements
        contradictions = hallucination_detection['contradiction_pairs']
        for contradiction_pair in contradictions:
            if len(contradiction_pair) == 2:
                pos, neg = contradiction_pair
                if pos in response_content.lower() and neg in response_content.lower():
                    indicators.append(f"Potential contradiction: both '{pos}' and '{neg}' mentioned")
        
        # Check for unsupported technical claims
        claims_pattern = hallucination_detection['technical_claims_pattern']
        technical_claims = re.findall(claims_pattern, response_content, re.IGNORECASE)
        max_claims = hallucination_detection['max_technical_claims_error']
        
        if len(technical_claims) > max_claims:
            indicators.append(f"Multiple unsupported causal claims detected ({len(technical_claims)} > {max_claims})")
        
        return {'indicators': indicators, 'errors': errors}
    
    def _calculate_confidence_score(self, response_content: str, context_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on evidence and content quality"""
        
        # Get confidence scoring config - no fallbacks, configuration is required
        confidence_config = self.validator_config['validation_thresholds']['confidence_scoring']
        context_config = self.validator_config['context_validation']
        
        # Base confidence from content length and structure
        base_max = confidence_config['base_confidence_max']
        length_divisor = confidence_config['content_length_divisor']
        base_confidence = min(base_max, len(response_content) / length_divisor)
        
        # Evidence indicators
        evidence_indicators = context_config['evidence_indicators']
        evidence_score = sum(1 for indicator in evidence_indicators if indicator in response_content.lower())
        evidence_max = confidence_config['evidence_confidence_max']
        evidence_multiplier = confidence_config['evidence_multiplier']
        evidence_confidence = min(evidence_max, evidence_score * evidence_multiplier)
        
        # Specificity indicators (specific references)
        specificity_score = len(re.findall(r'line\s+\d+|function\s+\w+|class\s+\w+', response_content, re.IGNORECASE))
        specificity_max = confidence_config['specificity_confidence_max']
        specificity_multiplier = confidence_config['specificity_multiplier']
        specificity_confidence = min(specificity_max, specificity_score * specificity_multiplier)
        
        # Penalty for uncertainty indicators
        uncertainty_indicators = context_config['uncertainty_indicators']
        uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in response_content.lower())
        uncertainty_max_penalty = confidence_config['uncertainty_penalty_max']
        uncertainty_multiplier = confidence_config['uncertainty_multiplier']
        uncertainty_penalty = min(uncertainty_max_penalty, uncertainty_count * uncertainty_multiplier)
        
        final_confidence = base_confidence + evidence_confidence + specificity_confidence - uncertainty_penalty
        return max(0.0, min(1.0, final_confidence))
    
    def _calculate_evidence_score(self, response_content: str, context_data: Dict[str, Any]) -> float:
        """Calculate evidence score based on factual grounding"""
        
        # Get evidence scoring config - no fallbacks, configuration is required
        evidence_config = self.validator_config['validation_thresholds']['evidence_scoring']
        context_config = self.validator_config['context_validation']
        
        # Check for references to actual data
        data_references = 0
        min_findings_score = evidence_config['min_findings_score']
        min_metrics_score = evidence_config['min_metrics_score']
        
        if 'findings' in context_data and len(context_data['findings']) > 0:
            data_references += min_findings_score
        if 'metrics' in context_data and context_data['metrics']:
            data_references += min_metrics_score
        
        # Check for specific code references
        code_references = len(re.findall(r'line\s+\d+', response_content, re.IGNORECASE))
        code_multiplier = evidence_config['code_reference_multiplier']
        code_score = min(0.2, code_references * code_multiplier)
        
        # Check for reasoning chain
        reasoning_indicators = context_config['reasoning_indicators']
        reasoning_multiplier = evidence_config['reasoning_multiplier']
        reasoning_max = evidence_config['reasoning_max_score']
        reasoning_score = min(reasoning_max, sum(1 for indicator in reasoning_indicators if indicator in response_content.lower()) * reasoning_multiplier)
        
        return min(1.0, data_references + code_score + reasoning_score)
    
    def _apply_quality_gates(
        self, 
        response_content: str, 
        confidence_score: float, 
        evidence_score: float,
        error_count: int
    ) -> bool:
        """Apply quality gates to determine if response is valid"""
        
        # Get quality gate thresholds from config - no fallbacks, configuration is required
        quality_gates = self.validator_config['validation_thresholds']['quality_gates']
        
        # Basic quality checks
        min_length = quality_gates['min_response_length']
        if len(response_content.strip()) < min_length:
            return False
        
        if error_count > 0:
            return False
        
        min_confidence = quality_gates['min_confidence_threshold']
        if confidence_score < min_confidence:
            return False
        
        min_evidence = quality_gates['min_evidence_threshold']
        if evidence_score < min_evidence:
            return False
        
        return True
    
    async def _improve_response(
        self,
        original_request: LLMRequest,
        original_response: str,
        validation_result: ValidationResult,
        context_data: Dict[str, Any]
    ) -> str:
        """Attempt to improve response based on validation failures"""
        
        try:
            # Get improvement config - no fallbacks, configuration is required
            improvement_config = self.validator_config['response_improvement']
            improvement_instructions = improvement_config['improvement_instructions']
            quality_enhancement = improvement_config['quality_enhancement']
            
            # Create improvement prompt
            instructions_list = []
            for key, instruction in improvement_instructions.items():
                instructions_list.append(instruction)
            
            improvement_prompt = f"""
The following response failed quality validation. Please improve it based on these issues:

VALIDATION ERRORS:
{chr(10).join(validation_result.validation_errors)}

VALIDATION WARNINGS:
{chr(10).join(validation_result.validation_warnings)}

ORIGINAL RESPONSE:
{original_response}

IMPROVEMENT INSTRUCTIONS:
{chr(10).join(instructions_list)}

Please provide an improved version that addresses these issues:
"""

            system_prompt = quality_enhancement['system_prompt']
            temperature = quality_enhancement['temperature']

            improved_request = LLMRequest(
                prompt=improvement_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=original_request.max_tokens
            )
            
            llm_provider = get_llm_provider()
            response = await llm_provider.generate_response(improved_request)
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.warning(f"Failed to improve response: {e}")
            return original_response

    
    # ===== SECURITY VALIDATION METHODS =====
    
    def validate_input_security(self, user_input: str, context: Dict[str, Any]) -> SecurityValidationResult:
        """
        Comprehensive security validation for user inputs
        
        Args:
            user_input: The input to validate
            context: Context for validation
            
        Returns:
            SecurityValidationResult with security assessment
        """
        try:
            logger.debug("Starting input security validation")
            
            threats_detected = []
            injection_attempts = []
            risk_level = "low"
            
            # 1. Prompt injection detection
            injection_result = self._detect_prompt_injection(user_input)
            if injection_result['detected']:
                injection_attempts.extend(injection_result['patterns'])
                threats_detected.append("prompt_injection")
                risk_level = "high"
            
            # 2. Dangerous pattern detection
            dangerous_result = self._detect_dangerous_patterns(user_input)
            if dangerous_result['detected']:
                threats_detected.extend(dangerous_result['threats'])
                risk_level = max(risk_level, dangerous_result['risk_level'], key=lambda x: ["low", "medium", "high", "critical"].index(x))
            
            # 3. Self-destructive behavior detection
            destructive_result = self._detect_self_destructive_behavior(user_input)
            if destructive_result['detected']:
                threats_detected.extend(destructive_result['behaviors'])
                risk_level = "critical"
            
            # 4. Input sanitization
            sanitized_input = self._sanitize_input(user_input)
            
            # 5. Calculate security score
            security_score = self._calculate_security_score(threats_detected, injection_attempts, risk_level)
            
            is_secure = len(threats_detected) == 0 and len(injection_attempts) == 0
            
            logger.info(f"Input security validation completed - Secure: {is_secure}, Risk: {risk_level}")
            
            return SecurityValidationResult(
                is_secure=is_secure,
                security_score=security_score,
                threats_detected=threats_detected,
                injection_attempts=injection_attempts,
                sanitized_input=sanitized_input,
                sanitized_output="",  # Not applicable for input validation
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Input security validation failed: {e}")
            return SecurityValidationResult(
                is_secure=False,
                security_score=0.0,
                threats_detected=["validation_error"],
                injection_attempts=[],
                sanitized_input="",
                sanitized_output="",
                risk_level="critical"
            )
    
    def validate_output_security(self, output: str, context: Dict[str, Any]) -> SecurityValidationResult:
        """
        Comprehensive security validation for outputs
        
        Args:
            output: The output to validate
            context: Context for validation
            
        Returns:
            SecurityValidationResult with security assessment
        """
        try:
            logger.debug("Starting output security validation")
            
            threats_detected = []
            risk_level = "low"
            
            # 1. Sensitive data detection
            sensitive_result = self._detect_sensitive_data(output)
            if sensitive_result['detected']:
                threats_detected.extend(sensitive_result['types'])
                risk_level = "high"
            
            # 2. Data leakage detection
            leakage_result = self._detect_data_leakage(output)
            if leakage_result['detected']:
                threats_detected.extend(leakage_result['leakage_types'])
                risk_level = max(risk_level, leakage_result['risk_level'], key=lambda x: ["low", "medium", "high", "critical"].index(x))
            
            # 3. Output sanitization
            sanitized_output = self._sanitize_output(output)
            
            # 4. Calculate security score
            security_score = self._calculate_security_score(threats_detected, [], risk_level)
            
            is_secure = len(threats_detected) == 0
            
            logger.info(f"Output security validation completed - Secure: {is_secure}, Risk: {risk_level}")
            
            return SecurityValidationResult(
                is_secure=is_secure,
                security_score=security_score,
                threats_detected=threats_detected,
                injection_attempts=[],  # Not applicable for output validation
                sanitized_input="",  # Not applicable for output validation
                sanitized_output=sanitized_output,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Output security validation failed: {e}")
            return SecurityValidationResult(
                is_secure=False,
                security_score=0.0,
                threats_detected=["validation_error"],
                injection_attempts=[],
                sanitized_input="",
                sanitized_output="",
                risk_level="critical"
            )
    
    def _detect_prompt_injection(self, text: str) -> Dict[str, Any]:
        """Detect prompt injection attacks"""
        injection_config = self.security_config['prompt_injection_protection']
        patterns_detected = []
        
        # Check each category of injection patterns
        for category, patterns in injection_config['injection_patterns'].items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    patterns_detected.append(f"{category}: {pattern}")
        
        detected = len(patterns_detected) > injection_config['detection_thresholds']['max_injection_score']
        
        if detected:
            logger.warning(f"Prompt injection detected: {patterns_detected}")
        
        return {
            'detected': detected,
            'patterns': patterns_detected,
            'score': len(patterns_detected)
        }
    
    def _detect_dangerous_patterns(self, text: str) -> Dict[str, Any]:
        """Detect dangerous input patterns"""
        sanitization_config = self.security_config['input_sanitization']
        threats_detected = []
        risk_level = "low"
        
        # Check each category of dangerous patterns
        for category, patterns in sanitization_config['dangerous_patterns'].items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    threats_detected.append(f"{category}_attempt")
                    # Escalate risk based on category
                    if category in ['code_execution', 'file_system_access']:
                        risk_level = "critical"
                    elif category in ['network_requests', 'database_access']:
                        risk_level = "high"
                    elif risk_level == "low":
                        risk_level = "medium"
        
        detected = len(threats_detected) > 0
        
        if detected:
            logger.warning(f"Dangerous patterns detected: {threats_detected}")
        
        return {
            'detected': detected,
            'threats': threats_detected,
            'risk_level': risk_level
        }
    
    def _detect_self_destructive_behavior(self, text: str) -> Dict[str, Any]:
        """Detect self-destructive behavior attempts"""
        prevention_config = self.security_config['self_destructive_prevention']
        behaviors_detected = []
        
        # Check each category of self-destructive patterns
        for category, patterns in prevention_config.items():
            if isinstance(patterns, list):
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        behaviors_detected.append(f"{category}_attempt")
        
        detected = len(behaviors_detected) > 0
        
        if detected:
            logger.error(f"Self-destructive behavior detected: {behaviors_detected}")
        
        return {
            'detected': detected,
            'behaviors': behaviors_detected
        }
    
    def _detect_sensitive_data(self, text: str) -> Dict[str, Any]:
        """Detect sensitive data in output"""
        output_config = self.security_config['output_sanitization']
        types_detected = []
        
        # Check each category of sensitive patterns
        for category, patterns in output_config['sensitive_patterns'].items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    types_detected.append(f"sensitive_{category}")
        
        detected = len(types_detected) > 0
        
        if detected:
            logger.warning(f"Sensitive data detected in output: {types_detected}")
        
        return {
            'detected': detected,
            'types': types_detected
        }
    
    def _detect_data_leakage(self, text: str) -> Dict[str, Any]:
        """Detect potential data leakage"""
        output_config = self.security_config['output_sanitization']
        leakage_types = []
        risk_level = "low"
        
        # Check for specific leakage patterns
        sensitive_patterns = output_config['sensitive_patterns']
        
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in sensitive_patterns['credentials']):
            leakage_types.append("credential_leakage")
            risk_level = "critical"
        
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in sensitive_patterns['personal_info']):
            leakage_types.append("pii_leakage")
            risk_level = max(risk_level, "high", key=lambda x: ["low", "medium", "high", "critical"].index(x))
        
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in sensitive_patterns['system_info']):
            leakage_types.append("system_info_leakage")
            risk_level = max(risk_level, "medium", key=lambda x: ["low", "medium", "high", "critical"].index(x))
        
        detected = len(leakage_types) > 0
        
        return {
            'detected': detected,
            'leakage_types': leakage_types,
            'risk_level': risk_level
        }
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input"""
        sanitization_config = self.security_config['input_sanitization']
        sanitized = text
        
        if sanitization_config['sanitization_rules']['remove_null_bytes']:
            sanitized = sanitized.replace('\x00', '')
        
        if sanitization_config['sanitization_rules']['normalize_whitespace']:
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        if sanitization_config['sanitization_rules']['escape_special_characters']:
            # Basic escape of potentially dangerous characters
            sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        
        max_length = sanitization_config['sanitization_rules']['limit_input_length']
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")
        
        return sanitized
    
    def _sanitize_output(self, text: str) -> str:
        """Sanitize output to prevent data leakage"""
        output_config = self.security_config['output_sanitization']
        sanitized = text
        
        if output_config['leakage_prevention']['redact_credentials']:
            # Redact credential patterns
            redaction_settings = output_config['redaction_settings']
            for pattern in output_config['sensitive_patterns']['credentials']:
                sanitized = re.sub(pattern, redaction_settings['credential_replacement'], sanitized, flags=re.IGNORECASE)
        
        if output_config['leakage_prevention']['mask_personal_info']:
            # Mask personal information
            redaction_settings = output_config['redaction_settings']
            for pattern in output_config['sensitive_patterns']['personal_info']:
                sanitized = re.sub(pattern, redaction_settings['personal_info_replacement'], sanitized, flags=re.IGNORECASE)
        
        if output_config['leakage_prevention']['remove_file_paths']:
            # Remove file paths
            redaction_settings = output_config['redaction_settings']
            for pattern in output_config['sensitive_patterns']['system_info']:
                sanitized = re.sub(pattern, redaction_settings['file_path_replacement'], sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _calculate_security_score(self, threats: List[str], injections: List[str], risk_level: str) -> float:
        """Calculate security score based on threats detected"""
        base_score = 1.0
        
        # Deduct points for threats
        threat_penalty = len(threats) * 0.2
        injection_penalty = len(injections) * 0.3
        
        # Risk level penalty
        risk_penalties = {
            "low": 0.0,
            "medium": 0.3,
            "high": 0.6,
            "critical": 1.0
        }
        risk_penalty = risk_penalties.get(risk_level, 1.0)
        
        final_score = max(0.0, base_score - threat_penalty - injection_penalty - risk_penalty)
        return final_score


# Factory function
def create_llm_response_validator() -> LLMResponseValidator:
    """Create an LLM response validator instance"""
    return LLMResponseValidator()


# Convenience function for agents
async def validate_llm_response(
    llm_request: LLMRequest,
    context_data: Dict[str, Any],
    response_type: str = "general"
) -> ValidationResult:
    """
    Convenience function for agents to validate LLM responses
    
    Args:
        llm_request: The LLM request to execute with validation
        context_data: Context data for validation
        response_type: Type of response for specialized validation
        
    Returns:
        ValidationResult with validated response
    """
    validator = create_llm_response_validator()
    return await validator.validate_and_improve_llm_response(llm_request, context_data, response_type)