#Presented by KeJi
#Date : 2026-01-19

"""
AddAgent - 使用llama-cpp-python的加法Agent
"""

import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llama_cpp import Llama
from API.Add import Add, API_DESCRIPTION


class Add_Agent:
    """
    加法Agent - 使用LLM理解用户意图并调用Add API
    """
    
    MODEL_PATH = "Model/Qwen3-0.6B-Q8_0.gguf"
    DEBUG = True
    
    def __init__(self, model_path: str = None):
        """
        初始化Agent
        
        Args:
            model_path: 模型文件路径，默认使用MODEL_PATH
        """
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                self.MODEL_PATH
            )
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False,
            chat_format="chatml"
        )
        
        self.tools = [API_DESCRIPTION]
    
    def _Build_Messages(self, user_input: str) -> list:
        """
        构建聊天消息
        
        Args:
            user_input: 用户输入
        
        Returns:
            消息列表
        """
        system_prompt = """你是一个加法计算助手。当用户的问题涉及到两个数量相加时，提取数字并输出JSON。

判断规则：
- 涉及数量累加、总和、合计的问题都是加法请求
- "有X个，又买了Y个"、"X加Y"、"X+Y"等都是加法
- 提取问题中的两个数字作为a和b

输出格式：
- 加法请求: {"action": "Add", "a": 数字1, "b": 数字2}
- 非加法: {"action": "none", "message": "非加法请求"}

示例：
用户：1+2等于多少
{"action": "Add", "a": 1, "b": 2}

用户：我有3个苹果，买了5个，现在有几个？
{"action": "Add", "a": 3, "b": 5}

用户：小明有10元，妈妈给了20元，共多少钱？
{"action": "Add", "a": 10, "b": 20}

只输出JSON。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input + " /no_think"}
        ]
        
        return messages
    
    def _Parse_Response(self, response: str) -> dict:
        """
        解析LLM响应
        
        Args:
            response: LLM响应文本
        
        Returns:
            解析后的字典
        """
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return {"action": "none", "message": f"解析失败，原始响应：{response[:100]}"}
    
    def Run(self, user_input: str) -> str:
        """
        运行Agent处理用户输入
        
        Args:
            user_input: 用户输入
        
        Returns:
            处理结果
        """
        messages = self._Build_Messages(user_input)
        
        output = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=256,
            stop=["</s>"]
        )
        
        response_text = output["choices"][0]["message"]["content"].strip()
        
        if self.DEBUG:
            print(f"[DEBUG] 模型原始响应: {response_text}")
        
        parsed = self._Parse_Response(response_text)
        
        if parsed.get("action") == "Add":
            try:
                a = float(parsed.get("a", 0))
                b = float(parsed.get("b", 0))
                result = Add(a, b)
                return f"计算结果：{a} + {b} = {result}"
            except (ValueError, TypeError) as e:
                return f"参数错误：{e}"
        else:
            return parsed.get("message", "无法处理的请求")


if __name__ == "__main__":
    print("加法Agent - 输入'退出'或'exit'结束")
    print("正在加载模型...")
    
    agent = Add_Agent()
    
    print("模型加载完成！请输入您的计算请求：")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("用户> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["退出", "exit", "quit", "q"]:
                print("再见！")
                break
            
            result = agent.Run(user_input)
            print(f"Agent> {result}")
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except EOFError:
            print("\n再见！")
            break
