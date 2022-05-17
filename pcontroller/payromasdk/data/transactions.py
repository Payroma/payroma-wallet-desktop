from . import loader


db = loader.loader(file_name='transactions')
__all__ = ['db']
