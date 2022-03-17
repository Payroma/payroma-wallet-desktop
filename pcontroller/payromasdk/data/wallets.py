from ..tools import interface
import time
import SPDatabase
import SPSecurity


def upgrade_to_v2():
    username_element = 1
    pin_element = 2
    address_element = 3
    is_favorite_element = 4
    changes_available = False
    data = db.get_data()

    for wallet_id in data.copy():
        if isinstance(data[wallet_id], interface.Wallet):
            # Ignore the upgraded wallets
            continue

        address = interface.Address(data[wallet_id][address_element])
        data[address.to_integer()] = interface.Wallet(
            username=data[wallet_id][username_element],
            address=address,
            pin_code=data[wallet_id][pin_element],
            date_created=time.ctime(),
            is_favorite=data[wallet_id][is_favorite_element]
        )
        del data[wallet_id]
        changes_available = True

    if changes_available:
        db.dump()


def __loader() -> SPDatabase.DataManager:
    """
    :exception FILE_SUPPORT_ERROR
    :exception SPCrypto.FILE_SUPPORT_ERROR
    :exception SPCrypto.PERMISSION_ERROR
    :exception pickle.UnpicklingError
    :exception MemoryError, PermissionError
    :return: SPDatabase.DataManager
    """

    # Memory setup
    config = SPDatabase.FileConfig(backup=True)
    config.database_update(file='wallets', extension='db')
    config.backup_update(file='payroma', extension='backup')
    config.setup()

    # Default configuration and load
    database = SPDatabase.DataManager(
        config, SPSecurity.secure_string(
            # Set the application password here
            (116, 101, 115, 116)
        ).decode()
    )
    database.load()

    return database


db = __loader()
__all__ = ['db']
