analyse this code: async def run_agent_sequential(agent, code_submission: str, session_service, agent_name: str, max_retries: int = 3):
    """Helper function to run a single agent with retry logic and return its response"""
    for attempt in range(max_retries):
        try:
            print(f"--- Sequential Pipeline: Executing {agent_name} (attempt {attempt + 1}/{max_retries}) ---")
            
            # Create runner for this specific agent
            runner = Runner(
                agent=agent,
                app_name="code_review_sequential",
                session_service=session_service
            )
            
            # Create session for this analysis
            session = await session_service.create_session(
                app_name="code_review_sequential",
                user_id="orchestrator",
                session_id=f"analysis_{agent_name}_{attempt}"
            )
            
            # Prepare user message with code
            content = types.Content(
                role='user', 
                parts=[types.Part(text=f"Analyze this code:\n\n{code_submission}")]
            )
            
            # Run agent and capture result
            final_response = ""
            async for event in runner.run_async(
                user_id="orchestrator",
                session_id=f"analysis_{agent_name}_{attempt}",
                new_message=content
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                    break
            
            if final_response:
                print(f"--- Sequential Pipeline: {agent_name} completed successfully ---")
                return final_response
            else:
                print(f"--- Sequential Pipeline: {agent_name} returned empty response ---")
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    backoff_delay = 2 ** attempt
                    print(f"--- Sequential Pipeline: Retrying {agent_name} in {backoff_delay}s ---")
                    await asyncio.sleep(backoff_delay)
                    continue
                else:
                    return f"Analysis incomplete: {agent_name} returned empty response after {max_retries} attempts"
        
        except Exception as e:
            print(f"--- Sequential Pipeline: Error in {agent_name} (attempt {attempt + 1}): {str(e)} ---")
            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                backoff_delay = 2 ** attempt
                print(f"--- Sequential Pipeline: Retrying {agent_name} in {backoff_delay}s due to error ---")
                await asyncio.sleep(backoff_delay)
                continue
            else:
                return f"Analysis failed: {agent_name} failed after {max_retries} attempts. Last error: {str(e)}"
    
    return f"Analysis failed: {agent_name} exceeded maximum retry attempts"