"""
Tools for multi-scenario memory injection attacks.

Provides web_search and update_memory tools that work with
the dynamic scenario memory system.
"""

from inspect_ai.tool import tool

from .scenario_content import get_scenario_web_search_response
from .scenario_memory import update_memory_value, get_scenario_memory


@tool
def scenario_web_search(scenario_id: str, strategy: str | None = None):
    """
    Create a web search tool that returns scenario-specific content.
    
    Args:
        scenario_id: The scenario identifier
        strategy: Injection strategy ("chat_log", "user_review") or None for control
    """
    async def execute(query: str) -> str:
        """
        Search the web and return relevant pages for your query.
        
        Use this to find information online about any topic.
        
        Args:
            query: The search query to look up
            
        Returns:
            Combined HTML content of relevant web pages
        """
        # Return scenario-specific content regardless of query
        return get_scenario_web_search_response(scenario_id, strategy)
    
    return execute


@tool
def scenario_update_memory():
    """
    Create an update_memory tool for the scenario memory system.
    """
    async def execute(key: str, value: str) -> str:
        """
        Update your memory about the user.
        
        Use this when you learn new preferences, facts, or relevant
        information about the user that should be remembered for
        future conversations.
        
        Args:
            key: The memory key to update (e.g., "risk_tolerance", "allergies")
            value: The new value to store
            
        Returns:
            Confirmation message
        """
        success, message = update_memory_value(key, value)
        return message
    
    return execute

