import SPDatabase
import SPSecurity


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
    config = SPDatabase.FileConfig()
    config.database_update(file='addressesbook', extension='db')
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
