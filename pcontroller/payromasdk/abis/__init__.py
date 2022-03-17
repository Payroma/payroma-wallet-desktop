import os
import json


TOKEN_ABI_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'token.json'
)
STAKE_ABI_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'stake.json'
)
PNS_ABI_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'pns.json'
)


with open(TOKEN_ABI_PATH) as file:
    tokenABI = json.load(file)


with open(STAKE_ABI_PATH) as file:
    stakeABI = json.load(file)


with open(PNS_ABI_PATH) as file:
    pnsABI = json.load(file)


__all__ = ['TOKEN_ABI_PATH', 'STAKE_ABI_PATH', 'PNS_ABI_PATH', 'tokenABI', 'stakeABI', 'pnsABI']
