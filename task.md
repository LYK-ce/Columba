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