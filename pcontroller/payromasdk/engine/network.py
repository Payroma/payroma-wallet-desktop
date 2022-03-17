from ..tools import interface
from ..data import networks


def get_all() -> list:
    return list(networks.db.get_data().values())


def add_new(rpc: str, name: str, chain_id: int, symbol: str, explorer: str) -> bool:
    """
    Add a new network
    :exception SPDatabase.ITEM_EXISTS_ERROR
    :exception OSError, FileNotFoundError, PermissionError
    :return: bool
    """

    network_interface = interface.Network(
        rpc=rpc, name=name, chain_id=chain_id, symbol=symbol, explorer=explorer
    )
    networks.db.update_item(value=network_interface, item_id=network_interface.networkID)

    return True


def remove(network_interface: interface.Network) -> bool:
    """
    Remove specific network interface
    :return: bool
    """

    valid = False
    if isinstance(network_interface, interface.Network):
        try:
            networks.db.remove_item(item_id=network_interface.networkID)
        except KeyError:
            pass
        else:
            valid = True

    return valid


__all__ = ['get_all', 'add_new', 'remove']
