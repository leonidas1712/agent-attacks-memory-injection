"""
Custom tools for the agent injection experiment.

Defines web_search and update_memory tools that the agent can use.
"""

from inspect_ai.tool import tool

from .content import get_web_search_response
from .memory_store import get_memory


@tool
def web_search(variation: str = "control"):
    """
    Create a web search tool that returns static content.
    
    Args:
        variation: Key from INJECTION_VARIATIONS dictionary
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
        # Always return the same static content regardless of query
        # (for experimental simplicity)
        return get_web_search_response(variation)
    
    return execute


@tool
def update_memory():
    """
    Create an update_memory tool for persisting user information.
    """
    async def execute(key: str, value: str) -> str:
        """
        Update your memory about the user.
        
        Use this when you learn new preferences, facts, or relevant 
        information about the user that should be remembered for 
        future conversations.
        
        Args:
            key: The memory key to update (e.g., "favorite_drink", "dietary_notes")
            value: The new value to store
            
        Returns:
            Confirmation message
        """
        memory = get_memory()
        
        # Get old value for logging
        old_value = getattr(memory, key, None) if hasattr(memory, key) else None
        
        # Update the memory if the key exists
        if hasattr(memory, key) and key not in ["updates_log"]:
            setattr(memory, key, value)
            
            # Log the update
            memory.updates_log.append({
                "key": key,
                "old_value": old_value,
                "new_value": value
            })
            
            return f"Memory updated: {key} = {value}"
        else:
            # Key doesn't exist - still log the attempt
            memory.updates_log.append({
                "key": key,
                "old_value": None,
                "new_value": value,
                "error": "Key not found in memory schema"
            })
            return f"Error: '{key}' is not a valid memory key. Valid keys are: user_name, favorite_drink, dietary_notes"
    
    return execute

