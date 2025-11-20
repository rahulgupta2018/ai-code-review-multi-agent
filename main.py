import asyncio

from dotenv import load_dotenv
from google.adk.runners import Runner

# Import the main code review orchestrator agent
from agent_workspace.orchestrator_agent.agent import orchestrator_agent
# Load session service with persistence
from util.session import JSONFileSessionService
# Load artifact service for storing code, reports, and analysis outputs
from util.artifact_service import FileArtifactService
# Service registry for agent access to services
from util.service_registry import register_services

load_dotenv()

# Using JSON file storage for persistent sessions
session_service = JSONFileSessionService(uri="jsonfile://./sessions")
# Using file-based artifact storage for code inputs, reports, and sub-agent outputs
artifact_service = FileArtifactService(base_dir="./artifacts")

# Register services for agent access
register_services(artifact_service=artifact_service, session_service=session_service)
async def main_async():
    # Setup constants
    APP_NAME = "Code Review System"
    USER_ID = "rahul_gupta_123"

    # ===== PART 2: Session Creation with Initial State =====
    # Create a new session (initial state loaded from mock data automatically)
    new_session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )
    SESSION_ID = new_session.id
    print(f"✅ Created new session: {SESSION_ID}")
    print(f"👤 User: {new_session.state.get('user_name', 'Unknown')}")
    print(f"📊 Review History: {len(new_session.state.get('review_history', []))} entries\n")

    # ===== PART 3: Agent Runner Setup =====
    # Create a runner with the main code review orchestrator
    # Now includes artifact service for storing code inputs, reports, and analysis outputs
    runner = Runner(
        agent=orchestrator_agent,
        app_name=APP_NAME,
        session_service=session_service,
        artifact_service=artifact_service,
    )
    
    print(f"📁 Artifact storage: {artifact_service.base_dir}")
    print(f"💾 Session storage: ./sessions")

    # ===== PART 4: Interactive Conversation Loop =====
    print("\n🤖 Welcome to AI Code Review System!")
    print("Submit your code for analysis or ask questions about code quality.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        # Get user input
        user_input = input("You: ")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit"]:
            print("Ending conversation. Goodbye!")
            break

        # Process the user query through the agent
        from google.genai import types
        
        content = types.Content(role="user", parts=[types.Part(text=user_input)])
        print(f"\n🔍 Analyzing...\n")
        
        try:
            async for event in runner.run_async(
                user_id=USER_ID, 
                session_id=SESSION_ID, 
                new_message=content
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(f"{part.text.strip()}")
            print()  # Add newline after response
        except Exception as e:
            print(f"❌ ERROR during analysis: {e}\n")

if __name__ == "__main__":
    asyncio.run(main_async())   

