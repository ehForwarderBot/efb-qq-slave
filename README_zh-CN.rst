########################################################################
EFB QQ Slave Channel：EFB QQ 从端 (EQS)
########################################################################

.. figure:: https://i.imgur.com/KHhlL6c.png
   :alt: This project proudly supports #SayNoToQQ campaign.

**Channel ID**: ``milkice.qq``

`English Documentation <README.rst>`_

***********************
软件依赖
***********************

-  Python >= 3.6
-  EH Forwarder Bot >= 2.0.0
-  ffmpeg
-  libmagic
-  pillow


******************
安装与启用
******************

本项目目前仍是 Alpha 版本，仍不稳定，且功能可能随时变更。

现阶段，请按照以下步骤安装此软件包并开始测试。

1. 安装依赖及 EH forwarder bot.

2. pip 安装 efb-qq-slave

   ``pip3 install efb-qq-slave``

3. 在当前配置文件夹 (Profile) ``<profile directory>/config.yaml`` 的 ``config.yaml`` 中启用 ``milkice.qq`` 

   当前配置文件夹的位置会根据用户的设定而改变。

   **(EFB 2.0.0a1 中，默认的配置文件夹位于**
   ``~/.ehforwarderbot/profiles/default`` **)**

4. 为 ``milkice.qq`` EQS从端 创建配置文件 ``config.yaml`` 来指定 QQ 客户端

   各种QQ客户端的详细配置步骤如下。

**目前efb-qq-slave仅支持酷Q 客户端**

客户端们:
------------------------------

酷Q: `酷Q 客户端配置教程 <doc/CoolQ_zh-CN.rst>`_

FAQs
------------------------------

**以下内容通用 针对所有客户端有效**

* Q - 如何在 主端(Telegram) 撤回消息？

  A - 如果 QQ 客户端支持该操作，请编辑该消息并在该消息前段加上 ``rm``` 字样即可在QQ端撤回该消息 同时请注意发出的消息仅能在发出后2分钟内撤回
  
* Q - 如何在 主端(Telegram) 编辑消息？
  
  A - 直接使用 Telegram 的编辑消息功能即可

注意事项
------------------------------

* 目前项目并不稳定，欢迎提交Issue
