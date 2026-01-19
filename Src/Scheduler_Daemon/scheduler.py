#Presented by KeJi
#Date : 2026-01-19

"""
Scheduler_Daemon 后台模组
负责检查邮箱内容，唤醒agent处理任务
"""

import time
import signal
import threading
from multiprocessing import Process, Queue
import queue
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Log.Log import Log_Info
from Comm.Email import Comm


class Scheduler:
    """Scheduler后台守护进程类"""
    
    # 状态常量
    STATE_IDLE = "Idle"
    STATE_ACTIVE = "Active"
    
    def __init__(self, config, agent_target=None):
        """
        根据config配置初始化属性
        
        Args:
            config: 配置字典
            agent_target: Agent进程的目标函数，签名为 agent_target(to_agent_queue, from_agent_queue)
        """
        scheduler_config = config.get("Scheduler", {})
        
        # 配置属性
        self.poll_interval_idle = scheduler_config.get("poll_interval_idle", 60)
        self.poll_interval_active = scheduler_config.get("poll_interval_active", 5)
        self.active_timeout = scheduler_config.get("active_timeout", 300)
        self.agent_persistence = scheduler_config.get("agent_persistence", False)
        self.agent_timeout = scheduler_config.get("agent_timeout", 120)
        
        # 运行时属性
        self.state = self.STATE_IDLE
        self.to_agent_queue = Queue()
        self.from_agent_queue = Queue()
        self.agent = None
        self.last_email_time = 0
        self.last_agent_response_time = 0
        self.stop_event = threading.Event()
        
        # Agent目标函数
        self._agent_target = agent_target
        
        # Comm实例
        self._comm = Comm(config)
        
        Log_Info("Scheduler", f"初始化完成: idle间隔={self.poll_interval_idle}s, active间隔={self.poll_interval_active}s")
    
    def _setup_signal_handlers(self):
        """设置信号处理器（仅在主线程中有效）"""
        # 检查是否在主线程中，signal只能在主线程设置
        if threading.current_thread() is not threading.main_thread():
            Log_Info("Scheduler", "非主线程运行，跳过信号处理器设置")
            return
        
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        Log_Info("Scheduler", "信号处理器已设置")
    
    def _handle_signal(self, signum, frame):
        """信号处理函数"""
        Log_Info("Scheduler", f"收到信号 {signum}，准备退出")
        self.shutdown()
    
    def _start_agent(self):
        """启动Agent进程并等待其就绪"""
        if self._agent_target is None:
            Log_Info("Scheduler", "错误: agent_target未设置")
            return False
        
        if self.agent and self.agent.is_alive():
            Log_Info("Scheduler", "Agent进程已在运行")
            return True
        
        self.agent = Process(
            target=self._agent_target,
            args=(self.to_agent_queue, self.from_agent_queue)
        )
        self.agent.start()
        Log_Info("Scheduler", f"Agent进程已启动, PID={self.agent.pid}")
        
        # 等待Agent发送ready消息
        Log_Info("Scheduler", "等待Agent就绪...")
        try:
            ready_msg = self.from_agent_queue.get(timeout=self.agent_timeout)
            if ready_msg.get("type") == "ready":
                Log_Info("Scheduler", "Agent已就绪")
                return True
            else:
                Log_Info("Scheduler", f"收到意外消息: {ready_msg.get('type')}")
                return False
        except queue.Empty:
            Log_Info("Scheduler", "等待Agent就绪超时")
            self._stop_agent()
            return False
    
    def _stop_agent(self):
        """停止Agent进程"""
        if self.agent is None:
            return
        
        if not self.agent.is_alive():
            self.agent = None
            return
        
        # 发送关闭指令
        self.to_agent_queue.put({"type": "shutdown"})
        
        # 等待进程退出
        self.agent.join(timeout=10)
        
        if self.agent.is_alive():
            Log_Info("Scheduler", "Agent进程未响应，强制终止")
            self.agent.terminate()
            self.agent.join(timeout=5)
        
        Log_Info("Scheduler", "Agent进程已停止")
        self.agent = None
    
    def _send_to_agent(self, message):
        """发送消息给Agent"""
        self.to_agent_queue.put({
            "type": "user_message",
            "content": message,
            "timestamp": time.time()
        })
        Log_Info("Scheduler", f"消息已发送给Agent: {message[:50]}...")
    
    def _check_agent_response(self):
        """检查Agent响应"""
        try:
            response = self.from_agent_queue.get(timeout=self.agent_timeout)
            self.last_agent_response_time = time.time()
            Log_Info("Scheduler", f"收到Agent响应: type={response.get('type')}")
            return response
        except queue.Empty:
            Log_Info("Scheduler", "等待Agent响应超时")
            return None
    
    def _try_get_agent_response(self):
        """非阻塞检查Agent响应"""
        try:
            response = self.from_agent_queue.get_nowait()
            self.last_agent_response_time = time.time()
            return response
        except queue.Empty:
            return None
    
    def _check_timeout(self):
        """检查是否超时需要返回Idle状态"""
        current_time = time.time()
        email_timeout = current_time - self.last_email_time > self.active_timeout
        agent_timeout = current_time - self.last_agent_response_time > self.active_timeout
        
        return email_timeout and agent_timeout
    
    def start(self):
        """
        开始运行Scheduler主循环
        """
        self._setup_signal_handlers()
        Log_Info("Scheduler", "Scheduler开始运行")
        
        while not self.stop_event.is_set():
            if self.state == self.STATE_IDLE:
                self._run_idle_state()
            else:
                self._run_active_state()
        
        Log_Info("Scheduler", "Scheduler主循环结束")
    
    def _run_idle_state(self):
        """Idle状态处理"""
        # 等待poll_interval_idle
        if self.stop_event.wait(self.poll_interval_idle):
            return  # 收到停止信号
        
        # 检查邮件
        email_content = self._comm.Try_Receive()
        
        if email_content:
            Log_Info("Scheduler", "收到用户邮件，切换到Active状态")
            self.last_email_time = time.time()
            
            # 启动Agent（如果需要）
            if not self._start_agent():
                Log_Info("Scheduler", "Agent启动失败，保持Idle状态")
                return
            
            # 发送消息给Agent
            self._send_to_agent(email_content)
            
            # 等待Agent响应
            response = self._check_agent_response()
            if response:
                self.state = self.STATE_ACTIVE
                self.last_agent_response_time = time.time()
            else:
                Log_Info("Scheduler", "Agent响应超时，返回Idle状态")
                if not self.agent_persistence:
                    self._stop_agent()
    
    def _run_active_state(self):
        """Active状态处理"""
        # 等待poll_interval_active
        if self.stop_event.wait(self.poll_interval_active):
            return  # 收到停止信号
        
        # 检查邮件
        email_content = self._comm.Try_Receive()
        
        if email_content:
            Log_Info("Scheduler", "Active状态收到新邮件")
            self.last_email_time = time.time()
            
            # 发送消息给Agent
            self._send_to_agent(email_content)
            
            # 等待Agent响应
            response = self._check_agent_response()
            if response:
                self.last_agent_response_time = time.time()
        
        # 检查是否有Agent主动发来的消息
        while True:
            response = self._try_get_agent_response()
            if response:
                self.last_agent_response_time = time.time()
            else:
                break
        
        # 检查超时
        if self._check_timeout():
            Log_Info("Scheduler", "超时，切换到Idle状态")
            self.state = self.STATE_IDLE
            
            if not self.agent_persistence:
                self._stop_agent()
    
    def shutdown(self):
        """优雅退出"""
        Log_Info("Scheduler", "开始优雅退出")
        self.stop_event.set()
        
        if self.agent and self.agent.is_alive():
            self._stop_agent()
        
        Log_Info("Scheduler", "Scheduler已退出")


