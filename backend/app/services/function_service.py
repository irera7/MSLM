"""
Function calling service.
Allows models to call predefined functions/tools.
"""

import logging
import json
import inspect
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FunctionParameter(BaseModel):
    """Function parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[Any]] = None


class FunctionDefinition(BaseModel):
    """Function definition for model"""
    name: str
    description: str
    parameters: List[FunctionParameter]
    callable: Optional[Any] = None


class FunctionCallService:
    """
    Service for managing function calls.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.functions: Dict[str, Dict[str, Any]] = {}
    
    def register_function(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: List[FunctionParameter]
    ) -> bool:
        """
        Register a function that can be called by the model.
        
        Args:
            name: Function name
            func: Callable function
            description: Function description
            parameters: List of parameter definitions
            
        Returns:
            bool: True if successful
        """
        try:
            self.functions[name] = {
                "function": func,
                "description": description,
                "parameters": parameters
            }
            
            self.logger.info(f"Registered function: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register function {name}: {str(e)}")
            return False
    
    def unregister_function(self, name: str) -> bool:
        """Unregister a function"""
        if name in self.functions:
            del self.functions[name]
            self.logger.info(f"Unregistered function: {name}")
            return True
        return False
    
    def list_functions(self) -> List[FunctionDefinition]:
        """
        List all registered functions.
        
        Returns:
            List of function definitions
        """
        definitions = []
        
        for name, func_data in self.functions.items():
            definitions.append(FunctionDefinition(
                name=name,
                description=func_data["description"],
                parameters=func_data["parameters"]
            ))
        
        return definitions
    
    def get_function_schema(self) -> List[Dict[str, Any]]:
        """
        Get function schemas in OpenAI format.
        
        Returns:
            List of function schemas
        """
        schemas = []
        
        for name, func_data in self.functions.items():
            # Build parameters schema
            properties = {}
            required = []
            
            for param in func_data["parameters"]:
                prop = {
                    "type": param.type,
                    "description": param.description
                }
                
                if param.enum:
                    prop["enum"] = param.enum
                
                properties[param.name] = prop
                
                if param.required:
                    required.append(param.name)
            
            schema = {
                "name": name,
                "description": func_data["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            
            schemas.append(schema)
        
        return schemas
    
    async def execute_function(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a function by name with given arguments.
        
        Args:
            name: Function name
            arguments: Function arguments
            
        Returns:
            Dict with result or error
        """
        if name not in self.functions:
            return {
                "success": False,
                "error": f"Function '{name}' not found"
            }
        
        try:
            func = self.functions[name]["function"]
            
            # Check if function is async
            if inspect.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Function execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def parse_function_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse function call from model response.
        
        Expected format:
        <function_call>
        {
            "name": "function_name",
            "arguments": {...}
        }
        </function_call>
        
        Args:
            response: Model response text
            
        Returns:
            Dict with function call details or None
        """
        try:
            # Look for function call tags
            start_tag = "<function_call>"
            end_tag = "</function_call>"
            
            if start_tag not in response or end_tag not in response:
                return None
            
            start_idx = response.find(start_tag) + len(start_tag)
            end_idx = response.find(end_tag)
            
            json_str = response[start_idx:end_idx].strip()
            function_call = json.loads(json_str)
            
            if "name" not in function_call or "arguments" not in function_call:
                return None
            
            return function_call
            
        except Exception as e:
            self.logger.error(f"Failed to parse function call: {str(e)}")
            return None
    
    def build_function_prompt(
        self,
        base_prompt: str,
        available_functions: Optional[List[str]] = None
    ) -> str:
        """
        Build a prompt that instructs the model on how to use functions.
        
        Args:
            base_prompt: Base system prompt
            available_functions: List of function names to include (None = all)
            
        Returns:
            Enhanced prompt with function instructions
        """
        if available_functions is None:
            functions = self.list_functions()
        else:
            functions = [
                func for func in self.list_functions()
                if func.name in available_functions
            ]
        
        if not functions:
            return base_prompt
        
        # Build function descriptions
        func_descriptions = []
        for func in functions:
            params_str = ", ".join([
                f"{p.name}: {p.type}" + (f" ({p.description})" if p.description else "")
                for p in func.parameters
            ])
            
            func_descriptions.append(
                f"- {func.name}({params_str}): {func.description}"
            )
        
        function_instructions = f"""
You have access to the following functions:

{chr(10).join(func_descriptions)}

To call a function, respond with:
<function_call>
{{
    "name": "function_name",
    "arguments": {{
        "arg1": "value1",
        "arg2": "value2"
    }}
}}
</function_call>

Only use functions when necessary. If you don't need to call a function, respond normally.
"""
        
        return f"{base_prompt}\n\n{function_instructions}"


# Singleton instance
function_service = FunctionCallService()


# Register some built-in functions
def calculator(operation: str, a: float, b: float) -> float:
    """Perform basic arithmetic operations"""
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero"
    }
    
    if operation not in operations:
        return f"Error: Unknown operation '{operation}'"
    
    return operations[operation](a, b)


def get_current_time() -> str:
    """Get current date and time"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def search_web(query: str) -> str:
    """Search the web (placeholder)"""
    return f"Web search for '{query}' is not implemented yet. This is a placeholder."


# Register built-in functions
function_service.register_function(
    name="calculator",
    func=calculator,
    description="Perform basic arithmetic operations",
    parameters=[
        FunctionParameter(name="operation", type="string", description="Operation: add, subtract, multiply, divide"),
        FunctionParameter(name="a", type="number", description="First number"),
        FunctionParameter(name="b", type="number", description="Second number")
    ]
)

function_service.register_function(
    name="get_current_time",
    func=get_current_time,
    description="Get current date and time",
    parameters=[]
)

function_service.register_function(
    name="search_web",
    func=search_web,
    description="Search the web for information",
    parameters=[
        FunctionParameter(name="query", type="string", description="Search query")
    ]
)

