#Presented by KeJi
#Date : 2026-01-20

"""
Scheduler_Daemon 后台模组
负责检查邮箱内容，唤醒agent处理任务
"""

import time
import signal
import threading
import shutil
import atexit
from multiprocessing import Process, Queue
import queue
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Log.Log import Log_Info, Cleanup_Old_Logs
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
            agent_target: Agent进程的目标函数，签名为 agent_target(config, to_agent_queue, from_agent_queue)
        """
        self._config = config  # 保存完整config供Agent使用
        scheduler_config = config.get("Scheduler", {})
        
        # 配置属性
        self.poll_interval_idle = scheduler_config.get("poll_interval_idle", 60)
        self.poll_interval_active = scheduler_config.get("poll_interval_active", 5)
        self.active_timeout = scheduler_config.get("active_timeout", 300)
        self.agent_persistence = scheduler_config.get("agent_persistence", False)
        self.agent_timeout = scheduler_config.get("agent_timeout", 120)
        
        # 临时工作目录配置
        tmp_config = config.get("Tmp_WorkingSpace", {})
        self._tmp_workspace = tmp_config.get("workspace", ".columba_tmp_workspace")
        
        # 运行时属性
        self.state = self.STATE_IDLE
        self.to_agent_queue = Queue()
        self.from_agent_queue = Queue()
        self.agent = None
        self.last_email_time = 0
        self.last_agent_response_time = 0
        self.stop_event = threading.Event()
        self._last_log_cleanup_time = 0  # 上次日志清理时间
        
        # Agent目标函数
        self._agent_target = agent_target
        
        # Comm实例
        self._comm = Comm(config)
        
        # 初始化临时工作目录
        self._init_tmp_workspace()
        
        # 注册atexit清理函数作为兜底
        atexit.register(self._cleanup_tmp_workspace)
        
        # 清理过期日志
        log_config = config.get("Log", {})
        cleanup_days = log_config.get("clean_up_interval_days", 0)
        if cleanup_days > 0:
            Cleanup_Old_Logs(cleanup_days)
        
        Log_Info("Scheduler", f"初始化完成: idle间隔={self.poll_interval_idle}s, active间隔={self.poll_interval_active}s")
    
    def _init_tmp_workspace(self):
        """
        初始化临时工作目录
        启动时清理残留目录，然后创建新目录
        """
        # 构建完整路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._tmp_workspace_path = os.path.join(base_dir, self._tmp_workspace)
        
        # 清理可能存在的残留目录
        if os.path.exists(self._tmp_workspace_path):
            Log_Info("Scheduler", f"清理残留临时目录: {self._tmp_workspace_path}")
            try:
                shutil.rmtree(self._tmp_workspace_path)
            except Exception as e:
                Log_Info("Scheduler", f"清理残留目录失败: {e}")
        
        # 创建新目录
        try:
            os.makedirs(self._tmp_workspace_path, exist_ok=True)
            Log_Info("Scheduler", f"临时工作目录已创建: {self._tmp_workspace_path}")
        except Exception as e:
            Log_Info("Scheduler", f"创建临时目录失败: {e}")
            raise
    
    def _cleanup_tmp_workspace(self):
        """
        清理临时工作目录
        """
        if hasattr(self, '_tmp_workspace_path') and self._tmp_workspace_path:
            if os.path.exists(self._tmp_workspace_path):
                try:
                    shutil.rmtree(self._tmp_workspace_path)
                    Log_Info("Scheduler", f"临时工作目录已清理: {self._tmp_workspace_path}")
                except Exception as e:
                    Log_Info("Scheduler", f"清理临时目录失败: {e}")
    
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
            args=(self._config, self.to_agent_queue, self.from_agent_queue)
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
    
    def _check_and_cleanup_logs(self):
        """检查并执行日志清理，每24小时执行一次"""
        current_time = time.time()
        ONE_DAY = 86400  # 24小时的秒数
        
        if current_time - self._last_log_cleanup_time >= ONE_DAY:
            log_config = self._config.get("Log", {})
            cleanup_days = log_config.get("clean_up_interval_days", 0)
            if cleanup_days > 0:
                Cleanup_Old_Logs(cleanup_days)
            self._last_log_cleanup_time = current_time
    
    def _build_email_content(self, agent_content: str, output_files: list) -> str:
        """
        构建邮件内容，包含Agent响应和命令输出文件内容
        
        Args:
            agent_content: Agent响应内容
            output_files: 命令输出文件路径列表
        
        Returns:
            完整邮件内容
        """
        parts = [agent_content]
        
        if output_files:
            parts.append("\n" + "=" * 50)
            parts.append("命令执行输出详情：")
            parts.append("=" * 50)
            
            # Windows使用gbk编码，Unix使用utf-8
            file_encoding = 'gbk' if os.name == 'nt' else 'utf-8'
            
            for i, file_path in enumerate(output_files, 1):
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding=file_encoding, errors='replace') as f:
                            content = f.read()
                        
                        filename = os.path.basename(file_path)
                        parts.append(f"\n--- [{i}] {filename} ---")
                        parts.append(content if content.strip() else "[无输出]")
                    else:
                        Log_Info("Scheduler", f"输出文件不存在: {file_path}")
                except Exception as e:
                    Log_Info("Scheduler", f"读取输出文件失败: {file_path}, {e}")
                    parts.append(f"\n--- [{i}] 读取失败: {e} ---")
        
        return "\n".join(parts)
    
    def start(self):
        """
        开始运行Scheduler主循环
        """
        self._setup_signal_handlers()
        Log_Info("Scheduler", "Scheduler开始运行")
        
        while not self.stop_event.is_set():
            # 检查日志清理（每24小时执行一次）
            self._check_and_cleanup_logs()
            
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
                
                # 将Agent响应通过邮件发送给用户（包含命令输出文件内容）
                if response.get("type") == "response":
                    reply_content = response.get("content", "")
                    output_files = response.get("output_files", [])
                    email_content = self._build_email_content(reply_content, output_files)
                    self._comm.Send(email_content)
                    Log_Info("Scheduler", f"已将响应通过邮件发送给用户，包含{len(output_files)}个输出文件")
            else:
                Log_Info("Scheduler", "Agent响应超时，返回Idle状态")
                self._comm.Send("抱歉，处理您的请求时超时，请稍后重试。")
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
                
                # 将Agent响应通过邮件发送给用户（包含命令输出文件内容）
                if response.get("type") == "response":
                    reply_content = response.get("content", "")
                    output_files = response.get("output_files", [])
                    email_content = self._build_email_content(reply_content, output_files)
                    self._comm.Send(email_content)
                    Log_Info("Scheduler", f"已将响应通过邮件发送给用户，包含{len(output_files)}个输出文件")
        
        # 检查是否有Agent主动发来的消息
        while True:
            response = self._try_get_agent_response()
            if response:
                self.last_agent_response_time = time.time()
                # 将Agent响应通过邮件发送给用户（包含命令输出文件内容）
                if response.get("type") == "response":
                    reply_content = response.get("content", "")
                    output_files = response.get("output_files", [])
                    email_content = self._build_email_content(reply_content, output_files)
                    self._comm.Send(email_content)
                    Log_Info("Scheduler", f"已将Agent主动响应通过邮件发送给用户，包含{len(output_files)}个输出文件")
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
        
        # 清理临时工作目录
        self._cleanup_tmp_workspace()
        
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
