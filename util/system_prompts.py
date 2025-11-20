"""
System Prompts Loader
Loads centralized system prompts from config/llm/system_prompts.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, Any

# Path to system prompts configuration
SYSTEM_PROMPTS_PATH = Path(__file__).parent.parent / "config" / "llm" / "system_prompts.yaml"


def load_system_prompts() -> Dict[str, Any]:
    """
    Load all system prompts from centralized YAML configuration.
    
    Returns:
        Dictionary containing all agent prompts with their descriptions and instructions
    """
    try:
        with open(SYSTEM_PROMPTS_PATH, 'r') as f:
            prompts = yaml.safe_load(f)
        return prompts
    except FileNotFoundError:
        raise FileNotFoundError(
            f"System prompts file not found at {SYSTEM_PROMPTS_PATH}. "
            "Please ensure config/llm/system_prompts.yaml exists."
        )
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing system prompts YAML: {e}")


def get_agent_prompt(agent_name: str) -> Dict[str, str]:
    """
    Get the prompt configuration for a specific agent.
    
    Args:
        agent_name: Name of the agent (e.g., 'orchestrator_agent', 'code_quality_agent')
    
    Returns:
        Dictionary with 'description' and 'instruction' keys
    
    Raises:
        KeyError: If agent_name not found in configuration
    """
    prompts = load_system_prompts()
    
    if agent_name not in prompts:
        available_agents = ', '.join(prompts.keys())
        raise KeyError(
            f"Agent '{agent_name}' not found in system prompts. "
            f"Available agents: {available_agents}"
        )
    
    return prompts[agent_name]


def get_agent_description(agent_name: str) -> str:
    """Get the description for a specific agent."""
    return get_agent_prompt(agent_name)['description']


def get_agent_instruction(agent_name: str) -> str:
    """Get the instruction/system prompt for a specific agent."""
    return get_agent_prompt(agent_name)['instruction']


# Convenience function for direct access
def get_prompts() -> Dict[str, Any]:
    """Alias for load_system_prompts()"""
    return load_system_prompts()


if __name__ == "__main__":
    # Test the loader
    print("🔍 Testing System Prompts Loader\n")
    
    try:
        prompts = load_system_prompts()
        print(f"✅ Loaded {len(prompts)} agent prompts:")
        for agent_name in prompts.keys():
            print(f"   - {agent_name}")
        
        print("\n📋 Testing individual agent access:")
        test_agent = "orchestrator_agent"
        prompt = get_agent_prompt(test_agent)
        print(f"   Agent: {test_agent}")
        print(f"   Description: {prompt['description'][:50]}...")
        print(f"   Instruction length: {len(prompt['instruction'])} characters")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
