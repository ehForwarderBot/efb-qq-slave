Client: CoolQ
====================================

As the features are provided by CoolQ Binary which is isolated from efb-qq-slave, two sides must be configured to be able to communicate with each other properly.

The tutorial below shows how to set up two sides when CoolQ and ehForwarderBot is running on the same machine. 

For other situations, for example CoolQ and ehForwarderBot is running on different machine, ``CoolQ Post Url`` and ``CoolQ API Url`` have to be set to specific value and firewall should be properly configured so that the requests from both sides won't be blocked by the firewall. If the requests sent have to be transmitted via Internet, make sure you have configured ``Access Token`` and enabled ``HTTPS`` for extra security.

For more details please visit `config documentation <https://cqhttp.cc/docs/4.4/#/Configuration>`_ and `HTTPS documentation <https://github.com/richardchien/coolq-http-api/wiki/HTTPS>`_.

For CoolQ binary client
---------------------------

- If you are using Linux/OS X -> Docker(Wine Inside) is recommended for running CoolQ.

  1. Install docker.

  2. Run the following commands.

  .. code:: shell

    $ docker pull richardchien/cqhttp:latest
    $ mkdir coolq  # Contains CoolQ binary
    $ docker run -ti --rm --name cqhttp-test --net="host" \
             -v $(pwd)/coolq:/home/user/coolq \  # mount coolq folder
             -p 9000:9000 \                      # noVNC port
             -p 5700:5700 \                      # HTTP API port
             -e VNC_PASSWD=MAX8char \            # Modify VNC password
             -e COOLQ_PORT=5700 \                # API Port
             -e COOLQ_ACCOUNT=123456 \           # Specify qq uid, optional but recommended
             -e CQHTTP_POST_URL=http://example.com:8000 \  # Event callback url
             -e CQHTTP_SERVE_DATA_FILES=yes \    # Allow accessing CoolQ data file via HTTP
             -e CQHTTP_ACCESS_TOKEN=ac0f790e1fb74ebcaf45da77a6f9de47 \ # Access Token
             -e CQHTTP_POST_MESSAGE_FORMAT=array \ # Use array for posting(Required)
             richardchien/cqhttp:latest

  Please note that in order to ensure that ehforwarderbot is accessible from docker inside, it's recommended to have the argument ``--net="host"`` enabled. If you encounter network issues please try removing this parameter.

  - For CoolQ Pro User

    **Please add extra argument (``-e COOLQ_URL="http://dlsec.cqp.me/cqp-tuling"``) to docker run command so that docker will download CoolQ Pro instead of Air**


  *Please read the* `docker documentation <https://cqhttp.cc/docs/4.4/#/Docker>`_ *for more options.*

  
  3. Access http://<your_domain_name_or_your_ip>:9000 in your browser.

     You'll be asked to login into noVNC console and complete the login procedure.

- If you are using Windows -> Directly run CoolQ
  
  1. Download CoolQ Binary from CoolQ website

  * For CoolQ Lite user:
    
    * Download from http://dlsec.cqp.me/cqa-tuling, extract zip.

  * For CoolQ Pro user:

    * Download from http://dlsec.cqp.me/cqp-tuling, extract zip.
   
  2. Download CoolQ HTTP API Plugin from `Github Releases <https://github.com/richardchien/coolq-http-api/releases>`_ and then drop it in ``app/`` folder

  3. Create configuration file for CoolQ HTTP API in ``app\io.github.richardchien.coolqhttpapi\config``

     Filename should be <user_id>.json or <user_id>.ini, depending on your choice.
     
     Take .ini for example, the configuration sample can be as follows:
   
     .. code:: yaml

       [80000000]                                       # Specify your qq uid
       serve_data_files = yes                           # Required
       post_message_format = array                      # Required
       post_url = http://127.0.0.1:8000                 # Set callback url
       access_token = ac0f790e1fb74ebcaf45da77a6f9de47  # Access Token

     For detailed information please refer to the `configuration documentation <https://cqhttp.cc/docs/4.3/#/Configuration>`_.

  4. Launch CoolQ, enter your account & password and complete the login procedure.

For EH Forwarder Bot
---------------------------

1. Create ``config.yaml`` file for ``milkice.qq`` slave channel

   *Configuration file is stored at* ``<profile directory>/milkice.qq/config.yaml``.

   A sample config file can be as follows:

   .. code:: yaml

       Client: CoolQ                         # Defines the client efb-qq-slave should use
       CoolQ:
           type: HTTP                        # Set communication methods between CoolQ Client and efb-qq-slave
           access_token: ac0f790e1fb74ebcaf45da77a6f9de47
           api_root: http://127.0.0.1:5700/  # API url for CoolQ http-api plugin
           host: 127.0.0.1                   # Local Callback API which handles events from CoolQ http-api plugin
           port: 8000
           is_pro: true                      # Defines if the CoolQ instance is Pro version or not
           air_option:                       # Only valid when is_pro == false
               upload_to_smms: true          # Upload images from efb.master_channel to sm.ms for CoolQ Air doesn't support sending images directly to QQ chats

2. Then launch with command ``ehforwarderbot``, you are good to go!

FAQ:
---------------------------

**Following content is only valid for CoolQ**

* Q - Why can't I send images to QQ from master channel(Telegram)?

  A - If you are using CoolQ Air, due to technical barriers CoolQ is unable to send images directly to QQ. Please change the ``is_pro`` to false and ``upload_to_smms`` to true in order to send images via links.

* Q - Why can't I send/receive audio？

  A - Currently we have no intention to develop that, please leave feedback on `this Github Issue <https://github.com/milkice233/efb-qq-slave/issues/1>`_ if you are eager for this feature

* Q - What's the differences between CoolQ Air and Pro?

  A - `https://cqp.cc/t/23290 <https://cqp.cc/t/23290>`_

* Q - What are the features that haven't been implemented？

  A - Friend Request, Group Request, Some kinds of messages(like siganture messages), receiving/sending audio
