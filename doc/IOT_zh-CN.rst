客户端：IOTBot(OPQBot)
====================================

需要运行 OPQBot 客户端以及做好相应的配置

步骤：

1. 请到 `OPQBot 安装指南页 <https://github.com/OPQBOT/OPQ/wiki/%E5%AE%89%E8%A3%85%E6%8C%87%E5%8D%97>`_ 按照文档下载运行 OPQBot，需要申请 Gitter API key，启动完成后访问 `<http://127.0.0.1:8888/v1/Login/GetQRcode>`_ 扫码完成登录

2. 安装 efb-qq-plugin-iot ``pip3 install git+https://github.com/milkice233/efb-qq-plugin-iot``

3. 配置 EQS 端

.. code:: yaml

    Client: iot
    iot:
      qq: 1234567890              # 此处填写登录的QQ号
      host: "http://127.0.0.1"    # 默认IP为本地
      port: 8888                  # 默认端口为 8888

如果有别的特殊设置还请按照文档自行修改

4. 启动 ehforwarderbot
