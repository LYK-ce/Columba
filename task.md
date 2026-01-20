1. 帮我在Tool目录下写一个python脚本download_model.py，这个脚本从目标网址中下载模型文件到Model目录下，默认的模型为https://www.modelscope.cn/models/Qwen/Qwen3-8B-GGUF/file/view/master/Qwen3-8B-Q8_0.gguf?status=2 
完成

2. 在Tool目录下写一个doc.md，说明Tool中的每一个脚本的作用和使用方法、
完成

3. 撰写git 配置文件，llama.cpp作为引用子仓库的形式在本仓库中，Model目录不上传，roo/rules不上传
完成

4. 阅读Columba Design Document.md，根据其中Log模组的设计，在Src/Log目录中实现对应的脚本
   完成
5. 阅读Columba Design Document.md，根据其中Comm模组的设计，实现对应scripts
   完成
6. 在Test 目录下写一个test_comm.py脚本，这个脚本初始化一个Comm实例，然后向user email发送一封邮件，内容是hello world，然后尝试接收邮件，并且把内容打印出来
   完成
7. 阅读Columba Design Document.md，根据其中Scheduler模组的设计，实现对应scripts.当然，现在我们还没有实现agent脚本，所以这里的agent脚本就写一个简单的等待5s后通过message queue返回消息即可。然后在Test目录下写一个test_scheduler.py脚本，测试scheduler的功能。
   完成
8. 阅读Columba Design Document.md，根据其中Agent模组的设计，实现对应scripts，暂时不需要实现test脚本
   完成

9. 阅读Columba Design Document.md，根据其中API模组的设计，实现对应scripts，在Test目录下写一个test_agent.py脚本，这个脚本测试Agent的工具调用功能，用户输入为获取当前gpu状况，agent应当调用nvidia-smi来获取信息并且返回。
 完成
10. good，现在我们在Src目录下写一个main.py，新建入口文件，加载config，启动Scheduler，同时修改其他对应文件
    完成
11. 写一个requirements.txt，把我们需要install的库全部写进去
    完成
12. 我修改了config.json,在里面添加了一个tmp workspace，这将作为一个全局的变量，告诉每一个模组我们项目的工作目录是什么。那么迭代当前代码，在scheduler初始化时，你应该创建这个目录，在整个项目退出时，你应该清理掉这个目录。同时，在agent初始化时，它也应该获取此变量作为agent的工作目录。
    完成
13. 我修改了config.json,在里面添加了一个Target_Workspace,我们的Columba项目实际上是运行在服务器中的远程agent，帮助用户通过邮件就能操作服务器当中的一些组件，因此我设计了target workspace这一属性，告诉agent它应该在哪个目录下工作。这和之前的tmp workspace不同，之前的目录是用来存储agent运行过程中产生的临时文件，而target workspace则是agent应该操作此目录下的一些文件等。因此，修改代码，把这个变量传给agent即可，同时API也应该默认在此目录下进行操作。
    完成
14. 修改当前的shell.py，创建一个持久化的shell进程，随着agent进程启用而启动，关闭而退出。在agent类当中增加一个shell的属性指向此shell，shell创建时自动进入到agent 的target space目录下。同时修改当前exec命令，把它改成向shell当中输入命令
    完成
15. 修改当前shell的执行逻辑，将输入命令结果重定向到临时工作目录tmp workspace当中，然后将文件内容返回给Agent，发送邮件给用户时除了发送Agent的回话，还要把文件内容发送给用户。
    完成
16. 根据我们当前的实现，更新Columba Design Document.md，另外，当前Model当中 0.6B模型无法支持两个或两个以上的命令执行，而4B模型则可以支持两个命令的串行执行。把这个发现也写到后面
    完成
17. 浏览当前目录，写一个Readme.md，首先介绍这是一个什么项目，然后说明如何安装并配置环境，最后给出使用案例