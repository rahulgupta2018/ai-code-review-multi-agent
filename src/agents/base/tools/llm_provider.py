"""
LLM Provider Integration for Code Analysis Tools
Supports both Ollama (development) and Gemini (production) providers with environment-based switching.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path
import time

# HTTP client for Ollama
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not available. Install with: pip install httpx")

# Google Cloud Vertex AI imports (optional for production)
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI not available. Only Ollama provider will work.")

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    OLLAMA = "ollama"
    GEMINI = "gemini"


@dataclass
class LLMRequest:
    """LLM request structure"""
    prompt: str
    temperature: float = 0.1
    max_tokens: int = 4096
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """LLM response structure"""
    content: str
    provider: str
    model: str
    tokens_used: int
    response_time: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


class LLMProviderManager:
    """
    Manages LLM provider integration for code analysis tools.
    Supports environment-based switching between Ollama and Gemini.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.active_provider = self._determine_active_provider()
        self.client: Optional[Union[Any, Any]] = None  # Union of httpx.AsyncClient and GenerativeModel
        self._initialize_client()
        
        logger.info(f"LLM Provider Manager initialized with {self.active_provider.value} provider")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load LLM configuration from YAML file"""
        if config_path is None:
            # Look in the correct location: /src/agents/configs/llm_config.yaml  
            config_file = Path(__file__).parent.parent.parent / "configs" / "llm_config.yaml"
            config_path = str(config_file)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.debug("LLM configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to load LLM configuration: {e}")
            raise RuntimeError(f"Critical error: Unable to load LLM configuration from {config_path}: {e}")
    
    def _determine_active_provider(self) -> LLMProvider:
        """Determine which LLM provider to use based on environment"""
        environment = os.getenv("LLM_ENVIRONMENT")
        if not environment:
            raise RuntimeError("LLM_ENVIRONMENT environment variable is required")
        
        if environment == "production":
            if not VERTEX_AI_AVAILABLE:
                raise RuntimeError("Vertex AI not available for production environment")
            return LLMProvider.GEMINI
        elif environment == "development":
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx not available for development environment")
            return LLMProvider.OLLAMA
        else:
            raise RuntimeError(f"Unsupported LLM_ENVIRONMENT: {environment}. Must be 'development' or 'production'")
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if self.active_provider == LLMProvider.OLLAMA:
            self._initialize_ollama_client()
        elif self.active_provider == LLMProvider.GEMINI:
            self._initialize_gemini_client()
    
    def _initialize_ollama_client(self):
        """Initialize Ollama HTTP client"""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx not available. Install with: pip install httpx")
        
        ollama_config = self.config.get("ollama_config", {})
        endpoint = os.getenv("OLLAMA_ENDPOINT")
        if not endpoint:
            raise RuntimeError("OLLAMA_ENDPOINT environment variable is required")
        
        timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))
        
        self.client = httpx.AsyncClient(
            base_url=endpoint,
            timeout=timeout
        )
        logger.debug("Ollama client initialized")
    
    def _initialize_gemini_client(self):
        """Initialize Gemini/Vertex AI client"""
        if not VERTEX_AI_AVAILABLE:
            raise RuntimeError("Vertex AI not available. Install google-cloud-aiplatform package.")
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT environment variable is required")
        
        location = os.getenv("GOOGLE_CLOUD_LOCATION")
        if not location:
            raise RuntimeError("GOOGLE_CLOUD_LOCATION environment variable is required")
        
        model_name = os.getenv("GEMINI_MODEL")
        if not model_name:
            raise RuntimeError("GEMINI_MODEL environment variable is required")
        
        try:
            vertexai.init(project=project_id, location=location)
            self.client = GenerativeModel(model_name)
            logger.debug("Gemini client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise RuntimeError(f"Failed to initialize Gemini client: {e}")
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using the active LLM provider"""
        start_time = time.time()
        
        try:
            if self.active_provider == LLMProvider.OLLAMA:
                response = await self._generate_ollama_response(request)
            elif self.active_provider == LLMProvider.GEMINI:
                response = await self._generate_gemini_response(request)
            else:
                raise ValueError(f"Unsupported provider: {self.active_provider}")
            
            response.response_time = time.time() - start_time
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            raise RuntimeError(f"LLM generation failed: {e}")
    
    async def _generate_ollama_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Ollama"""
        if not HTTPX_AVAILABLE or self.client is None:
            raise RuntimeError("Ollama client not available")
        
        model = request.model or os.getenv("OLLAMA_MODEL")
        if not model:
            raise RuntimeError("OLLAMA_MODEL environment variable is required")
        
        # Construct Ollama request payload
        payload = {
            "model": model,
            "prompt": self._construct_prompt(request),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            }
        }
        
        # Type assertion for httpx client
        client = self.client  # type: ignore
        response = await client.post("/api/generate", json=payload)
        response.raise_for_status()
        
        result = response.json()
        content = result.get("response", "")
        
        return LLMResponse(
            content=content,
            provider="ollama",
            model=model,
            tokens_used=len(content.split()),  # Approximate token count
            response_time=0.0,  # Will be set by caller
            confidence=float(os.getenv("OLLAMA_CONFIDENCE", "0.8")),
            metadata={"ollama_model": model}
        )
    
    async def _generate_gemini_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini"""
        if not VERTEX_AI_AVAILABLE or self.client is None:
            raise RuntimeError("Gemini client not available")
        
        model_name = os.getenv("GEMINI_MODEL")
        if not model_name:
            raise RuntimeError("GEMINI_MODEL environment variable is required")
        
        # Construct prompt for Gemini
        prompt = self._construct_prompt(request)
        
        # Type assertion for Gemini client  
        client = self.client  # type: ignore
        
        # Generate response
        response = client.generate_content(
            prompt,
            generation_config={
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens,
            }
        )
        
        content = response.text
        
        return LLMResponse(
            content=content,
            provider="gemini",
            model=model_name,
            tokens_used=response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else len(content.split()),
            response_time=0.0,  # Will be set by caller
            confidence=float(os.getenv("GEMINI_CONFIDENCE", "0.9")),
            metadata={"gemini_model": model_name}
        )
    
    def _construct_prompt(self, request: LLMRequest) -> str:
        """Construct the full prompt for the LLM"""
        parts = []
        
        if request.system_prompt:
            parts.append(f"System: {request.system_prompt}")
        
        if request.context:
            context_str = json.dumps(request.context, indent=2)
            parts.append(f"Context: {context_str}")
        
        parts.append(f"User: {request.prompt}")
        
        return "\n\n".join(parts)
    
    async def analyze_code_patterns(self, code: str, language: str, analysis_type: str = "quality") -> Dict[str, Any]:
        """
        Analyze code patterns using LLM
        
        Args:
            code: Source code to analyze
            language: Programming language
            analysis_type: Type of analysis (quality, security, complexity, etc.)
        
        Returns:
            Analysis results with insights and recommendations
        """
        system_prompt = self._get_analysis_system_prompt(analysis_type, language)
        
        # Get temperature and max_tokens from config or environment
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        
        request = LLMRequest(
            prompt=f"Analyze this {language} code:\n\n```{language}\n{code}\n```",
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            context={
                "language": language,
                "analysis_type": analysis_type,
                "code_length": len(code)
            }
        )
        
        response = await self.generate_response(request)
        
        # Parse structured response
        try:
            # Try to extract JSON from response if available
            content = response.content.strip()
            if content.startswith('{') and content.endswith('}'):
                return json.loads(content)
            else:
                # Return structured format even for plain text
                return {
                    "analysis": content,
                    "language": language,
                    "analysis_type": analysis_type,
                    "confidence": response.confidence,
                    "provider": response.provider,
                    "insights": self._extract_insights(content),
                    "recommendations": self._extract_recommendations(content)
                }
        except json.JSONDecodeError:
            return {
                "analysis": response.content,
                "language": language,
                "analysis_type": analysis_type,
                "confidence": response.confidence,
                "provider": response.provider,
                "insights": [],
                "recommendations": []
            }
    
    def _get_analysis_system_prompt(self, analysis_type: str, language: str) -> str:
        """Get system prompt for specific analysis type from config file"""
        # Load LLM integration config
        llm_config_path = Path(__file__).parent.parent / "configs" / "llm_integration.yaml"
        
        try:
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                llm_config = yaml.safe_load(f)
            
            # Get analysis type configuration
            analysis_config = llm_config.get("analysis_types", {}).get(analysis_type, {})
            system_prompt_template = analysis_config.get("system_prompt_template", "")
            
            if not system_prompt_template:
                raise RuntimeError(f"No system prompt template found for analysis type: {analysis_type}")
            
            # Replace language placeholder
            return system_prompt_template.format(language=language)
            
        except Exception as e:
            logger.error(f"Failed to load system prompt from config: {e}")
            raise RuntimeError(f"Failed to load system prompt configuration: {e}")
    
    def _extract_insights(self, content: str) -> List[str]:
        """Extract key insights from LLM response using config keywords"""
        try:
            # Load LLM integration config
            llm_config_path = Path(__file__).parent.parent / "configs" / "llm_integration.yaml"
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                llm_config = yaml.safe_load(f)
            
            keywords = llm_config.get("response_processing", {}).get("insight_extraction", {}).get("keywords", [])
            max_insights = llm_config.get("response_processing", {}).get("insight_extraction", {}).get("max_insights", 5)
        except Exception as e:
            logger.warning(f"Failed to load insight keywords from config: {e}")
            keywords = ['insight:', 'key finding:', 'important:', 'note:']
            max_insights = 5
        
        insights = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in keywords):
                insights.append(line)
        
        return insights[:max_insights]
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from LLM response using config keywords"""
        try:
            # Load LLM integration config
            llm_config_path = Path(__file__).parent.parent / "configs" / "llm_integration.yaml"
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                llm_config = yaml.safe_load(f)
            
            keywords = llm_config.get("response_processing", {}).get("recommendation_extraction", {}).get("keywords", [])
            max_recommendations = llm_config.get("response_processing", {}).get("recommendation_extraction", {}).get("max_recommendations", 5)
        except Exception as e:
            logger.warning(f"Failed to load recommendation keywords from config: {e}")
            keywords = ['recommend:', 'suggestion:', 'consider:', 'should:']
            max_recommendations = 5
        
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in keywords):
                recommendations.append(line)
        
        return recommendations[:max_recommendations]
    
    async def close(self):
        """Close LLM provider connections"""
        if self.client and hasattr(self.client, 'aclose'):
            await self.client.aclose()
        logger.debug("LLM provider connections closed")


# Global LLM provider instance (singleton pattern)
_llm_provider = None


def get_llm_provider() -> LLMProviderManager:
    """Get or create global LLM provider instance"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = LLMProviderManager()
    return _llm_provider


async def cleanup_llm_provider():
    """Cleanup global LLM provider instance"""
    global _llm_provider
    if _llm_provider:
        await _llm_provider.close()
        _llm_provider = None