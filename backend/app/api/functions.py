"""
Function calling API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.function_service import function_service, FunctionParameter

router = APIRouter(prefix="/api/functions", tags=["functions"])


class FunctionRegister(BaseModel):
    name: str
    description: str
    parameters: List[FunctionParameter]


class FunctionExecute(BaseModel):
    name: str
    arguments: Dict[str, Any]


class FunctionCallParse(BaseModel):
    response: str


@router.get("/")
async def list_functions():
    """List all available functions"""
    try:
        functions = function_service.list_functions()
        return {
            "functions": [func.model_dump() for func in functions],
            "count": len(functions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema")
async def get_function_schema():
    """
    Get function schemas in OpenAI format.
    This can be used with OpenAI-compatible API calls.
    """
    try:
        schemas = function_service.get_function_schema()
        return {
            "functions": schemas,
            "count": len(schemas)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_function(request: FunctionExecute):
    """
    Execute a function by name with given arguments.
    """
    try:
        result = await function_service.execute_function(
            name=request.name,
            arguments=request.arguments
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse")
async def parse_function_call(request: FunctionCallParse):
    """
    Parse a function call from model response.
    """
    try:
        function_call = function_service.parse_function_call(request.response)
        
        if function_call is None:
            return {
                "found": False,
                "message": "No function call found in response"
            }
        
        return {
            "found": True,
            "function_call": function_call
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build-prompt")
async def build_function_prompt(
    base_prompt: str,
    available_functions: Optional[List[str]] = None
):
    """
    Build a prompt with function calling instructions.
    
    Args:
        base_prompt: Base system prompt
        available_functions: List of function names to include (None = all)
    """
    try:
        prompt = function_service.build_function_prompt(
            base_prompt=base_prompt,
            available_functions=available_functions
        )
        
        return {
            "prompt": prompt,
            "functions_included": available_functions or "all"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{function_name}")
async def unregister_function(function_name: str):
    """
    Unregister a function.
    Note: Built-in functions cannot be unregistered.
    """
    built_in = ["calculator", "get_current_time", "search_web"]
    
    if function_name in built_in:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot unregister built-in function: {function_name}"
        )
    
    try:
        success = function_service.unregister_function(function_name)
        
        if success:
            return {"message": f"Function '{function_name}' unregistered successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Function '{function_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

