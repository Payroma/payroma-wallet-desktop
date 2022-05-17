from . import loader


db = loader.loader(file_name='stakecontracts')
__all__ = ['db']
