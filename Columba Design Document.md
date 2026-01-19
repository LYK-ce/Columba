# Columba 设计文档

## 项目结构



### Model
模型文件存储目录，存放GGUF格式的大语言模型文件。Agent模组从此目录加载模型。该目录不纳入git版本控制。

### Src
源代码目录，包含以下子模组：
- Agent/ - Agent执行器模组
- API/ - 方法调用模组
- Comm/ - 通信模组
- Config/ - 配置文件
- Log/ - 日志模组
- Scheduler_Daemon/ - 后台调度模组
- main.py - 程序入口

### Tool
工具脚本目录，提供辅助功能：
- download_model.py - 从ModelScope下载GGUF模型到Model目录
- doc.md - 工具说明文档

## Columba Design

### Agent 执行器模组
Agent模组是整个Columba项目的执行器。它负责接收用户传递来的消息，然后将内容转换成各种方法调用。它需要与scheduler进程同步配合，scheduler进程将会把用户的信息传递给它，agent处理完毕后会通知scheduler继续执行。

#### 文件
Src/Agent
   Agent_Process.py  Agent进程脚本
   Agent.py          Agent脚本，用于配置Agent，Tool Calling等

#### Agent_Process类
Class Agent_Process
Agent进程类

##### 属性  
   - to_agent_queue
   - from_agent_queue
   - agent     具体的agent指针

##### 方法
1. init(config)
   从config文件中配置属性,加载模型
2. run()
   主循环，在这里接收来自scheduler的消息，然后处理，调用各种方法等
3. _send_ready()
4. _process_message()
5. shutdown()
6. agent_main()进程主入口
   
#### Agent类
Class Agent
Agent类

##### 属性
   - model_path 模型路径，agent从这个路径中加载对应的模型
   - n_threads 使用多少个线程 
   - max_iteration   tool调用最大轮数
   - conext_length   上下文长度限制
   - system_prompt   系统提示词  
   
   - model     llama.cpp具体模型实例
   - tools     注册的工具
   

##### 方法
1. __init__(self, config):
   """加载模型，配置tools"""
    
2. register_tool(self, name, func, description):
   """注册工具"""
    
3. run(self, user_message)
   """处理用户消息，返回结果"""
   解析用户的指令，可能会调用多个tool。
    
4. _parse_tool_call(self, response) -> tuple:
   """解析LLM输出中的tool调用"""
    
5. _execute_tool(self, tool_name, args) -> str:
   """执行指定tool"""



### API 方法调用模组
API模组为当前的Agent提供了我们所需要的功能。

#### 文件
Src/API
   - Shell.py 命令行抽象，所有工具调用将会通过这里变成各种命令执行。后续还需要添加命令检测确保安全等等。
   - Exec.py  命令执行工具
#### Shell 
   命令行抽象，封装subprocess类，所有工具调用通过这里变成各种具体的命令，后续添加安全检测
#### Exec 命令执行工具
   工具API封装，包含执行agent转换成的对应命令。
   Execute_Command(command) 供Agent调用
   API_DESCRIPTION 工具描述
   调用Shell.Execute()获取结果

### Scheduler_Daemon 后台模组
Scheduler_Daemon模组，是整个Columba项目的后台进程。它运行在后台，负责检查邮箱内容，以及唤醒agent呼叫它处理任务等。scheduler daemon根据用户配置，每隔一定时间检查一次邮箱，如果没有邮件那么就什么都不做，如果有邮件，就唤醒agent，等待agent加载完毕后将用户的指令发送给agent开始处理，同时将轮询次数调整为5 s。根据用户配置，如果一定时间内没有再次收到用户的邮件，那么就恢复到原来的检查次数，然后关闭当前的agent。

#### 文件
Src/Scheduler_Daemon
   - scheduler.py

#### 类
Class Scheduler

##### 属性
| 属性 | 类型 | 说明 |
|------|------|------|
| poll_interval_idle | int | Idle状态时的poll间隔（秒） |
| poll_interval_active | int | Active状态时的poll间隔（秒） |
| active_timeout | int | 超过此时间无活动则返回Idle状态（秒） |
| agent_persistence | bool | 是否持久化agent进程 |
| agent_timeout | int | agent响应超时时间（秒） |
| state | str | 状态值 {"Idle", "Active"} |
| to_agent_queue | Queue | Scheduler→Agent 消息队列 |
| from_agent_queue | Queue | Agent→Scheduler 消息队列 |
| agent | Process | agent进程引用 |
| last_email_time | float | 上次收到邮件的时间戳 |
| last_agent_response_time | float | 上次agent响应的时间戳 |
| stop_event | Event | 用于优雅停止的事件对象 |
| _agent_target | function | Agent进程的目标函数 |
| _comm | Comm | 通信模组实例 |

##### 方法
1. __init__(self, config, agent_target=None)
   根据config["Scheduler"]配置初始化属性，agent_target为Agent进程入口函数

2. start(self)
   开始运行Scheduler主循环，进入状态机：
   - Idle状态：每隔poll_interval_idle调用Try_Receive()检查邮件
   - 收到邮件后启动Agent，等待Agent发送ready消息，然后发送用户消息
   - 切换到Active状态，每隔poll_interval_active检查新邮件
   - 超过active_timeout无活动则返回Idle状态

