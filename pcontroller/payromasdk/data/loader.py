import SPDatabase
import SPSecurity


def loader(file_name: str, password: str = None, backup: bool = False) -> SPDatabase.DataManager:
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
    config.database_update(file=file_name, extension='db')
    if backup:
        config.backup_update(file='payroma', extension='backup')

    config.setup()

    if not password:
        password = SPSecurity.secure_string(
            # Set the application password here, it must be changed in a real environment
            (116, 101, 115, 116)
        ).decode()

    # Default configuration and load
    database = SPDatabase.DataManager(config, password)
    database.load()

    return database
