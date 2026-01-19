#Presented by KeJi
#Date : 2026-01-19

"""
Agent_Process - Agent进程管理类
负责接收scheduler消息，调用Agent处理，返回结果
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Log.Log import Log_Info
from Agent.Agent import Agent
from API.Exec import Execute_Command, API_DESCRIPTION


class Agent_Process:
    """
    Agent进程类 - 管理Agent生命周期和消息通信
    """
    
    MODULE_NAME = "Agent_Process"
    
    def __init__(self, config: dict, to_agent_queue, from_agent_queue):
        """
        初始化Agent进程
        
        Args:
            config: 配置字典
            to_agent_queue: Scheduler→Agent消息队列
            from_agent_queue: Agent→Scheduler消息队列
        """
        self.config = config
        self.to_agent_queue = to_agent_queue
        self.from_agent_queue = from_agent_queue
        self.running = False
        self.agent = None
        
        Log_Info(self.MODULE_NAME, "Initializing Agent_Process")
    
    def _Load_Agent(self):
        """
        加载Agent实例并注册工具
        """
        Log_Info(self.MODULE_NAME, "Loading Agent")
        self.agent = Agent(self.config)
        
        # 注册Execute_Command工具
        self.agent.Register_Tool(
            name="Execute_Command",
            func=Execute_Command,
            description=API_DESCRIPTION
        )
        Log_Info(self.MODULE_NAME, "Agent loaded and tools registered")
    
    def _Send_Ready(self):
        """
        发送ready消息给Scheduler
        """
        message = {
            "type": "ready",
            "timestamp": time.time()
        }
        self.from_agent_queue.put(message)
        Log_Info(self.MODULE_NAME, "Sent ready message")
    
    def _Process_Message(self, message: dict):
        """
        处理来自Scheduler的消息
        
        Args:
            message: 消息字典
        """
        msg_type = message.get("type")
        
        if msg_type == "user_message":
            content = message.get("content", "")
            Log_Info(self.MODULE_NAME, f"Processing user message: {content[:50]}...")
            
            # 调用Agent处理
            result = self.agent.Run(content)
            
            # 发送响应
            response = {
                "type": "response",
                "content": result,
                "timestamp": time.time()
            }
            self.from_agent_queue.put(response)
            Log_Info(self.MODULE_NAME, "Sent response")
        
        elif msg_type == "shutdown":
            Log_Info(self.MODULE_NAME, "Received shutdown command")
            self.running = False
    
    def Run(self):
        """
        主循环，接收并处理消息
        """
        Log_Info(self.MODULE_NAME, "Starting main loop")
        self.running = True
        
        # 加载Agent
        self._Load_Agent()
        
        # 发送ready消息
        self._Send_Ready()
        
        while self.running:
            try:
                # 阻塞等待消息，超时1秒检查running状态
                message = self.to_agent_queue.get(timeout=1.0)
                self._Process_Message(message)
            except Exception:
                # 队列超时或其他异常，继续循环
                continue
        
        Log_Info(self.MODULE_NAME, "Main loop ended")
    
    def Shutdown(self):
        """
        关闭Agent进程
        """
        Log_Info(self.MODULE_NAME, "Shutting down")
        self.running = False


def Agent_Main(config: dict, to_agent_queue, from_agent_queue):
    """
    Agent进程主入口函数
    
    Args:
        config: 配置字典
        to_agent_queue: Scheduler→Agent消息队列
        from_agent_queue: Agent→Scheduler消息队列
    """
    Log_Info("Agent_Main", "Agent process starting")
    
    try:
        agent_process = Agent_Process(config, to_agent_queue, from_agent_queue)
        agent_process.Run()
    except Exception as e:
        Log_Info("Agent_Main", f"Agent process error: {e}")
        # 发送错误响应
        try:
            from_agent_queue.put({
                "type": "error",
                "content": str(e),
                "timestamp": time.time()
            })
        except Exception:
            pass
    
    Log_Info("Agent_Main", "Agent process ended")
