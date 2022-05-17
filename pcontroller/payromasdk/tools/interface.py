from web3 import Web3
from typing import Union
import re
import hashlib
import webbrowser


def _convert_to_id(value: str) -> int:
    sha256 = hashlib.sha256(value.encode()).hexdigest()
    return int(sha256, 16) % (10 ** 8)


class Network(object):
    def __init__(
            self, rpc: str, name: str, chain_id: int, symbol: str, explorer: str
    ):
        self.id = _convert_to_id(rpc)
        self.rpc = rpc
        self.name = name
        self.chainID = chain_id
        self.symbol = symbol
        self.explorer = explorer


class Address(object):
    networkInterface: Network = None

    def __init__(
            self, value: str
    ):
        if not re.compile('^0x([A-Fa-f0-9]{40})$').match(value):
            raise ValueError("wrong address")

        self.__value = Web3.toChecksumAddress(value)
        self.__int = _convert_to_id(self.__value)

    def value(self) -> str:
        return self.__value

    def to_integer(self) -> int:
        return self.__int

    def explorer_view(self, browse: bool = True) -> str:
        url = '{}/address/{}'.format(Address.networkInterface.explorer, self.__value)
        if browse:
            webbrowser.open_new(url)

        return url


class TXHash(object):
    networkInterface: Network = None

    def __init__(
            self, value: str
    ):
        value = value.lower()
        if not re.compile('^0x([a-f0-9]{64})$').match(value):
            raise ValueError("wrong tx hash")

        self.__value = value
        self.__int = _convert_to_id(self.__value)

    def value(self) -> str:
        return self.__value

    def to_integer(self) -> int:
        return self.__int

    def explorer_view(self, browse: bool = True) -> str:
        url = '{}/tx/{}'.format(TXHash.networkInterface.explorer, self.__value)
        if browse:
            webbrowser.open_new(url)

        return url


class WeiAmount(object):
    def __init__(
            self, value: int, decimals: int
    ):
        self.__value = value
        self.__ether = float(Web3.fromWei(self.__value, str(decimals)))
        self.__int, self.__decimals = self.__display_float(self.__ether).split('.')

    def value(self) -> int:
        return self.__value

    def to_string(self) -> str:
        return str(self.__value)

    def to_ether(self) -> float:
        return self.__ether

    def to_ether_string(self, currency_format: bool = True, length: int = 8) -> str:
        if self.__ether > 999 and currency_format:
            return '{:,}.{}'.format(int(self.__int), self.__decimals[:length])
        elif self.__ether > 0 or not currency_format:
            return '{}.{}'.format(self.__int, self.__decimals[:length])

        # in case integer = 0
        return self.__int

    @staticmethod
    def __display_float(value: float) -> str:
        # format numbers > 1.
        if str(value).find('+') > -1:
            return '{:.1f}'.format(value)

        # format numbers > 1e-05
        e_idx = str(value).find('e')
        if e_idx == -1:
            return str(value)

        # format numbers < 1e-05
        shift = e_idx
        if str(value).find('.') > -1:
            shift -= 1

        decimal_points = -int(str(value)[str(value).find('-'):]) - 1 + shift
        float_format = '{:.' + str(decimal_points) + 'f}'

        return float_format.format(value)


class EtherAmount(object):
    def __init__(
            self, value: Union[str, int, float], decimals: int
    ):
        self.__value = value

        if isinstance(value, str):
            value = value.replace(',', '')
        self.__wei = int(Web3.toWei(value, str(decimals)))

    def value(self) -> Union[str, int, float]:
        return self.__value

    def to_wei(self) -> int:
        return self.__wei


class Wallet(object):
    def __init__(
            self, username: str, address: Address, pin_code: bytes, date_created: str, is_favorite: bool
    ):
        self.id = address.to_integer()
        self.username = username
        self.address = address
        self.pinCode = pin_code
        self.dateCreated = date_created
        self.isFavorite = is_favorite


class Token(object):
    def __init__(
            self, contract: Address, symbol: str, decimals: int
    ):
        self.id = contract.to_integer()
        self.contract = contract
        self.symbol = symbol
        self.decimals = decimals


class Transaction(object):
    class Status:
        FAILED = 0
        SUCCESS = 1
        PENDING = 2

    def __init__(
            self, tx_hash: TXHash, function: str,
            from_address: Address, to_address: Address, amount: WeiAmount,
            symbol: str, date_created: str, status: int
    ):
        self.id = tx_hash.to_integer()
        self.txHash = tx_hash
        self.function = function
        self.fromAddress = from_address
        self.toAddress = to_address
        self.amount = amount
        self.symbol = symbol
        self.dateCreated = date_created
        self.status = status

    def status_text(self) -> str:
        values = {
            Transaction.Status.FAILED: 'failed',
            Transaction.Status.SUCCESS: 'success',
            Transaction.Status.PENDING: 'pending'
        }

        return values[self.status]


class AddressBook(object):
    def __init__(
            self, username: str, address: Address
    ):
        self.id = address.to_integer()
        self.username = username
        self.address = address


class Stake(object):
    def __init__(
            self, contract: Address, stake_token: Token, reward_token: Token,
            expiry_date: int, is_favorite: bool
    ):
        self.id = contract.to_integer()
        self.contract = contract
        self.stakeToken = stake_token
        self.rewardToken = reward_token
        self.expiryDate = expiry_date
        self.isFavorite = is_favorite


__all__ = [
    'Network', 'Address', 'TXHash', 'WeiAmount', 'EtherAmount',
    'Wallet', 'Token', 'Transaction', 'AddressBook', 'Stake'
]
