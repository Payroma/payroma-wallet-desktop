from ..tools import interface, walletcreator
from ..data import wallets, tokens, transactions
from .provider import MainProvider
from typing import Union
import time


def get_all() -> list:
    return list(wallets.db.get_data().values())


def add_new(username: str, password: str, pin_code: str, otp_code: str) -> bool:
    """
    Add a new wallet
    :exception SPDatabase.ITEM_EXISTS_ERROR
    :exception OSError, FileNotFoundError, PermissionError
    :return: bool
    """

    valid = False
    result = walletcreator.access(username, password, pin_code, otp_code)
    if isinstance(result, tuple):
        address, _, pin_code_bytes = result
        wallet_interface = interface.Wallet(
            username=username,
            address=address,
            pin_code=pin_code_bytes,
            date_created=time.ctime(),
            is_favorite=False
        )
        wallets.db.update_item(value=wallet_interface, item_id=wallet_interface.addressID)
        valid = True

    return valid


def remove(wallet_interface: interface.Wallet) -> bool:
    """
    Remove specific wallet interface
    :return: bool
    """

    valid = False
    if isinstance(wallet_interface, interface.Wallet):
        try:
            wallets.db.remove_item(item_id=wallet_interface.addressID)
        except KeyError:
            pass
        else:
            valid = True

    return valid


def backup_wallets(
        path: str, wallets_id: list = None, progress_event: callable = None,
        password: Union[str, wallets.SPDatabase.ControlObject] = wallets.SPDatabase.Control.AUTO
) -> bool:
    """
    Backup all wallets are selected
    :exception SPDatabase.ITEM_NOT_FOUND_ERROR
    :exception OSError, MemoryError, FileNotFoundError, PermissionError
    :return: bool
    """

    wallets.db.dump_backup(
        items_id=wallets_id, destination=path, password=password, progress_event=progress_event
    )
    return True


def import_wallets(
        path: str, wallets_id: list = None, progress_event: callable = None,
        password: Union[str, wallets.SPDatabase.ControlObject] = wallets.SPDatabase.Control.AUTO,
        mode: wallets.SPDatabase.ControlObject = wallets.SPDatabase.Control.UPDATE
) -> bool:
    """
    Import all wallets are selected
    :exception SPDatabase.FILE_SUPPORT_ERROR
    :exception SPCrypto.FILE_SUPPORT_ERROR
    :exception SPCrypto.PERMISSION_ERROR
    :exception: OSError, MemoryError, FileNotFoundError, PermissionError
    :return: bool
    """

    wallets.db.load_backup(
        path=path, items_id=wallets_id, password=password, mode=mode, progress_event=progress_event
    )
    wallets.upgrade_to_v2()
    return True


class WalletEngine(object):
    def __init__(self, wallet_interface: interface.Wallet):
        self.__password = None
        self.__isLogged = False

        self.interface = wallet_interface

    def username(self) -> str:
        return self.interface.username

    def address(self) -> interface.Address:
        return self.interface.address

    def pin_code(self) -> bytes:
        return self.interface.pinCode

    def private_key(self, otp_code: str) -> str:
        value = ''
        if self.__isLogged:
            result = walletcreator.access(
                self.interface.username, self.__password, self.interface.pinCode, otp_code
            )
            if isinstance(result, tuple):
                _, private_key, _ = result
                value = private_key

        return value

    def date_created(self) -> str:
        return self.interface.dateCreated

    def is_favorite(self) -> bool:
        return self.interface.isFavorite

    def is_logged(self) -> bool:
        return self.__isLogged

    def set_favorite(self, status: bool):
        self.interface.isFavorite = status
        wallets.db.dump()

    def login(self, password: str, otp_code: str) -> bool:
        valid = False
        result = walletcreator.access(
            self.interface.username, password, self.interface.pinCode, otp_code
        )
        if isinstance(result, tuple):
            self.__password = password
            self.__isLogged = True
            valid = True

        return valid

    def logout(self):
        self.__password = None
        self.__isLogged = False

    def tokens(self) -> list:
        current_network = MainProvider.interface.networkID
        try:
            return tokens.db.get_item(self.interface.addressID)[current_network]
        except KeyError:
            return []

    def add_token(self, token_interface: interface.Token) -> bool:
        valid = False
        if isinstance(token_interface, interface.Token):
            current_network = MainProvider.interface.networkID
            _tokens = {current_network: self.tokens()}
            _tokens[current_network].append(token_interface)

            try:
                tokens.db.get_item(self.interface.addressID).update(_tokens)
            except KeyError:
                tokens.db.update_item(
                    value=_tokens, item_id=self.interface.addressID, ignore_item_exists=True
                )
            else:
                tokens.db.dump()
            finally:
                valid = True

        return valid

    def remove_token(self, token_interface: interface.Token) -> bool:
        valid = False
        if isinstance(token_interface, interface.Token):
            try:
                _tokens = self.tokens()
                _tokens.remove(token_interface)
            except ValueError:
                pass
            else:
                tokens.db.dump()
                valid = True

        return valid

    def transactions(self) -> list:
        current_network = MainProvider.interface.networkID
        try:
            return transactions.db.get_item(self.interface.addressID)[current_network]
        except KeyError:
            return []

    def add_transaction(self, transaction_interface: interface.Transaction) -> bool:
        valid = False
        if isinstance(transaction_interface, interface.Transaction):
            current_network = MainProvider.interface.networkID
            _transactions = {current_network: self.transactions()}
            _transactions[current_network].append(transaction_interface)

            try:
                transactions.db.get_item(self.interface.addressID).update(_transactions)
            except KeyError:
                transactions.db.update_item(
                    value=_transactions, item_id=self.interface.addressID, ignore_item_exists=True
                )
            else:
                transactions.db.dump()
            finally:
                valid = True

        return valid

    def remove_transaction(self, transaction_interface: interface.Transaction) -> bool:
        valid = False
        if isinstance(transaction_interface, interface.Transaction):
            try:
                _transactions = self.transactions()
                _transactions.remove(transaction_interface)
            except ValueError:
                pass
            else:
                transactions.db.dump()
                valid = True

        return valid


__all__ = ['get_all', 'add_new', 'remove', 'backup_wallets', 'import_wallets', 'WalletEngine']