def mock_agent(to_agent_queue, from_agent_queue):
    """
    Mock Agent进程
    用于测试Scheduler功能
    启动后发送ready消息，收到用户消息后等待5秒返回响应
    """
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from Log.Log import Log_Info
    
    Log_Info("MockAgent", "Mock Agent启动")
    
    # 发送ready消息通知Scheduler已准备就绪
    from_agent_queue.put({
        "type": "ready",
        "timestamp": time.time()
    })
    Log_Info("MockAgent", "已发送ready消息")
    
    while True:
        try:
            msg = to_agent_queue.get(timeout=30)
            
            if msg.get("type") == "shutdown":
                Log_Info("MockAgent", "收到关闭指令，退出")
                break
            
            if msg.get("type") == "user_message":
                Log_Info("MockAgent", f"收到用户消息: {msg.get('content', '')[:50]}")
                
                # 模拟处理（等待5秒）
                time.sleep(5)
                
                # 返回响应
                from_agent_queue.put({
                    "type": "response",
                    "content": f"已处理消息: {msg.get('content', '')[:20]}...",
                    "timestamp": time.time()
                })
                Log_Info("MockAgent", "响应已发送")
        
        except queue.Empty:
            continue
        except Exception as e:
            Log_Info("MockAgent", f"错误: {e}")
            break
    
    Log_Info("MockAgent", "Mock Agent退出")
