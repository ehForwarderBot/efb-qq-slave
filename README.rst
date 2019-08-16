########################################################################
EFB QQ Slave Channel
########################################################################

.. image:: https://img.shields.io/badge/Python->%3D%203.6-blue.svg
   :alt: Python >= 3.6
   :target: https://www.python.org/
.. image:: https://img.shields.io/pypi/v/efb-qq-slave.svg
   :alt: PyPI release
   :target: https://pypi.org/project/efb-qq-slave/
.. image:: https://img.shields.io/pypi/dm/efb-qq-slave.svg
   :alt: Downloads per month
   :target: https://pypi.org/project/efb-qq-slave/

.. figure:: https://i.imgur.com/KHhlL6c.png
   :alt: This project proudly supports #SayNoToQQ campaign.


**Channel ID**: ``milkice.qq``

`中文文档 <README_zh-CN.rst>`_

*******************************************
Software dependencies
*******************************************

-  Python >= 3.6
-  EH Forwarder Bot >= 2.0.0
-  ffmpeg
-  libmagic
-  pillow

******************
Installation
******************

This project is still in Alpha, use at your own risk

At this stage, please follow the following steps to install this package and start testing.

1. Install the binary dependencies and EH forwarder bot.

2. Install via pip

   ``pip3 install efb-qq-slave``

3. Enable ``milkice.qq`` slave channel in your ``<profile directory>/config.yaml``.

   *Usually, this file is located in* ``~/.ehforwarderbot/profiles/default/config.yaml``

4. Create ``config.yaml`` file for ``milkice.qq`` slave channel to specify QQ Client.

   The detailed configuration steps for various QQ Clients are as follows.

**Currently efb-qq-slave only supports CoolQ Client**

Clients:
------------------------------

CoolQ: `CoolQ Client Configuration <doc/CoolQ_en-US.rst>`_

FAQs
------------------------------

**The following content is valid for all clients**

* Q - How do I recall a message at the master channel (Telegram)?

  A - If the QQ client supports the operation, please edit the message and add the ``rm``` in the front of the message to recall the message on the QQ. Please also note that the message sent can only be recalled within 2 minutes of being sent.

* Q - How do I edit a message on the master channel (Telegram)?

  A - Directly use Telegram's edit message feature

Notes
------------------------------

* For end users, it's highly not recommended to test this project as mysterious bugs may occur and it's pretty disgusting for users who have no experience with Python to deal with it.
* For developers, contributions & issues are welcomed.
