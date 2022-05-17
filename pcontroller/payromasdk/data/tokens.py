from . import loader


db = loader.loader(file_name='tokens')
__all__ = ['db']
