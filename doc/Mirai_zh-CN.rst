客户端：Mirai
====================================

Mirai 有两种配置方式，一种是参照 OneBot 标准的兼容模式。在这种模式下许多功能不可用（因为 OneBot 标准原本是面向酷Q设计的，有一部分特性 Mirai 不支持），另外一种就是专门为 Mirai 适配的 Mirai 模式，目前仅支持兼容模式

兼容模式：
-------------------------------------
**强烈建议先阅读酷Q的配置方案，本模式默认用户已经了解酷Q版的配置方式**

所需依赖及条件

1. JDK 11+

步骤：

1. 使用 `此项目 <https://github.com/project-mirai/mirai-login-solver-selenium/blob/master/README.md>`_ 的方法获得 device.json

2. 下载 `Onebot Kotlin 版 <https://github.com/yyuueexxiinngg/onebot-kotlin/releases>`_  （此版本不需要安装Kotlin）

3. 将 步骤1 中获取的 ``device.json`` 复制到 Onebot Kotlin 的目录

4. 执行 ``java -jar onebot-kotlin-*.jar``

5. 按下 Ctrl-C 停止 Mirai

6. 编辑 ``config/OneBot/setting.yml`` 为如下内容

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
