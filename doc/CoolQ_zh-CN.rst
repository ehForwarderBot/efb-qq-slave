客户端：酷Q
====================================

由于 efb-qq-slave 的特性是由酷Q客户端提供的，两者互相隔离，因此必须正确配置两端确保两端能够正常通信。

下面的教程展示了当 酷Q 和 ehForwarderBot 在同一台机器上运行时如何设置两端。

（高级） 对于其他的情况，例如 酷Q 和 ehForwarderBot 在不同的机器上运行时， ``CoolQ Post Url`` 和 ``CoolQ API Url`` 必须修改为相应的值（前者是 efb-qq-slave 监听的地址/端口，后者是酷Q监听的地址/端口），同时防火墙应允许双方的数据包通过，以便双方的请求不会被防火墙拦截。如果双方通信内容必须经过 Internet 传输，请确保已配置 ``Access Token`` 并启用 ``HTTPS`` 确保双方通信内容不会在公网被窃听/篡改。

有关详细信息，请访问 `配置文件文档 <https://cqhttp.cc/docs/4.4/#/Configuration>`_ 和 `HTTPS 文档 <https://github.com/richardchien/coolq-http-api/wiki/ HTTPS>`_。

配置 酷Q 端
---------------------------

- 如果您正在运行 Linux/OS X -> 推荐使用Docker(包含Wine)来运行酷Q

  1. 安装 Docker

  2. 运行下列命令

  .. code:: shell

    $ docker pull richardchien/cqhttp:latest
    $ mkdir coolq  # 包含CoolQ程序文件
    $ docker run -ti --rm --name cqhttp-test --net="host" \
             -v $(pwd)/coolq:/home/user/coolq \  
             -p 9000:9000 \                      # 网页noVNC端口
             -p 5700:5700 \                      # 酷Q对外提供的API接口的端口
             -e VNC_PASSWD=MAX8char \            # 请修改 VNC 密码！！！！
             -e COOLQ_PORT=5700 \                # 酷Q对外提供的API接口的端口
             -e COOLQ_ACCOUNT=123456 \           # 在此输入要登录的QQ号，虽然可选但是建议填入
             -e CQHTTP_POST_URL=http://example.com:8000 \  # efb-qq-slave监听的端口/地址 用于接受传入的消息
             -e CQHTTP_SERVE_DATA_FILES=yes \    # 允许以HTTP方式访问酷Q数据文件
             -e CQHTTP_ACCESS_TOKEN=ac0f790e1fb74ebcaf45da77a6f9de47 \ # Access Token
             -e CQHTTP_POST_MESSAGE_FORMAT=array \ # 回传消息时使用数组（必选）
             richardchien/cqhttp:latest

  - 酷Q Pro用户请注意

    **请在docker run命令中添加额外参数 (-e COOLQ_URL = "http://dlsec.cqp.me/cqp-tuling")，以便docker下载CoolQ Pro而不是Air**

  请注意，为了确保可以从 docker 内访问 ehforwarderbot，建议添加参数 ``--net ="host"`` 如果您遇到网络问题，请尝试删除此参数。

  *请阅读* `docker 文档 <https://cqhttp.cc/docs/4.4/#/Docker>`_ *获悉更多的可配置选项.*

  3. 在浏览器内访问 http://<酷Q VNC监听的ip或者域名>:9000

     请在noVNC终端中输入上述配置选项中的 VNC 密码登录，并使用QQ账户和密码在酷Q中登录QQ账号

- 如果您正在运行 Windows -> 请直接运行 CoolQ

  1. 从CoolQ网站下载CoolQ程序文件

     * 如果您是 CoolQ Lite:
    
       * 从 http://dlsec.cqp.me/cqa-tuling 下载，并解压zip

     * 如果您是 CoolQ Pro：

       * 从 http://dlsec.cqp.me/cqp-tuling 下载，并解压zip
   
  2. 从 `Github Releases <https://github.com/richardchien/coolq-http-api/releases>`_ 下载 酷Q HTTP 插件并将其丢入 ``app/`` 文件夹内

  3. 在 ``app\io.github.richardchien.coolqhttpapi\config`` 文件夹内为 酷Q HTTP 插件 创建配置文件

     文件名应是 ``<QQ号>.json`` or ``<QQ号>.ini``, 文件格式取决于您
     
     以 .ini 为例, 配置文件样例如下:
   
     .. code:: yaml

       [80000000]                                       # 填入你的QQ号
       serve_data_files = yes                           # 必选
       post_message_format = array                      # 必选
       post_url = http://127.0.0.1:8000                 # 设置上报地址（efb-qq-slave监听的地址/端口）
       access_token = ac0f790e1fb74ebcaf45da77a6f9de47  # Access Token

     有关详细信息，请参阅 `配置文档 <https://cqhttp.cc/docs/4.3/#/Configuration>`_

  4. 双击启动 酷Q, 输入您的QQ号&密码完成登录

配置 ehForwarderBot 端
---------------------------

1. 为 ``milkice.qq`` 从端创建 ``config.yaml`` 配置文件
  
   *配置文件通常位于* ``~/.ehforwarderbot/profiles/default/blueset.telegram/config.yaml``.

   样例配置文件如下:

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

2. 控制台启动 ``ehforwarderbot``, 大功告成!

FAQ
---------------------------

**以下内容仅针对于 酷Q 客户端有效**

* Q - 为什么我无法在 Telegram 中发送图片到QQ?

  A - 如果您正在使用 CoolQ Air，由于技术限制无法直接发送图片到QQ，请将配置文件中的 ``is_pro`` 改为 false 并将 ``air_option`` 中的 ``upload_to_smms`` 改为true即可变相发送图片（通过链接形式）

* Q - 为什么我无法接收/发送QQ语音？

  A - 酷Q官方以语音处理库太大为由并未将语音模块集成入酷Q，而是提供了一个带语音处理版本的酷Q供下载，目前暂时没有动力编写QQ语音消息的处理，如有需求请在 `这个Github Issue <https://github.com/milkice233/efb-qq-slave/issues/1>`_ 中留言或在issue上发送表情，需求量较高将会考虑开发

* Q - 酷Q不同版本区别？

  A - `https://cqp.cc/t/23290 <https://cqp.cc/t/23290>`_ 同时请注意酷Q Air 不支持消息撤回

* Q - 目前暂未实现的功能？

  A - 好友请求处理，加群请求处理，尚未适配少部分消息类型（例如签到消息），语音发送/接收
