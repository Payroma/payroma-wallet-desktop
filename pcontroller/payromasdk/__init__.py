from . import abis
from . import data
from . import tools
from . import engine
from .engine.provider import MainProvider, PNSProvider
from web3 import Web3
from eth_utils import units
from typing import Union
import os
import re
import json
import time
import pyotp
import base64
import decimal
import hashlib
import requests
import webbrowser
import SPCrypto
import SPDatabase
import SPSecurity


units.units.update({
    '1': decimal.Decimal('10'),
    '2': decimal.Decimal('100'),
    '3': decimal.Decimal('1000'),
    '4': decimal.Decimal('10000'),
    '5': decimal.Decimal('100000'),
    '6': decimal.Decimal('1000000'),
    '7': decimal.Decimal('10000000'),
    '8': decimal.Decimal('100000000'),
    '9': decimal.Decimal('1000000000'),
    '10': decimal.Decimal('10000000000'),
    '11': decimal.Decimal('100000000000'),
    '12': decimal.Decimal('1000000000000'),
    '13': decimal.Decimal('10000000000000'),
    '14': decimal.Decimal('100000000000000'),
    '15': decimal.Decimal('1000000000000000'),
    '16': decimal.Decimal('10000000000000000'),
    '17': decimal.Decimal('100000000000000000'),
    '18': decimal.Decimal('1000000000000000000'),
    '19': decimal.Decimal('10000000000000000000'),
    '20': decimal.Decimal('100000000000000000000'),
    '21': decimal.Decimal('1000000000000000000000'),
    '22': decimal.Decimal('10000000000000000000000'),
    '23': decimal.Decimal('100000000000000000000000'),
    '24': decimal.Decimal('1000000000000000000000000'),
    '25': decimal.Decimal('10000000000000000000000000'),
    '26': decimal.Decimal('100000000000000000000000000'),
    '27': decimal.Decimal('1000000000000000000000000000'),
    '28': decimal.Decimal('10000000000000000000000000000'),
    '29': decimal.Decimal('100000000000000000000000000000')
})
