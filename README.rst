####################################
EFB QQ Slave Channel
####################################

**Channel ID**: `milkice.qq`

This project is under heavy development and can't be used in production environment.

******************
Installation
******************

As this project is in early development, it won't be pushed to PyPI until most functions are implemented and tested.

At this stage, please follow the following steps to install this package and start testing.

1. Install the binary dependencies and EH forwarder bot.

2. Clone this project with git

   ``git clone https://github.com/milkice233/efb-qq-slave``

3. Install this project via pip locally

   ``pip3 install -e efb-qq-slave/``

4. Enable `milkice.qq` slave channel in your `<profile directory>/config.yaml`.

   *Usually, this file is located in `~/.ehforwarderbot/profiles/default/config.yaml`*

5. Create `config.yaml` file for `milkice.qq` slave channel to specify QQ Client.

   The detailed configuration steps for various QQ Clients are as follows.

**Currently efb-qq-slave only supports CoolQ Client**

Client: CoolQ
====================================

For CoolQ binary client
---------------------------

- If you are using Linux/OS X -> Wine is recommended for running CoolQ.

  1. Install docker.

  2. Run the following commands.

  .. code:: shell

    $ docker pull richardchien/cqhttp:latest
    $ mkdir coolq  # Contains CoolQ binary
    $ docker run -ti --rm --name --net="host" cqhttp-test \
             -v $(pwd)/coolq:/home/user/coolq \  # 将宿主目录挂载到容器内用于持久化酷 Q 的程序文件
             -p 9000:9000 \                      # noVNC port
             -p 5700:5700 \                      # HTTP API port
             -e VNC_PASSWD=MAX8char \            # Modify VNC password
             -e COOLQ_PORT=5700 \                # API Port
             -e COOLQ_ACCOUNT=123456 \           # Specify qq uid, optional but recommended
             -e CQHTTP_POST_URL=http://example.com:8000 \  # Event callback url
             -e CQHTTP_SERVE_DATA_FILES=yes \    # Allow accessing CoolQ data file via HTTP
             richardchien/cqhttp:latest

  *Please note that in order to ensure that ehforwarderbot is accessible from docker inside, it's recommended to have the argument --net="host" enabled. If you encounter network issues please try removing this parameter.*

  - For CoolQ Pro User

    **Please add extra argument (-e COOLQ_URL="http://dlsec.cqp.me/cqp-tuling") to docker run command so that docker will download CoolQ Pro instead of Air**

- If you are using Windows -> Directly run CoolQ

    - For CoolQ Lite user:

      * Download from http://dlsec.cqp.me/cqa-tuling, extract zip, and run.

    - For CoolQ Pro user:

      * Download from http://dlsec.cqp.me/cqp-tuling, extract zip, and run.

3. Access http://your_domain.name:9000 in your browser.

   You'll be asked to login into noVNC console and complete the login procedure.

For EH Forwarder Bot
---------------------------

1. Create `config.yaml` file for `milkice.qq` slave channel

   *Configuration file is stored at `<profile directory>/blueset.telegram/config.yaml`.*

   A sample config file can be as follows:

   .. code:: yaml

       Client: CoolQ                         # Defines the client efb-qq-slave should use
       CoolQ:
           type: HTTP                        # Set communication methods between CoolQ Client and efb-qq-slave
           access_token: db0f790e1fb74ebcaf23da77a6f9de47
           api_root: http://127.0.0.1:5700/  # API url for CoolQ http-api plugin
           host: 127.0.0.1                   # Local Callback API which handles events from CoolQ http-api plugin
           port: 8000
           is_pro: true                      # Defines if the CoolQ instance is Pro version or not
           air_option:                       # Only valid when is_pro == false
               upload_to_smms: true          # Upload images from efb.master_channel to sm.ms for CoolQ Air doesn't support sending images directly to QQ chats

- Then launch with command `ehforwarderbot`, you are good to go!

Notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~
* For end users, it's highly not recommended to test this project as mysterious bugs may occur and it's pretty disgusting for users who have no experience with Python to deal with it.
* For developers, contributions & issues are welcomed.