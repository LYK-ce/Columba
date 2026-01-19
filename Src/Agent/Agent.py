#Presented by KeJi
#Date : 2026-01-19

"""
Agent - Columba Agent核心类，负责处理用户消息和工具调用
"""

import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llama_cpp import Llama
from Log.Log import Log_Info


class Agent:
    """
    Agent类 - 处理用户消息，支持工具调用
    """
    
    MODULE_NAME = "Agent"
    
    def __init__(self, config: dict):
        """
        初始化Agent
        
        Args:
            config: 配置字典，包含Agent配置
        """
        agent_config = config.get("Agent", {})
        
        self.model_path = agent_config.get("model_path", "Model/Qwen3-0.6B-Q8_0.gguf")
        self.n_threads = agent_config.get("n_threads", 4)
        self.max_iterations = agent_config.get("max_iterations", 10)
        self.context_length = agent_config.get("context_length", 2048)
        self.system_prompt = agent_config.get("system_prompt", "You are a helpful AI assistant.")
        
        # 构建完整模型路径
        if not os.path.isabs(self.model_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.model_path = os.path.join(base_dir, self.model_path)
        
        # 注册的工具
        self.tools = {}
        
        # 加载模型
        Log_Info(self.MODULE_NAME, f"Loading model from {self.model_path}")
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=self.context_length,
            n_threads=self.n_threads,
            verbose=False,
            chat_format="chatml"
        )
        Log_Info(self.MODULE_NAME, "Model loaded successfully")
    
    def Register_Tool(self, name: str, func: callable, description: str):
        """
        注册工具
        
        Args:
            name: 工具名称
            func: 工具函数
            description: 工具描述（JSON格式描述）
        """
        self.tools[name] = {
            "func": func,
            "description": description
        }
        Log_Info(self.MODULE_NAME, f"Registered tool: {name}")
    
    def Run(self, user_message: str, stream: bool = False) -> str:
        """
        处理用户消息，返回结果
        
        Args:
            user_message: 用户消息
            stream: 是否启用流式输出（逐token打印）
        
        Returns:
            处理结果字符串
        """
        Log_Info(self.MODULE_NAME, f"Processing message: {user_message[:50]}...")
        
        # 构建工具描述
        tool_descriptions = self._Build_Tool_Descriptions()
        
        # 构建系统提示词
        system_content = self._Build_System_Prompt(tool_descriptions)
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message}
        ]
        
        # 迭代处理，支持多轮工具调用
        for iteration in range(self.max_iterations):
            Log_Info(self.MODULE_NAME, f"Iteration {iteration + 1}")
            
            if stream:
                print(f"\n[Iteration {iteration + 1}] ", end="", flush=True)
            
            response_text = self._Generate_Response(messages, stream)
            Log_Info(self.MODULE_NAME, f"Model response: {response_text[:100]}...")
            
            # 解析工具调用
            tool_call = self._Parse_Tool_Call(response_text)
            
            if tool_call is None:
                # 无工具调用，清理并返回最终结果
                final_result = self._Clean_Response(response_text)
                
                # 如果清理后内容为空，说明模型只输出了think但没有答案，继续请求
                if not final_result.strip() and iteration < self.max_iterations - 1:
                    Log_Info(self.MODULE_NAME, "Empty response after cleaning, requesting continuation")
                    if stream:
                        print("\n[Requesting continuation...]")
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": "Please provide your final answer directly without using <think> tags."})
                    continue
                
                return final_result if final_result.strip() else response_text
            
            tool_name, tool_args = tool_call
            
            if stream:
                print(f"\n\n[Tool Call] {tool_name} with args: {tool_args}")
            
            # 执行工具
            tool_result = self._Execute_Tool(tool_name, tool_args)
            Log_Info(self.MODULE_NAME, f"Tool {tool_name} result: {tool_result}")
            
            if stream:
                print(f"\n[Tool Result]\n{tool_result}")
            
            # 将工具结果添加到消息历史
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
        
        Log_Info(self.MODULE_NAME, "Max iterations reached")
        return "Maximum tool call iterations reached."
    
    def _Generate_Response(self, messages: list, stream: bool = False) -> str:
        """
        生成LLM响应
        
        Args:
            messages: 消息列表
            stream: 是否启用流式输出
        
        Returns:
            完整响应文本
        """
        if stream:
            # 流式生成
            response_text = ""
            for chunk in self.model.create_chat_completion(
                messages=messages,
                max_tokens=1024,
                stop=["</s>"],
                stream=True
            ):
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    print(content, end="", flush=True)
                    response_text += content
            print()  # 换行
            return response_text.strip()
        else:
            # 非流式生成
            output = self.model.create_chat_completion(
                messages=messages,
                max_tokens=1024,
                stop=["</s>"]
            )
            return output["choices"][0]["message"]["content"].strip()
    
    def _Build_Tool_Descriptions(self) -> str:
        """
        构建工具描述字符串
        
        Returns:
            工具描述
        """
        if not self.tools:
            return "No tools available."
        
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- {name}: {tool['description']}")
        
        return "\n".join(descriptions)
    
    def _Build_System_Prompt(self, tool_descriptions: str) -> str:
        """
        构建系统提示词
        
        Args:
            tool_descriptions: 工具描述
        
        Returns:
            完整系统提示词
        """
        prompt = f"""{self.system_prompt}

You have access to the following tools:
{tool_descriptions}

## CRITICAL RULES
1. You can ONLY call ONE tool per response. Never output multiple JSON objects.
2. If a task requires multiple commands, call the first one, wait for the result, then call the next.
3. To use a tool, respond ONLY with a single JSON object:
{{"tool": "tool_name", "args": {{"command": "your_command"}}}}

4. Do NOT add any text before or after the JSON when calling a tool.
5. After receiving tool results, summarize the information clearly for the user.

## Examples
User: "Check GPU status"
{{"tool": "Execute_Command", "args": {{"command": "nvidia-smi"}}}}

User: "Create a folder called test and list files"
Step 1 (first response): {{"tool": "Execute_Command", "args": {{"command": "mkdir test"}}}}
(Wait for result, then in next response)
Step 2: {{"tool": "Execute_Command", "args": {{"command": "dir"}}}}

User: "What is 2+2?"
This doesn't need a tool. Answer: 2+2 equals 4.

IMPORTANT: ONE tool call per response only!
"""
        return prompt
    
    def _Parse_Tool_Call(self, response: str) -> tuple:
        """
        解析LLM输出中的tool调用
        
        Args:
            response: LLM响应文本
        
        Returns:
            (tool_name, args) 元组，或None表示无工具调用
        """
        # 移除<think>标签内容
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        cleaned = cleaned.strip()
        
        Log_Info(self.MODULE_NAME, f"Parsing cleaned response: {cleaned[:200]}...")
        
        # 尝试从markdown代码块中提取JSON
        code_block_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', cleaned, re.DOTALL)
        if code_block_match:
            try:
                parsed = json.loads(code_block_match.group(1))
                if "tool" in parsed:
                    tool_name = parsed["tool"]
                    tool_args = parsed.get("args", {})
                    if tool_name in self.tools:
                        Log_Info(self.MODULE_NAME, f"Found tool call in code block: {tool_name}")
                        return (tool_name, tool_args)
            except json.JSONDecodeError as e:
                Log_Info(self.MODULE_NAME, f"JSON decode error in code block: {e}")
        
        # 尝试直接从文本中提取JSON对象
        # 寻找以{开头包含"tool"的JSON
        json_start = cleaned.find('{')
        if json_start != -1:
            # 向后查找匹配的}
            brace_count = 0
            json_end = -1
            for i, char in enumerate(cleaned[json_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = json_start + i + 1
                        break
            
            if json_end > json_start:
                json_str = cleaned[json_start:json_end]
                try:
                    parsed = json.loads(json_str)
                    if "tool" in parsed:
                        tool_name = parsed["tool"]
                        tool_args = parsed.get("args", {})
                        if tool_name in self.tools:
                            Log_Info(self.MODULE_NAME, f"Found tool call: {tool_name}")
                            return (tool_name, tool_args)
                except json.JSONDecodeError as e:
                    Log_Info(self.MODULE_NAME, f"JSON decode error: {e}")
        
        Log_Info(self.MODULE_NAME, "No tool call found")
        return None
    
    def _Clean_Response(self, response: str) -> str:
        """
        清理响应文本，移除<think>标签等
        
        Args:
            response: 原始响应文本
        
        Returns:
            清理后的文本
        """
        # 移除完整的<think>...</think>标签及其内容
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # 移除未闭合的<think>标签（从<think>到结尾）
        cleaned = re.sub(r'<think>.*$', '', cleaned, flags=re.DOTALL)
        
        # 移除多余空白
        cleaned = cleaned.strip()
        return cleaned
    
    def _Execute_Tool(self, tool_name: str, args: dict) -> str:
        """
        执行指定tool
        
        Args:
            tool_name: 工具名称
            args: 工具参数
        
        Returns:
            工具执行结果字符串
        """
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found."
        
        try:
            func = self.tools[tool_name]["func"]
            result = func(**args)
            return str(result)
        except Exception as e:
            Log_Info(self.MODULE_NAME, f"Tool execution error: {e}")
            return f"Error executing tool: {e}"
