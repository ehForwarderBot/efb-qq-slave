客户端：Mirai
====================================

Mirai 有两种配置方式，一种是参照 OneBot 标准的兼容模式。在这种模式下许多功能不可用（因为 OneBot 标准原本是面向酷Q设计的，有一部分特性 Mirai 不支持），另外一种就是专门为 Mirai 适配的 Mirai 模式
目前仅支持兼容模式

兼容模式：
-------------------------------------
**强烈建议先阅读酷Q的配置方案，本模式默认用户已经了解酷Q版的配置方式**

所需依赖及条件

1. JRE 1.8+

步骤：

1. 下载 `cqhttp-mirai Embedded 版 <https://github.com/yyuueexxiinngg/cqhttp-mirai/releases>`_

2. 执行 ``java -jar cqhttp-mirai-*-embedded-all.jar``

3. 按下 Ctrl-C 停止 Mirai

4. 编辑 ``plugin/settings.yml`` 为如下内容

.. code:: yaml

    # Debug日志输出选项
    debug: false
    # 下载图片/语音时使用的Proxy, 配置后, 发送图片/语音时指定`proxy=1`以通过Proxy下载, 如[CQ:image,proxy=1,url=http://***]
    # 支持HTTP及Sock两种Proxy, 设置举例 proxy: "http=http://127.0.0.1:8888", proxy : "sock=127.0.0.1:1088"
    proxy: ""
    # *要进行配置的QQ号 (Mirai支持多帐号登录, 故需要对每个帐号进行单独设置)
    '1234567890':
      # 是否缓存所有收到的图片, 默认为否 (仅包含图片信息, 不包含图片本身,  < 0.5KB)
      cacheImage: false
      # 是否缓存所有收到的语音, 默认为否 (将下载完整语音进行保存)
      cacheRecord: false
      # 心跳包相关配置
      heartbeat:
        # 是否发送心跳包, 默认为否
        enable: false
        # 心跳包发送间隔, 默认为 15000毫秒
        interval: 15000
      # HTTP 相关配置
      http:
        # 可选，是否启用HTTP API服务器, 默认为不启用, 此项开始与否跟postUrl无关
        enable: true
        # 可选，HTTP API服务器监听地址, 默认为0.0.0.0
        host: 127.0.0.1
        # 可选，HTTP API服务器监听端口, 5700
        port: 5700
        # *可选，访问口令
        accessToken: ""
        # 可选，事件及数据上报URL, 默认为空, 即不上报
        postUrl: "http://127.0.0.1:8000"
        # 可选，上报消息格式，string 为字符串格式，array 为数组格式, 默认为string
        postMessageFormat: array
        # 可选，上报数据签名密钥, 默认为空
        secret: ""


其中需要修改的为 QQ 号及 accessToken，accessToken 需与 EQS 中的配置一致

4. 配置 EQS 端
    与酷Q版的配置几乎完全一致，除了要确认下 API Root 的地址

.. code:: yaml

    Client: CoolQ                         # 指定要使用的 QQ 客户端（此处为CoolQ）
       CoolQ:
           type: HTTP                        # 指定 efb-qq-slave 与 酷Q 通信的方式 现阶段仅支持HTTP
           access_token: ac0f790e1fb74ebcaf45da77a6f9de47
           api_root: http://127.0.0.1:5700/  # 酷Q API接口地址/端口
           host: 127.0.0.1                   # efb-qq-slave 所监听的地址用于接收消息
           port: 8000                        # 同上
           is_pro: true                      # 若为酷Q Pro则为true，反之为false
           air_option:                       # 包含于 air_option 的配置选项仅当 is_pro 为 false 时才有效
               upload_to_smms: true          # 将来自 EFB主端(通常是Telegram) 的图片上传到 sm.ms 服务器并以链接的形式发送到 QQ 端


需要注意的是其实 port 下面的配置都是无效的，只是为了兼容酷Q，is_pro 请保持为 true

5. 再次启动 Mirai, 而后启动 EQS 即可
