import asyncio
import datetime
import sys
import logging
from pathlib import Path
from typing import AsyncGenerator, List
from google.adk.agents import LlmAgent, BaseAgent, Agent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from typing_extensions import override

# Setup logging
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Initialize services when agent module loads (for adk web and adk api commands)
from util.artifact_service import FileArtifactService
from util.session import JSONFileSessionService
from util.service_registry import register_services

# Initialize services at module level so they're available for adk web/api commands
_artifact_service = FileArtifactService(base_dir="./artifacts")
_session_service = JSONFileSessionService(uri="jsonfile://./sessions")
register_services(artifact_service=_artifact_service, session_service=_session_service)
logger.info("✅ Services initialized: FileArtifactService and JSONFileSessionService")

# Import all specialized analysis agents
from .sub_agents.classifier_agent.agent import classifier_agent
from .sub_agents.code_quality_agent.agent import code_quality_agent
from .sub_agents.security_agent.agent import security_agent
from .sub_agents.engineering_practices_agent.agent import engineering_practices_agent
from .sub_agents.carbon_emission_agent.agent import carbon_emission_agent
from .sub_agents.report_synthesizer_agent.agent import report_synthesizer_agent


# ===== CUSTOM ORCHESTRATOR AGENT (Phase 1 MVP) =====
class CodeReviewOrchestratorAgent(BaseAgent):
    """
    Intelligent code review orchestrator using ReAct pattern (Phase 1 MVP).
    
    Instead of blindly calling all sub-agents, this orchestrator:
    1. Analyzes user input to understand intent (via InputClassifierAgent)
    2. Selectively invokes only relevant agents based on classification
    3. Consolidates results through report synthesizer
    
    Phase 1: Uses hardcoded if/elif logic for agent selection (simple, fast, predictable)
    Phase 2: Will migrate to PlanReActPlanner for LLM-driven selection (flexible, adaptive)
    """
    
    # Configure Pydantic to allow arbitrary types and extra attributes
    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow"  # Allow setting attributes not declared as fields
    }
    
    def __init__(
        self,
        name: str,
        classifier_agent: LlmAgent,
        code_quality_agent: Agent,
        security_agent: Agent,
        engineering_practices_agent: Agent,
        carbon_emission_agent: Agent,
        report_synthesizer_agent: Agent,
    ):
        """Initialize orchestrator with all sub-agents."""
        
        # Call parent constructor WITHOUT sub_agents to avoid parent-agent registration
        # We manually orchestrate these agents, so they shouldn't be auto-registered
        super().__init__(name=name)
        
        # Store sub-agents as instance attributes for manual orchestration
        self.classifier_agent = classifier_agent
        self.code_quality_agent = code_quality_agent
        self.security_agent = security_agent
        self.engineering_practices_agent = engineering_practices_agent
        self.carbon_emission_agent = carbon_emission_agent
        self.report_synthesizer_agent = report_synthesizer_agent
    
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Custom orchestration logic implementing ReAct pattern (Phase 1 MVP):
        1. Reason: Classify input via InputClassifierAgent
        2. Plan: Select agents using hardcoded logic (Phase 1)
        3. Act: Execute selected agents in parallel
        4. Synthesize: Generate report via ReportSynthesizerAgent
        """
        logger.info(f"[{self.name}] 🚀 Starting intelligent code review workflow (Phase 1 MVP)")
        
        # Store app_name in session state for artifact service access (first run only)
        if "_app_name" not in ctx.session.state:
            ctx.session.state["_app_name"] = ctx.app_name
        if "_user_id" not in ctx.session.state:
            ctx.session.state["_user_id"] = ctx.user_id
        
        # ===== STEP 1: REASONING - Classify User Input =====
        logger.info(f"[{self.name}] 🧠 Step 1: Analyzing user input via InputClassifierAgent...")
        
        async for event in self.classifier_agent.run_async(ctx):
            logger.info(f"[{self.name}] Classifier event: {event.author}")
            yield event
        
        # Get classification result from session state
        classification_raw = ctx.session.state.get("request_classification", {})
        
        # Parse JSON if the classifier returned a string
        import json
        import re
        if isinstance(classification_raw, str):
            try:
                # Strip markdown code fences if present (```json ... ```)
                json_str = classification_raw.strip()
                if json_str.startswith("```"):
                    # Remove opening fence (```json or ```)
                    json_str = re.sub(r'^```(?:json)?\s*\n?', '', json_str)
                    # Remove closing fence
                    json_str = re.sub(r'\n?```\s*$', '', json_str)
                
                classification = json.loads(json_str.strip())
                logger.info(f"[{self.name}] ✅ Parsed classification from JSON string")
            except json.JSONDecodeError as e:
                logger.error(f"[{self.name}] Failed to parse classification JSON: {e}")
                logger.error(f"[{self.name}] Raw classification: {classification_raw}")
                classification = {}
        else:
            classification = classification_raw
        
        if not classification:
            logger.error(f"[{self.name}] ❌ Classification failed, aborting")
            # Yield error event
            error_event = Event(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="❌ I encountered an error classifying your request. Please try again.")]
                ),
                author=self.name,
                turn_complete=True
            )
            yield error_event
            return
        
        request_type = classification.get("type", "code_review_full")
        has_code = classification.get("has_code", False)
        focus_areas = classification.get("focus_areas", [])
        confidence = classification.get("confidence", "medium")
        reasoning = classification.get("reasoning", "")
        
        logger.info(f"[{self.name}] 📋 Classification Result:")
        logger.info(f"[{self.name}]   - Type: {request_type}")
        logger.info(f"[{self.name}]   - Has Code: {has_code}")
        logger.info(f"[{self.name}]   - Focus Areas: {focus_areas}")
        logger.info(f"[{self.name}]   - Confidence: {confidence}")
        logger.info(f"[{self.name}]   - Reasoning: {reasoning}")
        
        # ===== STEP 2: HANDLE SPECIAL CASES =====
        
        # Case 1: General query (no code analysis needed)
        if request_type == "general_query":
            logger.info(f"[{self.name}] 💬 General query detected, responding directly")
            
            response_text = self._get_system_capabilities_response()
            
            response_event = Event(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=response_text)]
                ),
                author=self.name,
                turn_complete=True
            )
            yield response_event
            return
        
        # Case 2: No code provided but code analysis requested
        if not has_code:
            logger.info(f"[{self.name}] ⚠️ No code detected, prompting user")
            
            prompt_text = """I'm ready to analyze your code! However, I don't see any code in your message.

                Please provide:
                1. **The code** you'd like me to review (paste it directly or describe the file)
                2. **Optionally**, specify what you'd like me to focus on:
                - 🔒 **Security** vulnerabilities
                - 📊 **Code quality** and complexity
                - ⚙️ **Engineering practices** (SOLID, patterns)
                - 🌱 **Environmental impact** (performance, efficiency)
                - Or ask for a **comprehensive review** of all aspects

                **Example:** "Review this Python function for security issues: [paste code]"
                """.strip()
            
            prompt_event = Event(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=prompt_text)]
                ),
                author=self.name,
                turn_complete=True
            )
            yield prompt_event
            return
        
        # ===== STEP 3: PLANNING - Select Agents (Hardcoded Logic - Phase 1) =====
        logger.info(f"[{self.name}] 📝 Step 2: Planning agent execution (hardcoded logic)...")
        
        agents_to_run: List[Agent] = []
        
        # Hardcoded agent selection logic based on classification
        if request_type == "code_review_full" or not focus_areas:
            # Full comprehensive review - all agents
            agents_to_run = [
                self.code_quality_agent,
                self.security_agent,
                self.engineering_practices_agent,
                self.carbon_emission_agent,
            ]
            logger.info(f"[{self.name}] ✅ Full review: Running all 4 analysis agents")
        
        elif request_type == "code_review_security":
            agents_to_run = [self.security_agent]
            logger.info(f"[{self.name}] 🔒 Security-focused review")
        
        elif request_type == "code_review_quality":
            agents_to_run = [self.code_quality_agent]
            logger.info(f"[{self.name}] 📊 Quality-focused review")
        
        elif request_type == "code_review_engineering":
            agents_to_run = [self.engineering_practices_agent]
            logger.info(f"[{self.name}] ⚙️ Engineering practices review")
        
        elif request_type == "code_review_carbon":
            agents_to_run = [self.carbon_emission_agent]
            logger.info(f"[{self.name}] 🌱 Environmental impact review")
        
        elif request_type == "code_review_custom":
            # Custom selection based on focus areas
            if any(area in focus_areas for area in ["quality", "complexity", "maintainability"]):
                agents_to_run.append(self.code_quality_agent)
            if any(area in focus_areas for area in ["security", "vulnerability", "secure"]):
                agents_to_run.append(self.security_agent)
            if any(area in focus_areas for area in ["engineering", "solid", "practices", "patterns"]):
                agents_to_run.append(self.engineering_practices_agent)
            if any(area in focus_areas for area in ["carbon", "performance", "efficiency", "energy"]):
                agents_to_run.append(self.carbon_emission_agent)
            
            logger.info(f"[{self.name}] 🎯 Custom review: {len(agents_to_run)} agents selected")
        
        # Generate unique analysis ID
        analysis_id = f"analysis_{datetime.datetime.now():%Y%m%d_%H%M%S}"
        
        # Check cache for duplicate code reviews
        from util.result_cache import get_cache
        cache = get_cache()
        
        # Extract code first to check cache
        user_code = self._extract_code_from_conversation(ctx)
        
        if user_code and has_code:
            cached_result = cache.get(user_code, request_type)
            if cached_result:
                logger.info(f"[{self.name}] ♻️ Cache HIT! Returning cached analysis")
                
                # Yield cached response
                cached_response = Event(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=cached_result.get("report", "Cached analysis result"))]
                    ),
                    author=self.name,
                    turn_complete=True
                )
                yield cached_response
                return
        
        # Extract and save user code to artifact (if artifact service available)
        code_artifact_ref = await self._save_input_code_to_artifact(ctx, analysis_id, request_type)
        
        # Build code summary
        code_summary = {
            "request_type": request_type,
            "artifact_saved": code_artifact_ref is not None
        }
        if code_artifact_ref:
            code_summary["artifact_ref"] = code_artifact_ref
        
        # Store execution plan in session for tracking and report synthesis
        execution_plan = {
            "agents_selected": [agent.name for agent in agents_to_run],
            "request_type": request_type,
            "focus_areas": focus_areas,
            "classification_confidence": confidence,
            "classification_reasoning": reasoning,
            "timestamp": datetime.datetime.now().isoformat(),
            "analysis_id": analysis_id,
            "code_summary": code_summary
        }
        ctx.session.state["execution_plan"] = execution_plan
        ctx.session.state["current_analysis_id"] = analysis_id
        logger.info(f"[{self.name}] 📌 Execution plan stored in session (analysis_id: {analysis_id})")
        
        # ===== STEP 4: ACTING - Execute Selected Agents Sequentially (Rate Limit Protection) =====
        if agents_to_run:
            logger.info(f"[{self.name}] ⚡ Step 3: Executing {len(agents_to_run)} agents sequentially (rate limit protection)...")
            logger.info(f"[{self.name}] 🚦 Using sequential execution to prevent API rate limit (429/503 errors)")
            
            # Execute agents one by one to avoid overwhelming the API
            # This prevents the burst of 6+ LLM calls in 2 seconds that causes 503 errors
            for idx, agent in enumerate(agents_to_run, 1):
                logger.info(f"[{self.name}] 🔄 Starting agent {idx}/{len(agents_to_run)}: {agent.name}")
                
                # Execute agent and track last event for checkpointing
                last_event = None
                async for event in agent.run_async(ctx):
                    last_event = event
                    
                    # Log progress
                    if event.turn_complete:
                        logger.info(f"[{self.name}] ✅ {event.author} completed")
                    
                    yield event
                
                # Checkpoint completed agent output
                if last_event:
                    await self._checkpoint_agent_output(ctx, last_event.author)
                
                # Add small delay between agents to avoid API rate limits
                # This prevents rapid-fire requests that trigger 503 UNAVAILABLE
                if idx < len(agents_to_run):
                    delay = 2.0  # 2 second delay between agents
                    logger.info(f"[{self.name}] ⏱️  Waiting {delay}s before next agent (rate limit protection)...")
                    await asyncio.sleep(delay)
            
            logger.info(f"[{self.name}] ✅ All selected agents completed")
        else:
            logger.warning(f"[{self.name}] ⚠️ No agents selected for execution")
        
        # ===== STEP 5: SYNTHESIS - Always Consolidate Results =====
        logger.info(f"[{self.name}] 📊 Step 4: Synthesizing final report...")
        
        # Capture report content for saving to artifact
        report_content = ""
        async for event in self.report_synthesizer_agent.run_async(ctx):
            logger.info(f"[{self.name}] Report synthesizer event: {event.author}")
            
            # Capture report text from event
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        report_content += part.text
            
            yield event
        
        # Save report to artifact
        analysis_id = ctx.session.state.get("execution_plan", {}).get("analysis_id", "unknown")
        await self._save_report_to_artifact(ctx, analysis_id, report_content)
        
        # Update analysis history in session state
        await self._update_analysis_history(ctx, analysis_id)
        
        # Cache the final report for future duplicate requests
        if user_code and has_code and report_content:
            cache_data = {
                "report": report_content,
                "analysis_id": analysis_id,
                "timestamp": datetime.datetime.now().isoformat()
            }
            cache.set(user_code, request_type, cache_data)
            logger.info(f"[{self.name}] 💾 Cached analysis result for future requests")
        
        logger.info(f"[{self.name}] ✅ Code review workflow complete!")
    
    async def _checkpoint_agent_output(self, ctx: InvocationContext, agent_name: str):
        """
        Checkpoint sub-agent output to session state.
        Phase 2 will save to artifact service for recovery.
        """
        output_key_map = {
            "code_quality_agent": "code_quality_analysis",
            "security_agent": "security_analysis",
            "engineering_practices_agent": "engineering_practices_analysis",
            "carbon_emission_agent": "carbon_emission_analysis",
        }
        
        output_key = output_key_map.get(agent_name)
        if not output_key:
            return
        
        agent_output = ctx.session.state.get(output_key)
        if not agent_output:
            logger.warning(f"[{self.name}] ⚠️ No output found for {agent_name} under key {output_key}")
            return
        
        analysis_id = ctx.session.state.get("execution_plan", {}).get("analysis_id", "unknown")
        
        logger.info(f"[{self.name}] 💾 Checkpointed {agent_name} output (analysis_id: {analysis_id})")
        
        # Store checkpoint metadata
        ctx.session.state[f"checkpoint_{agent_name}"] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "analysis_id": analysis_id,
            "status": "completed"
        }
        
        # Save to artifact service if available
        from util.service_registry import get_artifact_service
        artifact_service = get_artifact_service()
        
        if artifact_service and agent_output:
            try:
                import json
                app_name = ctx.session.state.get("_app_name", "Code_Review_System")
                user_id = ctx.session.state.get("_user_id", ctx.session.id)
                
                # Save agent output to artifact
                filename = f"analysis_{analysis_id}_{agent_name}.json"
                await artifact_service.save_artifact(
                    app_name=app_name,
                    user_id=user_id,
                    filename=filename,
                    artifact=types.Part(text=json.dumps(agent_output, indent=2)),
                    session_id=ctx.session.id,
                    custom_metadata={
                        "analysis_id": analysis_id,
                        "agent_name": agent_name,
                        "output_key": output_key,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                )
                logger.info(f"[{self.name}] ✅ Saved {agent_name} output to artifact: {filename}")
                
                # Update checkpoint with artifact reference
                ctx.session.state[f"checkpoint_{agent_name}"]["artifact_ref"] = f"artifact://{filename}"
                
            except Exception as e:
                logger.warning(f"[{self.name}] ⚠️ Could not save agent output to artifact: {e}")
    
    async def _save_input_code_to_artifact(
        self, ctx: InvocationContext, analysis_id: str, request_type: str
    ) -> str | None:
        """Extract user code from conversation and save to artifact."""
        from util.service_registry import get_artifact_service
        from util.code_optimizer import strip_comments_and_docstrings, should_optimize_code
        
        artifact_service = get_artifact_service()
        if not artifact_service:
            logger.info(f"[{self.name}] ⚠️ Artifact service not available, skipping code save")
            return None
        
        try:
            # Extract code from conversation
            user_code = self._extract_code_from_conversation(ctx)
            if not user_code:
                logger.info(f"[{self.name}] ℹ️ No code found in conversation to save")
                return None
            
            # Detect language and get file extension
            language = self._detect_language(user_code)
            ext_map = {
                "python": "py", "javascript": "js", "typescript": "ts",
                "java": "java", "cpp": "cpp", "go": "go", "rust": "rs"
            }
            ext = ext_map.get(language, "txt")
            
            # Optimize code for token reduction if it's large
            optimized_code = user_code
            tokens_saved = 0
            if should_optimize_code(user_code):
                optimized_code, tokens_saved = strip_comments_and_docstrings(user_code, language)
                logger.info(f"[{self.name}] 🔧 Optimized code: ~{tokens_saved} tokens saved")
                # Store both original and optimized in session for agents to use
                ctx.session.state["_original_code"] = user_code
                ctx.session.state["_optimized_code"] = optimized_code
            else:
                ctx.session.state["_original_code"] = user_code
                ctx.session.state["_optimized_code"] = user_code
            
            # Save to artifact
            app_name = ctx.session.state.get("_app_name", "Code_Review_System")
            user_id = ctx.session.state.get("_user_id", ctx.session.id)
            filename = f"code_input_{analysis_id}.{ext}"
            
            await artifact_service.save_artifact(
                app_name=app_name,
                user_id=user_id,
                filename=filename,
                artifact=types.Part(text=user_code),  # Save original code
                session_id=ctx.session.id,
                custom_metadata={
                    "analysis_id": analysis_id,
                    "request_type": request_type,
                    "language": language,
                    "total_lines": len(user_code.split('\n')),
                    "optimized": tokens_saved > 0,
                    "tokens_saved": tokens_saved,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            )
            
            artifact_ref = f"artifact://{filename}"
            logger.info(f"[{self.name}] ✅ Saved input code to artifact: {artifact_ref}")
            return artifact_ref
            
        except Exception as e:
            logger.warning(f"[{self.name}] ⚠️ Could not save code to artifact: {e}")
            return None
    
    def _extract_code_from_conversation(self, ctx: InvocationContext) -> str | None:
        """Extract code from user's message in conversation."""
        # Get events from session (conversation history)
        events = ctx.session.events
        if not events or len(events) == 0:
            return None
        
        # Look at recent events for user messages
        for event in reversed(events[-10:]):  # Check last 10 events
            if hasattr(event, 'content') and event.content:
                content = event.content
                if content.role == "user" and content.parts:
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            text = part.text
                            # Check if message contains code patterns
                            if self._looks_like_code(text):
                                return self._extract_code_block(text)
        
        return None
    
    def _looks_like_code(self, text: str) -> bool:
        """Check if text contains code patterns."""
        code_indicators = [
            'def ', 'class ', 'function', 'const ', 'let ', 'var ',
            '```', 'import ', 'from ', 'public ', 'private ',
            '=>', '{}', '[]', '()', 'return ', 'if ', 'for ', 'while '
        ]
        return any(indicator in text for indicator in code_indicators)
    
    def _extract_code_block(self, text: str) -> str:
        """Extract code from text, handling markdown code blocks."""
        # Check for markdown code blocks
        if '```' in text:
            # Extract content between ``` markers
            parts = text.split('```')
            if len(parts) >= 3:
                code_block = parts[1]
                # Remove language identifier if present (e.g., ```python)
                lines = code_block.split('\n')
                if lines and lines[0].strip() and not any(c in lines[0] for c in [' ', '(', '{']):
                    lines = lines[1:]  # Skip language line
                return '\n'.join(lines).strip()
        
        # If no code blocks, return the whole text if it looks like code
        return text.strip()
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content."""
        code_lower = code.lower()
        
        # Python indicators
        if 'def ' in code or 'import ' in code_lower or 'from ' in code_lower:
            return "python"
        
        # JavaScript/TypeScript
        if 'function' in code_lower or 'const ' in code or 'let ' in code or '=>' in code:
            if 'interface' in code_lower or ': string' in code or ': number' in code:
                return "typescript"
            return "javascript"
        
        # Java
        if 'public class' in code_lower or 'private ' in code_lower:
            return "java"
        
        # C++
        if '#include' in code_lower or 'std::' in code:
            return "cpp"
        
        # Go
        if 'func ' in code or 'package ' in code_lower:
            return "go"
        
        # Rust
        if 'fn ' in code or 'let mut' in code:
            return "rust"
        
        return "unknown"
    
    async def _save_report_to_artifact(
        self, ctx: InvocationContext, analysis_id: str, report_content: str
    ) -> str | None:
        """Save final report to artifact."""
        from util.service_registry import get_artifact_service
        
        artifact_service = get_artifact_service()
        if not artifact_service or not report_content:
            return None
        
        try:
            app_name = ctx.session.state.get("_app_name", "Code_Review_System")
            user_id = ctx.session.state.get("_user_id", ctx.session.id)
            filename = f"report_{analysis_id}.md"
            
            # Get execution plan for metadata
            execution_plan = ctx.session.state.get("execution_plan", {})
            
            await artifact_service.save_artifact(
                app_name=app_name,
                user_id=user_id,
                filename=filename,
                artifact=types.Part(text=report_content),
                session_id=ctx.session.id,
                custom_metadata={
                    "analysis_id": analysis_id,
                    "request_type": execution_plan.get("request_type", "unknown"),
                    "agents_executed": execution_plan.get("agents_selected", []),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "report_length": len(report_content)
                }
            )
            
            artifact_ref = f"artifact://{filename}"
            logger.info(f"[{self.name}] ✅ Saved report to artifact: {artifact_ref}")
            
            # Store artifact reference in execution plan
            if "artifacts" not in ctx.session.state["execution_plan"]:
                ctx.session.state["execution_plan"]["artifacts"] = {}
            ctx.session.state["execution_plan"]["artifacts"]["final_report"] = artifact_ref
            
            return artifact_ref
            
        except Exception as e:
            logger.warning(f"[{self.name}] ⚠️ Could not save report to artifact: {e}")
            return None
    
    async def _update_analysis_history(self, ctx: InvocationContext, analysis_id: str) -> None:
        """Update session state with completed analysis record."""
        try:
            # Initialize analysis_history if not present
            if "analysis_history" not in ctx.session.state:
                ctx.session.state["analysis_history"] = []
            
            # Get execution plan
            execution_plan = ctx.session.state.get("execution_plan", {})
            
            # Count total issues from all agent outputs
            total_issues = 0
            severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            
            for agent_name in execution_plan.get("agents_selected", []):
                output_key_map = {
                    "code_quality_agent": "code_quality_analysis",
                    "security_agent": "security_analysis",
                    "engineering_practices_agent": "engineering_practices_analysis",
                    "carbon_emission_agent": "carbon_emission_analysis",
                }
                output_key = output_key_map.get(agent_name)
                if output_key:
                    agent_output = ctx.session.state.get(output_key, {})
                    # Try to extract issue counts (structure varies by agent)
                    if isinstance(agent_output, dict):
                        issues = agent_output.get("issues", [])
                        if isinstance(issues, list):
                            total_issues += len(issues)
                            # Count by severity if available
                            for issue in issues:
                                if isinstance(issue, dict):
                                    severity = issue.get("severity", "low").lower()
                                    if severity in severity_breakdown:
                                        severity_breakdown[severity] += 1
            
            # Build analysis record
            analysis_record = {
                "analysis_id": analysis_id,
                "timestamp": execution_plan.get("timestamp", datetime.datetime.now().isoformat()),
                "request_type": execution_plan.get("request_type", "unknown"),
                "status": "completed",
                "agents_executed": execution_plan.get("agents_selected", []),
                "code_summary": execution_plan.get("code_summary", {}),
                "artifacts": execution_plan.get("artifacts", {}),
                "metrics": {
                    "total_issues": total_issues,
                    "severity_breakdown": severity_breakdown,
                    "classification_confidence": execution_plan.get("classification_confidence", "medium")
                }
            }
            
            # Add to history
            ctx.session.state["analysis_history"].append(analysis_record)
            
            # Clear current_analysis_id
            if "current_analysis_id" in ctx.session.state:
                del ctx.session.state["current_analysis_id"]
            
            logger.info(
                f"[{self.name}] ✅ Updated analysis history: "
                f"{len(ctx.session.state['analysis_history'])} total analyses"
            )
            
        except Exception as e:
            logger.warning(f"[{self.name}] ⚠️ Could not update analysis history: {e}")
    
    def _get_system_capabilities_response(self) -> str:
        """Generate response for general capability queries."""
        return """🤖 **AI Code Review Assistant** (Phase 1 MVP)

        I'm an intelligent multi-agent system that analyzes code across multiple quality dimensions.

        **🔍 What I Can Do:**

        I coordinate a team of specialized agents to review your code:

        1. **📊 Code Quality Agent**: Analyzes complexity, maintainability, code smells
        2. **🔒 Security Agent**: Identifies vulnerabilities, security risks, unsafe practices
        3. **⚙️ Engineering Practices Agent**: Reviews SOLID principles, design patterns, best practices
        4. **🌱 Carbon Emission Agent**: Assesses environmental impact, performance, efficiency

        **💬 How to Use Me:**

        **Full Comprehensive Review:**
        ```
        "Review this code"
        "Analyze this function"
        ```
        → I'll run all 4 agents for complete analysis

        **Targeted Review (Specific Focus):**
        ```
        "Check this for security issues"
        "Analyze code quality"
        "Review for SOLID principles"
        "Check carbon footprint"
        ```
        → I'll run only the relevant agent

        **Custom Review (Multiple Areas):**
        ```
        "Review this for security and quality"
        "Check SOLID and performance"
        ```
        → I'll run the specific agents you request

        **🎯 How It Works:**

        1. **I analyze your request** to understand what you need
        2. **I select the right agents** (not all, just what's needed)
        3. **Agents work in parallel** for fast results
        4. **With the help of my Report Synthesizer Agent, I consolidate everything** into one clear report
å
        **Ready to analyze your code!** Just paste your code and tell me what you'd like me to focus on (or ask for a full review).
        """.strip()    


# ===== INSTANTIATE ORCHESTRATOR AGENT =====
orchestrator_agent = CodeReviewOrchestratorAgent(
    name="orchestrator_agent",
    classifier_agent=classifier_agent,
    code_quality_agent=code_quality_agent,
    security_agent=security_agent,
    engineering_practices_agent=engineering_practices_agent,
    carbon_emission_agent=carbon_emission_agent,
    report_synthesizer_agent=report_synthesizer_agent,
)

# Export as root_agent for main.py
root_agent = orchestrator_agent
