客户端：Mirai
====================================

Mirai 有两种配置方式，一种是参照 OneBot 标准的兼容模式。在这种模式下许多功能不可用（因为 OneBot 标准原本是面向酷Q设计的，有一部分特性 Mirai 不支持），另外一种就是专门为 Mirai 适配的 Mirai 模式。以下模式任选其一进行配置。

Mirai 模式(mirai-api-http):
-------------------------------------

所需依赖及条件

1. JDK 11+

2. Python 3.8+

步骤：

**注意：以下为 mirai-api-http 2.x 版本的安装步骤，由于 Mirai 还处于活跃开发中，Mirai 的安装步骤可能随时发生调整，具体请以官方文档为准**

1. 安装 efb-qq-plugin-mirai ``pip3 install git+https://github.com/milkice233/efb-qq-plugin-mirai``

2. 使用 `Mirai Console Loader(MCL) <https://github.com/iTXTech/mirai-console-loader>`_ 安装 Mirai，具体安装步骤请参阅该仓库的 README 文档

3. 安装完 MCL 和 mirai 后请使用 MCL 安装 `mirai-api-http <https://github.com/project-mirai/mirai-api-http>`_，efb-qq-plugin-mirai 从 v2.0.7 开始支持 mirai-api-http 2.x 版本，2.x版本的安装命令为 ``./mcl --update-package net.mamoe:mirai-api-http --channel stable-v2 --type plugin``

4. 编辑 ``config/net.mamoe.mirai-api-http/setting.yml`` 配置文件，其中需要留意的是需要自己设置一个 verifyKey，可使用随机密码生成器生成一个足够长的字符串，具体参见 `此处 <https://github.com/project-mirai/mirai-api-http#%E5%BC%80%E5%A7%8B%E4%BD%BF%E7%94%A8>`_ ，以下是样例（这里假设 mirai-api-http 监听在 127.0.0.1:8080）

.. code:: yml

    ## 启用的 adapter, 请确保 http 和 ws 列在下方
    adapters:
      - http
      - ws

    ## 是否开启认证流程, 若为 true 则建立连接时需要验证 verifyKey
    ## 强烈建议开启
    enableVerify: true
    verifyKey: <这里设置一个随机的足够长的字符串>

    ## 开启一些调式信息
    debug: false

    ## 是否开启单 session 模式, 若为 true，则自动创建 session 绑定 console 中登录的 bot
    ## 开启后，接口中任何 sessionKey 不需要传递参数
    ## 若 console 中有多个 bot 登录，则行为未定义
    ## 确保 console 中只有一个 bot 登陆时启用
    ## 这里可以留为 false
    singleMode: false

    ## 历史消息的缓存大小
    ## 同时，也是 http adapter 的消息队列容量
    cacheSize: 4096

    ## adapter 的单独配置，键名与 adapters 项配置相同
    adapterSettings:
      ## 详情看 http adapter 使用说明 配置
      http:
        host: localhost
        port: 8080
        cors: [*]

      ## 详情看 websocket adapter 使用说明 配置
      ws:
        host: localhost
        port: 8080
        reservedSyncId: -1

5. 配置 EQS 端（EQS 配置文件一般位于 ``~/.ehforwarderbot/profiles/default/milkice.qq/config.yaml``），内容如下：

.. code:: yml

    Client: mirai
    mirai:
      qq: 123456789           # 这里换成登录的 QQ 号
      host: "127.0.0.1"       # Mirai HTTP API 监听地址，一般是 127.0.0.1
      port: 8080              # Mirai HTTP API 监听端口，一般是 8080
      verifyKey: "28nrq0vnj02y" # 这里填入在配置 Mirai API HTTP 时生成的 verifyKey

6. 使用 mcl 启动 mirai, Mirai 为交互式登录，请使用 ``login 123456789 yourpassword ANDROID_PAD`` （如登录后有报错请忽略），请注意 login 命令中密码参数后面可以指定 QQ 所登录的终端，现阶段有 ``ANDROID_PHONE``, ``ANDROID_PAD``, ``ANDROID_WATCH`` 可供选择

7. 使用 ``ehforwarderbot`` 命令启动 EFB


兼容模式：
-------------------------------------
**强烈建议先阅读酷Q的配置方案，本模式默认用户已经了解酷Q版的配置方式**

所需依赖及条件

1. JDK 11+

步骤：

1. 安装 efb-qq-plugin-coolq ``pip3 install git+https://github.com/milkice233/efb-qq-plugin-coolq``

2. 使用 `此项目 <https://github.com/project-mirai/mirai-login-solver-selenium/blob/master/README.md>`_ 的方法获得 device.json

3. 下载 `Onebot Kotlin 版 <https://github.com/yyuueexxiinngg/onebot-kotlin/releases>`_  （此版本不需要安装Kotlin）

4. 将 步骤1 中获取的 ``device.json`` 复制到 Onebot Kotlin 的目录

5. 执行 ``java -jar onebot-kotlin-*.jar``

6. 按下 Ctrl-C 停止 Mirai

7. 编辑 ``config/OneBot/settings.yml`` 为如下内容

.. code:: yml

    proxy: ''
    bots:
      123456789:
        cacheImage: false
        cacheRecord: false
        heartbeat:
          enable: false
          interval: 1500
        http:
          enable: true
          # 请注意是否为true
          host: 127.0.0.1
          port: 5700
          accessToken: ac0f790e1fb74ebcaf45da77a6f9de47
          postUrl: 'http://127.0.0.1:8000'
          postMessageFormat: array
          secret: ''
          # 上报超时时间, 单位毫秒, 须大于0才会生效
          timeout: 0

其中需要修改的为 QQ 号及 accessToken，accessToken 需与 EQS 中的配置一致

8. 配置 EQS 端
    与酷Q版的配置几乎完全一致，除了要确认下 API Root 地址 和 efb-qq-slave 所监听的地址

.. code:: yaml

    Client: CoolQ                         # 指定要使用的 QQ 客户端（此处为CoolQ模式）
    CoolQ:
       type: HTTP                        # 指定 efb-qq-slave 与 酷Q 通信的方式 现阶段仅支持HTTP
       access_token: ac0f790e1fb74ebcaf45da77a6f9de47
       api_root: http://127.0.0.1:5700/  # OneBot-Kotlin 的API接口地址/端口
       host: 127.0.0.1                   # efb-qq-slave 所监听的地址用于接收消息
       port: 8000                        # 同上
       is_pro: true                      # 保持为默认
       air_option:                       # 包含于 air_option 的配置选项仅当 is_pro 为 false 时才有效
           upload_to_smms: true          # 将来自 EFB主端(通常是Telegram) 的图片上传到 sm.ms 服务器并以链接的形式发送到 QQ 端

需要注意的是其实 port 下面的配置都是无效的，只是为了兼容酷Q，is_pro 请保持为 true

9. 再次启动 Mirai并登录（ Mirai 为交互式登录，请使用 ``login 123456789 yourpassword`` ，或使用启动参数参数 ``--account 123456789 --password yourpassword`` 来登录（如登录后有报错请忽略），开启EFB后，重启 Mirai 即可
