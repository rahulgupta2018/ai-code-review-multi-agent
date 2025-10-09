"""
Base Specialized Agent Implementation
Base class for all specialized analysis agents with lightweight LLM integration
"""

import asyncio
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime
from abc import ABC, abstractmethod

from google.adk.core import BaseAgent, InvocationContext, Event, types
from google.adk.core.agents import Agent, Runner
from google.adk.core.session import InMemorySessionService

from .tools.deterministic_tool import BaseDeterministicTool
from ..core.llm.guardrails.security import SecureLLMContextManager
from ..core.llm.guardrails.bias_prevention import LLMOutputValidator


class BaseSpecializedAgent(BaseAgent, ABC):
    """Base class for all specialized analysis agents with lightweight LLM integration"""
    
    def __init__(self, name: str, description: str, tools: List[BaseDeterministicTool], 
                 lightweight_model: str = "gemini-2.0-flash"):
        super().__init__(name=name, description=description)
        self.tools = tools
        self.supported_languages = []
        # Lightweight LLM for domain-specific insights
        self.lightweight_model = lightweight_model
        self.domain_expertise = self._define_domain_expertise()
        
        # Security and validation
        self.security_manager = SecureLLMContextManager()
        self.output_validator = LLMOutputValidator()
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Standard specialized agent workflow with lightweight LLM synthesis"""
        
        files = self._extract_files_from_context(ctx)
        yield self._create_status_event(f"Starting {self.name} analysis")
        
        # Phase 1: Deterministic Analysis
        raw_results = []
        for file_path in files:
            if self._is_language_supported(file_path):
                file_results = await self._analyze_file_deterministic(file_path)
                raw_results.append(file_results)
        
        yield self._create_progress_event("Deterministic analysis complete, generating domain insights")
        
        # Phase 2: Lightweight LLM Domain Insights (following Google ADK pattern)
        if raw_results:
            domain_insights = await self._generate_domain_insights(raw_results, ctx)
            yield self._create_progress_event("Domain insights generated")
        else:
            domain_insights = {"insights": "No files to analyze in this domain", "status": "no_input"}
        
        # Phase 3: Package Results
        final_results = {
            'agent': self.name,
            'raw_analysis': raw_results,
            'domain_insights': domain_insights,
            'timestamp': datetime.now().isoformat(),
            'file_count': len(raw_results)
        }
        
        yield self._create_results_event(final_results)
    
    async def _analyze_file_deterministic(self, file_path: str) -> Dict:
        """Analyze a single file using deterministic tools"""
        
        results = {}
        for tool in self.tools:
            try:
                tool_result = await tool.analyze(file_path)
                results[tool.name] = tool_result
            except Exception as e:
                results[tool.name] = {'error': str(e), 'status': 'failed'}
        
        return {
            'file': file_path,
            'analysis_domain': self.name,
            'deterministic_results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _generate_domain_insights(self, raw_results: List[Dict], ctx: InvocationContext) -> Dict:
        """Generate lightweight domain-specific insights using LLM (ADK pattern)"""
        
        try:
            # Create domain-specific analysis prompt with security controls
            analysis_prompt = await self._create_secure_domain_prompt(raw_results)
            
            # Use ADK's Runner pattern for lightweight LLM call
            domain_analyzer = Agent(
                name=f"{self.name}_analyzer",
                model=self.lightweight_model,
                description=f"Domain expert for {self.name} analysis",
                instruction=f"""You are a {self.name} domain expert. 
                Analyze the provided deterministic data and generate focused insights.
                {self.domain_expertise}
                Be concise, factual, and focus only on {self.name} aspects.
                Provide actionable recommendations."""
            )
            
            # Create content for the domain analyzer
            content = types.Content(
                role='user', 
                parts=[types.Part(text=analysis_prompt)]
            )
            
            # Use InMemorySessionService for lightweight session
            temp_session_service = InMemorySessionService()
            temp_session = await temp_session_service.create_session(
                app_name=f"{self.name}_analysis",
                user_id="system",
                session_id=f"analysis_{datetime.now().timestamp()}"
            )
            
            # Create runner for domain analysis
            temp_runner = Runner(
                agent=domain_analyzer,
                app_name=f"{self.name}_analysis",
                session_service=temp_session_service
            )
            
            # Execute domain analysis
            final_response = ""
            async for event in temp_runner.run_async(
                user_id="system",
                session_id=temp_session.session_id,
                new_message=content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                    break
            
            # Validate output
            validation_result = await self.output_validator.validate_agent_output(
                final_response,
                raw_results,
                self.name
            )
            
            if not validation_result.is_valid:
                # Fallback to deterministic summary
                final_response = self._create_deterministic_summary(raw_results)
            
            return {
                'insights': final_response,
                'model_used': self.lightweight_model,
                'confidence': validation_result.confidence_score,
                'key_findings': self._extract_key_findings(final_response),
                'recommendations': self._extract_recommendations(final_response),
                'validation_metadata': validation_result.metadata,
                'status': 'success'
            }
            
        except Exception as e:
            # Fallback to deterministic summary
            return {
                'insights': self._create_deterministic_summary(raw_results),
                'error': str(e),
                'model_used': 'deterministic_fallback',
                'status': 'fallback'
            }
    
    @abstractmethod
    def _define_domain_expertise(self) -> str:
        """Define domain-specific expertise - must be implemented by subclasses"""
        pass
    
    def _extract_files_from_context(self, ctx: InvocationContext) -> List[str]:
        """Extract file list from invocation context"""
        # Implementation would extract files from context
        return []
    
    def _is_language_supported(self, file_path: str) -> bool:
        """Check if file language is supported by this agent"""
        # Implementation would check file extension against supported languages
        return True
    
    def _create_status_event(self, message: str) -> Event:
        """Create status event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=message)]),
            actions=types.EventActions(
                state_delta={'status': message}
            )
        )
    
    def _create_progress_event(self, message: str) -> Event:
        """Create progress event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=message)]),
            actions=types.EventActions(
                state_delta={'progress': message}
            )
        )
    
    def _create_results_event(self, results: Dict) -> Event:
        """Create results event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Analysis complete")]),
            actions=types.EventActions(
                state_delta={'results': results},
                artifact_delta={'analysis_data': json.dumps(results)}
            )
        )
