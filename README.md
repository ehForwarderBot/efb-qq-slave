EFB QQ Slave Channel
============================================

**Channel ID**: `milkice.qq`

This project is under heavy development and can't be used in production environment.

Installation
------

As this project is in early development, it won't be pushed to PyPI until most functions are implemented and tested.

At this stage, please follow the following steps to install this package and start testing.

1. Install the binary dependencies and EH forwarder bot.

2. Clone this project with git

`git clone https://github.com/milkice233/efb-qq-slave`

3. Install this project via pip locally

`pip3 install -e efb-qq-slave/`

4. Enable `milkice.qq` slave channel in your config.yaml which lies in the current profile directory.

*Usually, this file is located in ~/.ehforwarderbot/profiles/default/config.yaml*

5. Create config.yaml file for `milkice.qq` slave channel

Configuration file is stored at
`<profile directory>/blueset.telegram/config.yaml`.

A sample config file can be as follows:

```
Client: CoolQ  # Defines the client efb-qq-slave should use
CoolQ:
    type: HTTP  # Set communication methods between CoolQ Client and efb-qq-slave
    access_token: db0f790e1fb74eaabf23da77a6f9de47
    api_root: http://127.0.0.1:5700/  # API url for CoolQ http-api plugin
    host: 127.0.0.1  # Local Callback API which handles events from CoolQ http-api plugin
    port: 8000
    is_pro: true  # Defines if the CoolQ instance is Pro version or not
    air_option:  # Only valid when is_pro == false
        upload_to_smms: true  # Upload images from efb.master_channel to sm.ms for CoolQ Air doesn't support sending images directly to QQ chats
```

*Currently efb-qq-slave only supports CoolQ Client*

6. Launch ehforwarderbot by executing `ehforwarderbot` in your terminal.

Notes
------

For end users, it's highly not recommended to test this project as mysterious bugs may occur and it's pretty disgusting for users who have no experience with Python to deal with it.

For developers, contributions & issues are welcomed.
