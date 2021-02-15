from typing import TypedDict, Optional, Dict


class EFBGroupChat(Dict):
    channel: str
    uid: str
    name: str


class EFBPrivateChat(EFBGroupChat):
    alias: str


class EFBGroupMember(Dict):
    name: str
    uid: str
