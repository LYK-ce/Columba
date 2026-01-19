#Presented by KeJi
#Date : 2026-01-19

"""
test_agent - 测试Agent工具调用功能
用户输入为获取当前GPU状况，Agent应调用nvidia-smi获取信息
"""

import os
import sys
import json

# 添加Src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Src"))

from Agent.Agent import Agent
from API.Exec import Execute_Command, API_DESCRIPTION


def Load_Config() -> dict:
    """
    加载配置文件
    
    Returns:
        配置字典
    """
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Src", "Config", "config.json"
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """
    主测试函数
    """
    print("=" * 60)
    print("Agent Tool Calling Test")
    print("=" * 60)
    
    # 加载配置
    print("\n[1] Loading config...")
    config = Load_Config()
    print("Config loaded successfully")
    
    # 初始化Agent
    print("\n[2] Initializing Agent...")
    agent = Agent(config)
    print("Agent initialized")
    
    # 注册Execute_Command工具
    print("\n[3] Registering Execute_Command tool...")
    agent.Register_Tool(
        name="Execute_Command",
        func=Execute_Command,
        description=API_DESCRIPTION
    )
    print("Tool registered")
    
    # 测试用户输入（单任务测试）
    user_input = "请帮我查看当前的GPU状况"
    print(f"\n[4] Test input: '{user_input}'")
    print("-" * 60)
    
    # 运行Agent（启用流式输出）
    print("\n[5] Running Agent (streaming mode)...")
    print("=" * 60)
    result = agent.Run(user_input, stream=True)
    
    # 输出最终结果
    print("\n" + "=" * 60)
    print("Final Result:")
    print("=" * 60)
    print(result)
    print("=" * 60)
    
    print("\n[Test Completed]")


if __name__ == "__main__":
    main()