3. shutdown(self)
   优雅退出，设置stop_event，停止Agent进程

4. _setup_signal_handlers(self)
   设置SIGTERM/SIGINT信号处理器（仅主线程有效）

5. _start_agent(self) -> bool
   启动Agent进程，等待Agent发送ready消息后返回True

6. _stop_agent(self)
   发送shutdown指令并等待Agent进程退出

7. _send_to_agent(self, message)
   通过to_agent_queue发送用户消息给Agent

8. _check_agent_response(self) -> dict | None
   阻塞等待Agent响应，超时返回None

9. _try_get_agent_response(self) -> dict | None
   非阻塞检查Agent响应

10. _check_timeout(self) -> bool
    检查是否同时满足邮件超时和Agent响应超时

11. _run_idle_state(self)
    Idle状态处理逻辑

12. _run_active_state(self)
    Active状态处理逻辑

#### 消息协议

##### Scheduler → Agent
```python
{"type": "user_message", "content": "用户邮件内容", "timestamp": 1737277512.0}
{"type": "shutdown"}
```

##### Agent → Scheduler
```python
{"type": "ready", "timestamp": 1737277512.0}
{"type": "response", "content": "处理结果", "timestamp": 1737277517.0}
```

#### 状态机流程
```
┌─────────────────────────────────────────────────────┐
│                    start()                           │
│                       │                              │
│               ┌───────▼───────┐                      │
│         ┌────→│  state=Idle   │←─────────────────┐   │
│         │     └───────┬───────┘                  │   │
│         │             │                          │   │
│         │    wait(poll_interval_idle)            │   │
│         │             │                          │   │
│         │     Try_Receive()                      │   │
│         │             │                          │   │
│         │       无邮件 ───────────────────────────┘   │
│         │             │                              │
│         │          有邮件                            │
│         │             │                              │
│         │     ┌───────▼───────┐                      │
│         │     │ _start_agent()│                      │
│         │     │ 等待ready消息  │                      │
│         │     │ 发送user_msg  │                      │
│         │     │ 等待response  │                      │
│         │     └───────┬───────┘                      │
│         │             │                              │
│         │     ┌───────▼───────┐                      │
│         │     │ state=Active  │                      │
│         │     └───────┬───────┘                      │
│         │             │                              │
│         │    wait(poll_interval_active)              │
│         │             │                              │
│         │     Try_Receive() + 检查Agent响应          │
│         │             │                              │
│         │     超时判断(邮件+Agent都超时)              │
│         │             │                              │
│         │            是                              │
│         │             │                              │
│         │     _stop_agent() (如不持久化)             │
│         └─────────────┘                              │
└─────────────────────────────────────────────────────┘
```

#### 配置格式
```json
{
    "Scheduler": {
        "poll_interval_idle": 60,
        "poll_interval_active": 5,
        "active_timeout": 300,
        "agent_persistence": false,
        "agent_timeout": 120
    }
}
```

### Comm 通信模组
Comm通信模组，为整个Columba项目提供与用户通信的手段，当前版本通过Email脚本实现通信功能。

#### 文件
Src/Comm
    - Email.py

#### 类
Class Comm

##### 属性
| 属性 | 类型 | 说明 |
|------|------|------|
| smtp_host | str | SMTP服务器地址 |
| smtp_port | int | SMTP端口号 |
| imap_host | str | IMAP服务器地址 |
| imap_port | int | IMAP端口号 |
| password | str | 邮箱授权码 |
| agent_email | str | Columba Agent的邮箱地址 |
| user_email | list | 允许的用户邮箱列表，只接收这些邮箱的指令 |

##### 方法
1. __init__(self, config)
   读取config["Comm"]配置，初始化所有属性

2. _Validate_User(self, from_addr) -> bool
   内部方法，检查发件人是否在user_email列表中

3. Send(self, text)
   通过SMTP将text发送到所有user_email，标题为"Columba Agent Info"

4. _Send_Imap_Id(self, imap)
   内部方法，发送IMAP ID命令（163邮箱安全要求）

5. Try_Receive(self) -> str | None
   通过IMAP轮询收件箱未读邮件，校验发件人后提取正文，标记已读，返回合并文本或None

6. _Extract_Body(self, msg) -> str
   内部方法，从邮件对象中提取text/plain正文内容

#### 配置格式
```json
{
    "Comm": {
        "agent": {
            "smtp_host": "smtp.163.com",
            "smtp_port": 465,
            "imap_host": "imap.163.com",
            "imap_port": 993,
            "username": "agent@163.com",
            "password": "授权码"
        },
        "user_email": ["user@163.com"]
    }
}
```

### Log 模组
日志模组，为整个Columba项目提供全局的日志组件，它将会记录所有模组的执行信息。

#### 文件
Src/Log
    - Log.py

##### 方法
1. Log_Info(模组, 文本)
   按照 [时间] [信息] [模组] : 文本 的形式将日志存储到.log/日期.log当中
   
