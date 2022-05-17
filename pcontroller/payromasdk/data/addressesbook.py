from . import loader


db = loader.loader(file_name='addressesbook', password='')
__all__ = ['db']
