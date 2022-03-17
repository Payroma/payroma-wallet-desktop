from ..tools import interface
from ..data import addressesbook


def get_all() -> list:
    return list(addressesbook.db.get_data().values())


def add_new(username: str, address: interface.Address) -> bool:
    """
    Add a new address book
    :exception SPDatabase.ITEM_EXISTS_ERROR
    :exception OSError, FileNotFoundError, PermissionError
    :return: bool
    """

    address_book_interface = interface.AddressBook(
        username=username, address=address
    )
    addressesbook.db.update_item(value=address_book_interface, item_id=address_book_interface.addressID)

    return True


def remove(address_book_interface: interface.AddressBook) -> bool:
    """
    Remove specific address book interface
    :return: bool
    """

    valid = False
    if isinstance(address_book_interface, interface.AddressBook):
        try:
            addressesbook.db.remove_item(item_id=address_book_interface.addressID)
        except KeyError:
            pass
        else:
            valid = True

    return valid


__all__ = ['get_all', 'add_new', 'remove']
