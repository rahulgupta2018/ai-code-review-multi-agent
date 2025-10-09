"""
Master Orchestrator Implementation
Central coordinator for multi-agent code analysis with cross-domain synthesis
"""

import asyncio
import json
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime

from google.adk.core import BaseAgent, InvocationContext, Event, types
from google.adk.core.agents import Agent, Runner

from ..base.agent_registry import DynamicAgentRegistry
from ..base.specialized_agent import BaseSpecializedAgent
from ...core.session.session_manager import CodeReviewSessionManager
from ...core.llm.guardrails.security import SecureLLMContextManager
from ...core.llm.guardrails.bias_prevention import LLMOutputValidator
from ...core.reporting.report_generator import MasterOrchestratorReportGenerator


class CodeReviewOrchestrator(BaseAgent):
    """Master orchestrator for AI code review with intelligent sub-agent delegation"""
    
    def __init__(self):
        super().__init__(
            name="code_review_orchestrator",
            description="Master orchestrator for AI code review with intelligent sub-agent delegation"
        )
        
        # Session management (ADK pattern)
        self.session_manager = CodeReviewSessionManager()
        
        # Comprehensive LLM for cross-domain synthesis
        self.synthesis_model = "gemini-1.5-pro"
        
        # Security and validation
        self.security_manager = SecureLLMContextManager()
        self.output_validator = LLMOutputValidator()
        
        # Report generation
        self.report_generator = MasterOrchestratorReportGenerator()
        
        # Dynamic agent registry
        self.agent_registry = DynamicAgentRegistry()
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Main orchestration workflow with sub-agent delegation"""
        
        try:
            # Phase 1: Initialize Session and Parse Request
            request = self._parse_request(ctx)
            
            session = await self.session_manager.create_analysis_session(
                user_id=ctx.user_id,
                session_id=ctx.session_id,
                files=request.get('files', []),
                options=request.get('options', {})
            )
            
            yield self._create_status_event("Analysis session initialized")
            
            # Phase 2: Delegate to Specialized Sub-Agents
            yield self._create_status_event("Delegating to specialized agents")
            
            agent_results = {}
            active_agents = self.agent_registry.get_active_agents()
            
            for agent_name, sub_agent in active_agents.items():
                try:
                    # Update session progress
                    await self.session_manager.update_session_progress(
                        ctx.user_id, ctx.session_id, 
                        'agent_analysis', agent_name, 'started'
                    )
                    
                    # Delegate to sub-agent (ADK delegation pattern)
                    sub_agent_results = await self._delegate_to_sub_agent(sub_agent, request, ctx)
                    agent_results[agent_name] = sub_agent_results
                    
                    # Store results in session
                    await self.session_manager.store_agent_results(
                        ctx.user_id, ctx.session_id, 
                        agent_name, sub_agent_results
                    )
                    
                    # Update progress
                    await self.session_manager.update_session_progress(
                        ctx.user_id, ctx.session_id, 
                        'agent_analysis', agent_name, 'completed'
                    )
                    
                    yield self._create_progress_event(f"{agent_name} analysis complete")
                    
                except Exception as e:
                    # Handle agent failure gracefully
                    await self.session_manager.update_session_progress(
                        ctx.user_id, ctx.session_id, 
                        'agent_analysis', agent_name, 'failed'
                    )
                    
                    agent_results[agent_name] = {
                        'error': str(e),
                        'status': 'failed',
                        'fallback_summary': f"{agent_name} analysis failed but system continues"
                    }
                    
                    yield self._create_status_event(f"{agent_name} failed, continuing with other agents")
            
            # Phase 3: Cross-Domain Synthesis
            yield self._create_status_event("Performing cross-domain synthesis")
            
            await self.session_manager.update_session_progress(
                ctx.user_id, ctx.session_id, 'synthesis', 'orchestrator', 'started'
            )
            
            final_report = await self._perform_cross_domain_synthesis(agent_results, ctx)
            
            # Phase 4: Generate Comprehensive Report
            yield self._create_status_event("Generating comprehensive report")
            
            comprehensive_report = await self.report_generator.generate_comprehensive_report(
                orchestrator_results=final_report,
                agent_outputs=agent_results,
                analysis_metadata={
                    'user_id': ctx.user_id,
                    'session_id': ctx.session_id,
                    'files_analyzed': len(request.get('files', [])),
                    'agents_used': list(agent_results.keys()),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            )
            
            # Phase 5: Finalize Session
            await self._finalize_session(ctx.user_id, ctx.session_id, comprehensive_report)
            
            yield self._create_final_event(comprehensive_report)
            
        except Exception as e:
            error_report = {
                'error': str(e),
                'status': 'orchestration_failed',
                'partial_results': agent_results if 'agent_results' in locals() else {}
            }
            yield self._create_error_event(error_report)
    
    async def _delegate_to_sub_agent(self, 
                                   sub_agent: BaseSpecializedAgent, 
                                   request: Dict, 
                                   ctx: InvocationContext) -> Dict:
        """Delegate analysis to a specialized sub-agent (ADK delegation pattern)"""
        
        # Create sub-context for the specialized agent
        sub_context = self._create_sub_context(ctx, request['files'])
        
        # Execute sub-agent using ADK delegation
        agent_events = []
        async for event in sub_agent._run_async_impl(sub_context):
            agent_events.append(event)
        
        # Extract final results from sub-agent events
        return self._extract_results_from_agent_events(agent_events)
    
    async def _perform_cross_domain_synthesis(self, 
                                            agent_results: Dict, 
                                            ctx: InvocationContext) -> Dict:
        """Perform comprehensive cross-domain synthesis using powerful LLM"""
        
        try:
            # Create synthesis prompt with security controls
            synthesis_prompt = await self._create_secure_synthesis_prompt(agent_results)
            
            # Use comprehensive model for synthesis
            synthesis_agent = Agent(
                name="cross_domain_synthesizer",
                model=self.synthesis_model,
                description="Cross-domain code review synthesizer",
                instruction="""You are a senior technical architect performing cross-domain 
                analysis synthesis. Analyze results from multiple specialized agents and provide:
                1. Executive summary of overall code quality
                2. Critical issues requiring immediate attention  
                3. Cross-domain patterns and relationships
                4. Prioritized recommendations
                5. Overall risk assessment
                Be comprehensive but concise. Focus on actionable insights."""
            )
            
            # Execute synthesis with validation
            content = types.Content(
                role='user',
                parts=[types.Part(text=synthesis_prompt)]
            )
            
            temp_runner = Runner(
                agent=synthesis_agent,
                app_name=self.session_manager.app_name,
                session_service=self.session_manager.session_service
            )
            
            synthesis_result = ""
            async for event in temp_runner.run_async(
                user_id=ctx.user_id,
                session_id=f"{ctx.session_id}_synthesis",
                new_message=content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    synthesis_result = event.content.parts[0].text
                    break
            
            # Validate synthesis output
            validation_result = await self.output_validator.validate_agent_output(
                synthesis_result,
                agent_results,
                "orchestrator"
            )
            
            if not validation_result.is_valid:
                # Use fallback synthesis if validation fails
                synthesis_result = self._create_fallback_synthesis(agent_results)
            
            return {
                'executive_summary': self._extract_executive_summary(synthesis_result),
                'critical_issues': self._extract_critical_issues(synthesis_result),
                'cross_domain_patterns': self._identify_cross_patterns(agent_results),
                'prioritized_recommendations': self._prioritize_recommendations(synthesis_result),
                'overall_risk_score': self._calculate_risk_score(agent_results),
                'agent_results': agent_results,
                'synthesis_text': synthesis_result,
                'validation_metadata': validation_result.metadata,
                'metadata': {
                    'synthesis_model': self.synthesis_model,
                    'successful_agents': len([r for r in agent_results.values() if 'error' not in r]),
                    'total_agents': len(agent_results),
                    'synthesis_timestamp': datetime.now().isoformat(),
                    'confidence_score': validation_result.confidence_score
                }
            }
            
        except Exception as e:
            # Fallback synthesis without LLM
            return {
                'agent_results': agent_results,
                'structured_summary': self._create_structured_summary(agent_results),
                'error': f"Cross-domain synthesis failed: {str(e)}",
                'fallback_mode': True
            }
    
    def _parse_request(self, ctx: InvocationContext) -> Dict[str, Any]:
        """Parse analysis request from context"""
        # Implementation would extract files and options from context
        return {
            'files': [],  # Extract from context
            'options': {}  # Extract from context
        }
    
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
    
    def _create_final_event(self, report: Dict[str, Any]) -> Event:
        """Create final event with comprehensive report"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Analysis complete")]),
            actions=types.EventActions(
                state_delta={'final_report': report},
                artifact_delta={'comprehensive_report': json.dumps(report)}
            )
        )
    
    def _create_error_event(self, error_info: Dict[str, Any]) -> Event:
        """Create error event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Error: {error_info.get('error', 'Unknown error')}")]),
            actions=types.EventActions(
                state_delta={'error': error_info}
            )
        )
