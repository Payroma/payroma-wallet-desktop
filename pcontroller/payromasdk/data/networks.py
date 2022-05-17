from . import loader


db = loader.loader(file_name='networks')
__all__ = ['db']
