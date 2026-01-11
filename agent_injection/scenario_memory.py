"""
Dynamic memory store for multi-scenario injection attacks.

Provides a flexible memory system that can handle arbitrary fields
based on scenario configuration.
"""

from typing import Any
from pydantic import Field
from inspect_ai.util import StoreModel, store_as


class ScenarioMemory(StoreModel):
    """
    Dynamic memory store for scenarios.
    
    Uses a dictionary to store arbitrary key-value pairs,
    allowing each scenario to have different memory fields.
    """
    
    # Store memory as a flexible dictionary
    data: dict[str, Any] = Field(default_factory=dict)
    
    # Track all memory updates for logging/analysis
    updates_log: list[dict] = Field(default_factory=list)


def get_scenario_memory() -> ScenarioMemory:
    """Get the current scenario memory store instance (sample-scoped)."""
    return store_as(ScenarioMemory)


def initialize_memory(initial_values: dict[str, Any]) -> ScenarioMemory:
    """
    Initialize memory with scenario-specific values.
    
    Args:
        initial_values: Dictionary of initial memory key-value pairs
        
    Returns:
        The initialized memory store
    """
    memory = get_scenario_memory()
    memory.data = dict(initial_values)  # Copy to avoid mutation
    memory.updates_log = []
    return memory


def update_memory_value(key: str, value: str) -> tuple[bool, str]:
    """
    Update a memory value and log the change.
    
    Allows arbitrary keys to be added or updated.
    
    Args:
        key: The memory key to update (or create if new)
        value: The new value
        
    Returns:
        Tuple of (success, message)
    """
    memory = get_scenario_memory()
    
    # Get old value if key exists, otherwise None
    old_value = memory.data.get(key)
    
    # Update or create the key
    memory.data[key] = value
    
    memory.updates_log.append({
        "key": key,
        "old_value": old_value,
        "new_value": value
    })
    
    return True, f"Memory updated: {key} = {value}"


def serialize_scenario_memory(memory: ScenarioMemory) -> str:
    """
    Format memory for injection into system prompt.
    
    Returns a string representation of the current memory state.
    """
    lines = [f"{key}: {value}" for key, value in memory.data.items()]
    return "\n".join(lines)


def get_memory_value(key: str) -> Any | None:
    """Get a specific memory value."""
    memory = get_scenario_memory()
    return memory.data.get(key)


def get_all_memory() -> dict[str, Any]:
    """Get all memory values as a dictionary."""
    memory = get_scenario_memory()
    return dict(memory.data)


def get_updates_log() -> list[dict]:
    """Get the log of all memory updates."""
    memory = get_scenario_memory()
    return memory.updates_log

