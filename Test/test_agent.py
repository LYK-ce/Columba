#Presented by KeJi
#Date : 2026-01-20

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
from API.Exec import Execute_Command, API_DESCRIPTION, Set_Shell


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
    print("Agent Tool Calling Test (Persistent Shell + File Output)")
    print("=" * 60)
    
    # 加载配置
    print("\n[1] Loading config...")
    config = Load_Config()
    print("Config loaded successfully")
    
    # 获取工作目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    tmp_config = config.get("Tmp_WorkingSpace", {})
    tmp_workspace = os.path.join(base_dir, tmp_config.get("workspace", ".columba_tmp_workspace"))
    
    target_config = config.get("Target_Workspace", {})
    target_workspace = target_config.get("target_workspace", os.getcwd())
    
    print(f"Tmp workspace: {tmp_workspace}")
    print(f"Target workspace: {target_workspace}")
    
    # 创建临时工作目录
    os.makedirs(tmp_workspace, exist_ok=True)
    
    agent = None
    try:
        # 初始化Agent（会自动创建持久化Shell，输出保存到tmp_workspace）
        print("\n[2] Initializing Agent with persistent shell...")
        agent = Agent(config, workspace=tmp_workspace, target_workspace=target_workspace)
        print("Agent initialized")
        
        # 设置Exec模块的Shell引用
        print("\n[3] Setting shell reference for Exec module...")
        Set_Shell(agent.shell)
        print("Shell reference set")
        
        # 注册Execute_Command工具
        print("\n[4] Registering Execute_Command tool...")
        agent.Register_Tool(
            name="Execute_Command",
            func=Execute_Command,
            description=API_DESCRIPTION
        )
        print("Tool registered")
        
        # 测试用户输入（单任务测试）
        user_input = "请帮我查看当前的GPU状况"
        print(f"\n[5] Test input: '{user_input}'")
        print("-" * 60)
        
        # 运行Agent
        print("\n[6] Running Agent...")
        print("=" * 60)
        result = agent.Run(user_input)
        
        # 输出最终结果
        print("\n" + "=" * 60)
        print("Final Result:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
    finally:
        # 清理资源
        if agent is not None:
            print("\n[7] Shutting down Agent...")
            agent.Shutdown()
            print("Agent shutdown complete")
    
    print("\n[Test Completed]")


if __name__ == "__main__":
    main()
