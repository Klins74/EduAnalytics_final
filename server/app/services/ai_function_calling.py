from typing import Dict, Any, List, Optional
import json
import re
from app.services.ai_service import AIService


class FunctionRegistry:
    """
    Registry for AI functions that can be called by the LLM.
    Implements a simple function calling pattern for Ollama models.
    """
    
    def __init__(self):
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.implementations: Dict[str, callable] = {}
    
    def register(self, name: str, description: str, parameters: Dict[str, Any], implementation: callable):
        """Register a function that can be called by the LLM"""
        self.functions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
        self.implementations[name] = implementation
    
    def get_functions_schema(self) -> List[Dict[str, Any]]:
        """Get the schema of all registered functions"""
        return list(self.functions.values())
    
    def get_functions_prompt(self) -> str:
        """Get a prompt describing all available functions"""
        prompt = "Доступные функции:\n\n"
        
        for name, func in self.functions.items():
            prompt += f"Функция: {name}\n"
            prompt += f"Описание: {func['description']}\n"
            
            if "parameters" in func and func["parameters"]:
                prompt += "Параметры:\n"
                for param_name, param_info in func["parameters"].items():
                    param_type = param_info.get("type", "any")
                    param_desc = param_info.get("description", "")
                    prompt += f"- {param_name} ({param_type}): {param_desc}\n"
            
            prompt += "\n"
        
        prompt += "\nКогда нужно вызвать функцию, используй формат:\n"
        prompt += "```function_call\n"
        prompt += "{\n"
        prompt += '  "name": "название_функции",\n'
        prompt += '  "arguments": {\n'
        prompt += '    "параметр1": "значение1",\n'
        prompt += '    "параметр2": "значение2"\n'
        prompt += '  }\n'
        prompt += "}\n"
        prompt += "```\n"
        
        return prompt
    
    def extract_function_calls(self, text: str) -> List[Dict[str, Any]]:
        """Extract function calls from LLM response"""
        pattern = r"```function_call\s*({[^`]*})```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        calls = []
        for match in matches:
            try:
                call_data = json.loads(match.strip())
                if "name" in call_data and "arguments" in call_data:
                    calls.append(call_data)
            except json.JSONDecodeError:
                continue
        
        return calls
    
    async def execute_function_calls(self, calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the extracted function calls"""
        results = []
        
        for call in calls:
            name = call.get("name")
            args = call.get("arguments", {})
            
            if name in self.implementations:
                try:
                    result = await self.implementations[name](**args)
                    results.append({
                        "name": name,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "name": name,
                        "error": str(e)
                    })
            else:
                results.append({
                    "name": name,
                    "error": f"Function {name} not found"
                })
        
        return results


# Создаем глобальный реестр функций
function_registry = FunctionRegistry()


async def process_function_calls(user_message: str, system_context: str = "") -> str:
    """
    Process a user message, extract and execute function calls, and return the final response
    """
    service = AIService()
    
    # Первый проход: получаем ответ от модели с возможными вызовами функций
    functions_prompt = function_registry.get_functions_prompt()
    prompt = f"{system_context}\n\n{functions_prompt}\n\nВопрос пользователя: {user_message}\n\nОтвет:"
    
    response = service.generate_reply(user_message=prompt, user_context="")
    
    # Извлекаем вызовы функций
    function_calls = function_registry.extract_function_calls(response)
    
    if not function_calls:
        # Если нет вызовов функций, возвращаем исходный ответ
        # Очищаем от возможных остатков разметки
        return response.replace("```function_call", "").replace("```", "")
    
    # Выполняем вызовы функций
    results = await function_registry.execute_function_calls(function_calls)
    
    # Формируем контекст с результатами выполнения функций
    results_context = "Результаты выполнения функций:\n"
    for result in results:
        results_context += f"Функция: {result['name']}\n"
        if "result" in result:
            results_context += f"Результат: {json.dumps(result['result'], ensure_ascii=False)}\n"
        else:
            results_context += f"Ошибка: {result.get('error', 'Неизвестная ошибка')}\n"
        results_context += "\n"
    
    # Второй проход: получаем финальный ответ с учетом результатов выполнения функций
    final_prompt = f"{system_context}\n\n{results_context}\n\nИсходный вопрос пользователя: {user_message}\n\nОтвет:"
    final_response = service.generate_reply(user_message=final_prompt, user_context="")
    
    return final_response

