from ..tools import interface
from web3 import Web3
from typing import Union
import pyotp
import base64
import hashlib
import SPCrypto


def __signature(username: str, password: str, pin_code: str) -> bytes:
    pass


def __encrypt(value: str, password: str) -> bytes:
    pass


def __decrypt(value: bytes, password: str) -> str:
    pass


def otp_hash(username: str, password: str, pin_code: str) -> str:
    pass


def access(
        username: str, password: str, pin_code: Union[str, bytes], otp_code: str
) -> Union[bool, tuple[interface.Address, str, bytes]]:
    pass


__all__ = ['otp_hash', 'access']
