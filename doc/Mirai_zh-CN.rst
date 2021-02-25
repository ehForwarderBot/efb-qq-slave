客户端：Mirai
====================================

Mirai 有两种配置方式，一种是参照 OneBot 标准的兼容模式。在这种模式下许多功能不可用（因为 OneBot 标准原本是面向酷Q设计的，有一部分特性 Mirai 不支持），另外一种就是专门为 Mirai 适配的 Mirai 模式。以下模式任选其一进行配置。

Mirai 模式(Mirai-http-api):
-------------------------------------

所需依赖及条件

1. JDK 11+

2. Python 3.8+

步骤：

**由于 Mirai 还处于活跃开发中，Mirai 的安装步骤可能随时发生调整，具体请以官方文档为准**

1. 安装 efb-qq-plugin-mirai ``pip3 install git+https://github.com/milkice233/efb-qq-plugin-mirai``

2. 使用 `Mirai Console Loader(MCL) <https://github.com/iTXTech/mirai-console-loader>`_ 安装 Mirai，具体安装步骤请参阅该仓库的 README 文档

3. 安装完 MCL 和 mirai 后请使用 MCL 安装 `mirai-api-http <https://github.com/project-mirai/mirai-api-http>`_，现阶段的安装命令为 ``./mcl --update-package net.mamoe:mirai-api-http --channel stable --type plugin``

4. 编辑 ``config/net.mamoe.mirai-api-http/setting.yml`` 配置文件，其中需要留意的是需要自己设置一个 authKey，可使用随机密码生成器生成一个足够长的字符串，具体参见 `此处 <https://github.com/project-mirai/mirai-api-http#%E5%BC%80%E5%A7%8B%E4%BD%BF%E7%94%A8>`_ ，以下是样例

.. code:: yml

    cors:
      - '*'
    host: 127.0.0.1
    port: 8080
    authKey: xxxxxx        # 这里随机生成一个字符串
    cacheSize: 4096
    enableWebsocket: true  # 确保 Websocket 已经启用
    report:
      enable: true         # 确保这里是 true 用来启用消息上报
      groupMessage:
        report: true
      friendMessage:
        report: true
      tempMessage:
        report: true
      eventMessage:
        report: true
      destinations: []
      extraHeaders: {}

    heartbeat:
      enable: false
      delay: 1000
      period: 15000
      destinations: []
      extraBody: {}
      extraHeaders: {}

5. 配置 EQS 端（EQS 配置文件一般位于 ``~/.ehforwarderbot/profiles/default/milkice.qq/config.yaml``），内容如下：

.. code:: yml

    Client: mirai
    mirai:
      qq: 123456789           # 这里换成登录的 QQ 号
      host: "127.0.0.1"       # Mirai HTTP API 监听地址，一般是 127.0.0.1
      port: 8080              # Mirai HTTP API 监听端口，一般是 8080
      authKey: "28nrq0vnj02y" # 这里填入在配置 Mirai API HTTP 时生成的 authKey

6. 使用 mcl 启动 mirai, Mirai 为交互式登录，请使用 ``login 123456789 yourpassword ANDROID_PAD`` ，或使用启动参数参数 ``--account 123456789 --password yourpassword`` 来登录（如登录后有报错请忽略），请注意 login 命令中密码参数后面可以指定 QQ 所登录的终端，现阶段有 ``ANDROID_PHONE``, ``ANDROID_PAD``, ``ANDROID_WATCH`` 可供选择

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
          host: 127.0.0.1
          port: 5700
          accessToken: ac0f790e1fb74ebcaf45da77a6f9de47
          postUrl: 'http://127.0.0.1:8000'
          postMessageFormat: array
          secret: ''
          # 上报超时时间, 单位毫秒, 须大于0才会生效
          timeout: 0

其中需要修改的为 QQ 号及 accessToken，accessToken 需与 EQS 中的配置一致

需要 **重点** 注意的地方是

.. code:: yml

        http:
          enable: true

上述配置文件中 **enable** 必须为 **true** 否则将无法正常开启EFB

7. 配置 EQS 端
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

8. 再次启动 Mirai并登录（ Mirai 为交互式登录，请使用 ``login 123456789 yourpassword`` ，或使用启动参数参数 ``--account 123456789 --password yourpassword`` 来登录（如登录后有报错请忽略），开启EFB后，重启 Mirai 即可
