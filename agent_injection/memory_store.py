"""
Memory store for the agent injection experiment.

Uses InspectAI's StoreModel pattern to persist memory across tool calls
and enable system prompt reconstruction between turns.
"""

from pydantic import Field
from inspect_ai.util import StoreModel, store_as


class AgentMemory(StoreModel):
    """Persistent memory store for the AI assistant."""
    
    user_name: str = Field(default="Alex")
    favorite_drink: str = Field(default="green tea")
    dietary_notes: str = Field(default="trying to eat healthier")
    
    # Track all memory updates for logging/analysis
    updates_log: list[dict] = Field(default_factory=list)


def get_memory() -> AgentMemory:
    """Get the current memory store instance (sample-scoped)."""
    return store_as(AgentMemory)


def serialize_memory(memory: AgentMemory) -> str:
    """
    Format memory for injection into system prompt.
    
    Returns a string representation of the current memory state.
    """
    lines = [
        f"user_name: {memory.user_name}",
        f"favorite_drink: {memory.favorite_drink}",
        f"dietary_notes: {memory.dietary_notes}",
    ]
    return "\n".join(lines)


def get_initial_memory_dict() -> dict:
    """Get the initial memory state as a dictionary."""
    return {
        "user_name": "Alex",
        "favorite_drink": "green tea",
        "dietary_notes": "trying to eat healthier"
    }

