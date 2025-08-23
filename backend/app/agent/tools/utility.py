from langchain_core.tools import tool, ToolException
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


@tool
def calculate(expression: str) -> str:
    """Perform mathematical calculations.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "10 * 5", "100 / 4")
    
    Returns:
        Calculation result
    """
    try:
        # Safe evaluation with limited functions
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "len": len
        }
        
        # Remove any dangerous characters
        if any(char in expression for char in ["import", "exec", "eval", "__"]):
            raise ToolException("Invalid expression")
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        raise ToolException(f"Calculation error: {str(e)}")


@tool
def get_current_time(timezone: Optional[str] = None) -> str:
    """Get the current date and time.
    
    Args:
        timezone: Timezone name (e.g., "UTC", "US/Pacific") - optional
    
    Returns:
        Current date and time
    """
    try:
        now = datetime.now()
        
        result = f"📅 Current time:\n"
        result += f"  • Date: {now.strftime('%Y-%m-%d')}\n"
        result += f"  • Time: {now.strftime('%H:%M:%S')}\n"
        result += f"  • Day: {now.strftime('%A')}\n"
        
        if timezone:
            result += f"  • Timezone: {timezone} (conversion not implemented)\n"
        
        return result
    except Exception as e:
        raise ToolException(f"Error getting time: {str(e)}")


@tool
def format_json(data: str, indent: int = 2) -> str:
    """Format JSON data for readability.
    
    Args:
        data: JSON string to format
        indent: Number of spaces for indentation (default: 2)
    
    Returns:
        Formatted JSON string
    """
    try:
        parsed = json.loads(data)
        formatted = json.dumps(parsed, indent=indent, sort_keys=True)
        return f"```json\n{formatted}\n```"
    except json.JSONDecodeError as e:
        raise ToolException(f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise ToolException(f"Error formatting JSON: {str(e)}")


@tool
def create_todo_list(items: list[str], title: Optional[str] = "Todo List") -> str:
    """Create a formatted todo list.
    
    Args:
        items: List of todo items
        title: Title for the todo list (optional)
    
    Returns:
        Formatted todo list
    """
    try:
        if not items:
            return "No items provided for todo list"
        
        result = f"📝 {title}:\n\n"
        for i, item in enumerate(items, 1):
            result += f"☐ {i}. {item}\n"
        
        return result
    except Exception as e:
        raise ToolException(f"Error creating todo list: {str(e)}")


@tool
def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between common units.
    
    Args:
        value: Numeric value to convert
        from_unit: Source unit (e.g., "miles", "kg", "celsius")
        to_unit: Target unit (e.g., "km", "pounds", "fahrenheit")
    
    Returns:
        Converted value with units
    """
    try:
        # Simple conversion mappings
        conversions = {
            ("miles", "km"): 1.60934,
            ("km", "miles"): 0.621371,
            ("pounds", "kg"): 0.453592,
            ("kg", "pounds"): 2.20462,
            ("feet", "meters"): 0.3048,
            ("meters", "feet"): 3.28084,
            ("celsius", "fahrenheit"): lambda c: (c * 9/5) + 32,
            ("fahrenheit", "celsius"): lambda f: (f - 32) * 5/9,
        }
        
        key = (from_unit.lower(), to_unit.lower())
        
        if key in conversions:
            conversion = conversions[key]
            if callable(conversion):
                result = conversion(value)
            else:
                result = value * conversion
            
            return f"{value} {from_unit} = {result:.2f} {to_unit}"
        else:
            raise ToolException(f"Conversion from {from_unit} to {to_unit} not supported")
            
    except Exception as e:
        raise ToolException(f"Conversion error: {str(e)}")


@tool
def generate_uuid() -> str:
    """Generate a unique identifier (UUID).
    
    Returns:
        A new UUID string
    """
    try:
        import uuid
        new_uuid = str(uuid.uuid4())
        return f"Generated UUID: {new_uuid}"
    except Exception as e:
        raise ToolException(f"Error generating UUID: {str(e)}")


@tool
def search_web(query: str, num_results: int = 5) -> str:
    """Search the web for information.
    
    Args:
        query: Search query
        num_results: Number of results to return (default: 5)
    
    Returns:
        Search results summary
    """
    try:
        # In production, this would use a search API
        # Mock results for demo
        return f"🔍 Search results for '{query}':\n\n1. Result 1 title\n   Brief description of result 1\n\n2. Result 2 title\n   Brief description of result 2\n\n(This is a mock search - integrate with real search API for production)"
    except Exception as e:
        raise ToolException(f"Search error: {str(e)}")