from ..tools import interface
from . import loader
import time


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


db = loader.loader(file_name='wallets', backup=True)
__all__ = ['db']
