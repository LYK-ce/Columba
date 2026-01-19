#Presented by KeJi
#Date : 2026-01-19

"""
Columba Main Entry - 主入口文件
启动Scheduler后台进程，整合Agent执行器
"""

import json
import os
import sys

# 添加Src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Log.Log import Log_Info
from Scheduler_Daemon.scheduler import Scheduler
from Agent.Agent_Process import Agent_Main


MODULE_NAME = "Main"


def Load_Config() -> dict:
    """
    加载配置文件
    
    Returns:
        配置字典
    """
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Config", "config.json"
    )
    
    Log_Info(MODULE_NAME, f"Loading config from {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    Log_Info(MODULE_NAME, "Config loaded successfully")
    return config


def main():
    """
    主函数 - 启动Columba系统
    """
    print("=" * 60)
    print("Columba - AI Task Agent System")
    print("=" * 60)
    
    Log_Info(MODULE_NAME, "Columba starting...")
    
    # 加载配置
    config = Load_Config()
    
    # 创建Scheduler，使用真正的Agent_Main作为agent_target
    Log_Info(MODULE_NAME, "Initializing Scheduler with Agent")
    scheduler = Scheduler(config, agent_target=Agent_Main)
    
    # 启动Scheduler主循环
    print("\n[Columba] System started. Press Ctrl+C to stop.")
    print("[Columba] Waiting for incoming emails...")
    print("-" * 60)
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        Log_Info(MODULE_NAME, "Received keyboard interrupt")
        print("\n[Columba] Shutting down...")
    finally:
        scheduler.shutdown()
        Log_Info(MODULE_NAME, "Columba stopped")
        print("[Columba] System stopped.")


if __name__ == "__main__":
    main()
