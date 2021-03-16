客户端：IOTBot(OPQBot)
====================================

需要运行 OPQBot 客户端以及做好相应的配置

步骤：

1. 请到 `OPQBot 安装指南页 <https://github.com/OPQBOT/OPQ/wiki/%E5%AE%89%E8%A3%85%E6%8C%87%E5%8D%97>`_ 按照文档下载运行 OPQBot，需要申请 Gitter API key，启动完成后访问 `<http://127.0.0.1:8888/v1/Login/GetQRcode>`_ 扫码完成登录

2. 由于解码 QQ 所使用的 Silk 编码语音格式需要外部 C 库的支持，因此在安装阶段会编译解码器和编码器，请确保系统已经安装编译器和 Python Dev 头文件

    对于 Debian/Ubuntu 系列发行版请执行

    ``sudo apt install python3-dev build-essential``

    对于 Redhat/CentOS 系列发行版请执行（注意，未经过测试）

    ``sudo yum install python3-devel gcc gcc-c++ make``

3. 安装 efb-qq-plugin-iot ``pip3 install git+https://github.com/milkice233/efb-qq-plugin-iot``

    因为涉及到编译第三方库，在安装过程中可能会失败，请结合日志分析原因处理，如果遇到难以处理的问题可以发 issue 询问

4. 配置 EQS 端

.. code:: yaml

    Client: iot
    iot:
      qq: 1234567890              # 此处填写登录的QQ号
      host: "http://127.0.0.1"    # 默认IP为本地
      port: 8888                  # 默认端口为 8888
      receive_self_msg: False     # 不接收自己发出的消息
      
如果有别的特殊设置还请按照文档自行修改

4. 启动 ehforwarderbot
