#Presented by KeJi
#Date : 2026-01-19

"""
Scheduler模组测试脚本
测试Scheduler的基本功能，使用MockAgent
"""

import sys
import os
import time
import threading
import json

# 添加Src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Src'))

from Scheduler_Daemon.scheduler import Scheduler, mock_agent
from Log.Log import Log_Info


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Src', 'Config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 添加Scheduler配置（用于测试的短间隔）
    config["Scheduler"] = {
        "poll_interval_idle": 10,      # 10秒检查一次（测试用，实际可设更长）
        "poll_interval_active": 3,     # 3秒检查一次
        "active_timeout": 30,          # 30秒无活动返回Idle
        "agent_persistence": False,    # 不持久化Agent
        "agent_timeout": 60            # Agent响应超时60秒
    }
    
    return config


def test_scheduler_init():
    """测试Scheduler初始化"""
    print("\n=== 测试1: Scheduler初始化 ===")
    
    config = load_config()
    scheduler = Scheduler(config, agent_target=mock_agent)
    
    assert scheduler.poll_interval_idle == 10
    assert scheduler.poll_interval_active == 3
    assert scheduler.active_timeout == 30
    assert scheduler.state == Scheduler.STATE_IDLE
    assert scheduler.agent is None
    
    print("✓ Scheduler初始化成功")
    print(f"  - poll_interval_idle: {scheduler.poll_interval_idle}s")
    print(f"  - poll_interval_active: {scheduler.poll_interval_active}s")
    print(f"  - active_timeout: {scheduler.active_timeout}s")
    print(f"  - state: {scheduler.state}")


def test_mock_agent_communication():
    """测试与MockAgent的通信"""
    print("\n=== 测试2: MockAgent通信 ===")
    
    from multiprocessing import Process, Queue
    import queue
    
    to_agent = Queue()
    from_agent = Queue()
    
    # 启动MockAgent
    agent_process = Process(target=mock_agent, args=(to_agent, from_agent))
    agent_process.start()
    print(f"✓ MockAgent启动, PID={agent_process.pid}")
    
    # 等待Agent发送ready消息
    try:
        ready_msg = from_agent.get(timeout=10)
        if ready_msg.get("type") == "ready":
            print("✓ 收到Agent ready消息")
        else:
            print(f"✗ 收到意外消息: {ready_msg}")
    except queue.Empty:
        print("✗ 等待ready消息超时")
    
    # 发送测试消息
    test_message = {
        "type": "user_message",
        "content": "这是一条测试消息",
        "timestamp": time.time()
    }
    to_agent.put(test_message)
    print("✓ 测试消息已发送，等待响应...")
    
    # 等待响应（MockAgent会等待5秒）
    try:
        response = from_agent.get(timeout=10)
        print(f"✓ 收到响应: {response}")
    except queue.Empty:
        print("✗ 等待响应超时")
    
    # 发送关闭指令
    to_agent.put({"type": "shutdown"})
    agent_process.join(timeout=5)
    
    if agent_process.is_alive():
        agent_process.terminate()
        print("✗ MockAgent未正常退出，已强制终止")
    else:
        print("✓ MockAgent正常退出")


def test_scheduler_short_run():
    """测试Scheduler短时间运行"""
    print("\n=== 测试3: Scheduler短时间运行 ===")
    
    config = load_config()
    # 使用更短的间隔进行测试
    config["Scheduler"]["poll_interval_idle"] = 2
    
    scheduler = Scheduler(config, agent_target=mock_agent)
    
    # 在后台线程运行Scheduler
    def run_scheduler():
        scheduler.start()
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    print("✓ Scheduler已在后台启动")
    
    # 运行几秒钟
    print("  等待5秒...")
    time.sleep(5)
    
    # 停止Scheduler
    print("  发送停止信号...")
    scheduler.shutdown()
    
    scheduler_thread.join(timeout=10)
    
    if scheduler_thread.is_alive():
        print("✗ Scheduler未能正常停止")
    else:
        print("✓ Scheduler正常停止")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("Scheduler模组测试")
    print("=" * 50)
    
    try:
        test_scheduler_init()
        test_mock_agent_communication()
        test_scheduler_short_run()
        
        print("\n" + "=" * 50)
        print("所有测试完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
