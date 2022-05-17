from .provider import MainProvider, Metadata
from ..abis import tokenABI, stakeABI
from ..tools import interface
from ..data import stakecontracts
import time
import pickle
import requests


def __fetching(url: str) -> dict:
    try:
        return pickle.loads(
            eval(requests.get(url).text)
        )
    except requests.exceptions.ConnectionError:
        return {}


def __favorite_sort(contracts: list) -> list:
    items = contracts.copy()
    favorites = [i for i in items if i.isFavorite]
    for i in favorites:
        items.remove(i)

    return favorites + items


def get_all(filter_by_network: bool = False) -> list:
    result = []

    if filter_by_network:
        try:
            current_network = MainProvider.interface.id
            contracts = stakecontracts.db.get_item(current_network)
            result = __favorite_sort(contracts)
        except KeyError:
            pass

    else:
        result = list(stakecontracts.db.get_data().values())
        for index, contracts in enumerate(result):
            result[index] = __favorite_sort(contracts)

    return result


def add_new(
        contract: interface.Address, expiry_date: int,
        stake_token_contract: interface.Address, stake_token_symbol: str, stake_token_decimals: int,
        reward_token_contract: interface.Address, reward_token_symbol: str, reward_token_decimals: int
) -> bool:
    """
    Add a new stake contract
    :exception SPDatabase.ITEM_EXISTS_ERROR
    :exception OSError, FileNotFoundError, PermissionError
    :return: bool
    """

    stake_token_interface = interface.Token(
        contract=stake_token_contract,
        symbol=stake_token_symbol,
        decimals=stake_token_decimals
    )

    reward_token_interface = interface.Token(
        contract=reward_token_contract,
        symbol=reward_token_symbol,
        decimals=reward_token_decimals
    )

    stake_interface = interface.Stake(
        contract=contract,
        stake_token=stake_token_interface,
        reward_token=reward_token_interface,
        expiry_date=expiry_date,
        is_favorite=False
    )

    valid = False
    current_network = MainProvider.interface.id
    contracts = get_all(filter_by_network=True)

    is_exists = any(contract.id == stake_interface.id for contract in contracts)
    if not is_exists:
        contracts.append(stake_interface)
        stakecontracts.db.update_item(
            value=contracts, item_id=current_network, ignore_item_exists=True
        )
        valid = True

    return valid


def remove(stake_interface: interface.Stake) -> bool:
    """
    Remove specific stake interface
    :return: bool
    """

    valid = False
    if isinstance(stake_interface, interface.Stake):
        data_stored = get_all()

        for contracts in data_stored:
            for contract in contracts.copy():
                if stake_interface.id == contract.id:
                    contracts.remove(contract)
                    valid = True

        if valid:
            stakecontracts.db.dump()

    return valid


def data_export() -> bytes:
    data_stored = stakecontracts.db.get_data()
    return pickle.dumps(data_stored)


def data_import(api_url: str) -> bool:
    valid = False
    current_time = time.time()
    data_fetched = __fetching(api_url)
    data_stored = stakecontracts.db.get_data()

    # Remove expiration date contracts
    for contracts in data_stored.values():
        for contract in contracts.copy():
            if current_time > contract.expiryDate:
                contracts.remove(contract)
                valid = True

    # Merge latest contracts
    for network_id, contracts in data_fetched.items():
        data = data_stored.get(network_id, []).copy()
        for contract in contracts:
            is_exists = any(c.id == contract.id for c in data)
            if not is_exists and current_time < contract.expiryDate:
                data.append(contract)

        if data != data_stored.get(network_id):
            stakecontracts.db.update_item(
                value=data, item_id=network_id, ignore_item_exists=True, dump=False
            )
            valid = True

    if valid:
        stakecontracts.db.dump()

    return valid


class StakeEngine(object):
    def __init__(self, stake_interface: interface.Stake, sender: interface.Address = None):
        self.interface = stake_interface
        self.sender = sender
        self.contract = MainProvider.web3.eth.contract(
            address=stake_interface.contract.value(), abi=stakeABI
        )
        self.latestTransactionDetails = {
            'abi': {},
            'args': {},
            'data': b''
        }

    def owner(self) -> interface.Address:
        return interface.Address(self.contract.functions.owner().call())

    def smart_chef_factory(self) -> interface.Address:
        return interface.Address(self.contract.functions.SMART_CHEF_FACTORY().call())

    def has_user_limit(self) -> bool:
        return self.contract.functions.hasUserLimit().call()

    def locked_to_end(self) -> bool:
        return self.contract.functions.lockedToEnd().call()

    def is_initialized(self) -> bool:
        return self.contract.functions.isInitialized().call()

    def is_paused(self) -> bool:
        return self.contract.functions.paused().call()

    def last_pause_time(self) -> int:
        return self.contract.functions.lastPauseTime().call()

    def acc_token_per_share(self) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.availableToMintCurrentYear().call(),
            decimals=self.interface.rewardToken.decimals
        )

    def bonus_end_block(self) -> int:
        return self.contract.functions.bonusEndBlock().call()

    def start_block(self) -> int:
        return self.contract.functions.startBlock().call()

    def last_reward_block(self) -> int:
        return self.contract.functions.lastRewardBlock().call()

    def pool_limit_per_user(self) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.poolLimitPerUser().call(),
            decimals=self.interface.stakeToken.decimals
        )

    def reward_per_block(self) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.rewardPerBlock().call(),
            decimals=self.interface.rewardToken.decimals
        )

    def precision_factor(self) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.PRECISION_FACTOR().call(),
            decimals=self.interface.rewardToken.decimals
        )

    def reward_token(self) -> interface.Address:
        return interface.Address(self.contract.functions.rewardToken().call())

    def staked_token(self) -> interface.Address:
        return interface.Address(self.contract.functions.stakedToken().call())

    def total_supply(self) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.totalSupply().call(),
            decimals=self.interface.stakeToken.decimals
        )

    def reward_supply(self) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.rewardSupply().call(),
            decimals=self.interface.rewardToken.decimals
        )

    def balance_of(self, address: interface.Address) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.balanceOf(address.value()).call(),
            decimals=self.interface.stakeToken.decimals
        )

    def pending_reward(self, address: interface.Address) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.pendingReward(address.value()).call(),
            decimals=self.interface.rewardToken.decimals
        )

    def initialize(
            self, staked_token: interface.Address, reward_token: interface.Address,
            reward_per_block: interface.EtherAmount, start_block: int, bonus_end_block: int,
            pool_limit_per_user: int, locked_to_end: bool, admin: interface.Address
    ) -> dict:
        return self._build_transaction(
            self.contract.functions.approve(
                staked_token.value(), reward_token.value(), reward_per_block.to_wei(),
                start_block, bonus_end_block, pool_limit_per_user, locked_to_end, admin.value()
            )
        )

    def deposit(self, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.deposit(amount.to_wei())
        )

    def withdraw(self, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.withdraw(amount.to_wei())
        )

    def get_reward(self) -> dict:
        return self._build_transaction(
            self.contract.functions.getReward()
        )

    # Owner functions
    def emergency_reward_withdraw(self, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.emergencyRewardWithdraw(amount.to_wei())
        )

    def recover_wrong_tokens(self, token: interface.Address, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.recoverWrongTokens(token.value(), amount.to_wei())
        )

    def stop_reward(self) -> dict:
        return self._build_transaction(
            self.contract.functions.stopReward()
        )

    def set_pause(self, paused: bool) -> dict:
        return self._build_transaction(
            self.contract.functions.setPaused(paused)
        )

    def update_pool_limit_per_user(self, status: bool, users: int) -> dict:
        return self._build_transaction(
            self.contract.functions.updatePoolLimitPerUser(status, users)
        )

    def update_reward_per_block(self, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.updateRewardPerBlock(amount.to_wei())
        )

    def update_start_and_end_blocks(self, start_block: int, bonus_end_block: int) -> dict:
        return self._build_transaction(
            self.contract.functions.updateStartAndEndBlocks(start_block, bonus_end_block)
        )

    def renounce_ownership(self) -> dict:
        return self._build_transaction(
            self.contract.functions.renounceOwnership()
        )

    def transfer_ownership(self, new_owner: interface.Address) -> dict:
        return self._build_transaction(
            self.contract.functions.transferOwnership(new_owner.value())
        )

    def set_favorite(self, status: bool):
        self.interface.isFavorite = status
        stakecontracts.db.dump()

    def _build_transaction(self, method) -> dict:
        if not isinstance(self.sender, interface.Address):
            raise ValueError("The sender must not be a zero address")

        abi = method.abi
        abi_name = abi['name']
        args = {}

        # Get args
        for index, npt in enumerate(abi['inputs']):
            npt_name = npt['name']
            npt_type = npt['type']

            try:
                value = method.args[index]
            except IndexError:
                args[npt_name] = None
                continue

            if npt_type == 'address':
                args[npt_name] = interface.Address(value)
            elif npt_type == 'uint256' and npt_name in ['_poolLimitPerUser', '_amount']:
                args[npt_name] = interface.WeiAmount(
                    value=value, decimals=self.interface.stakeToken.decimals
                )
            elif npt_type == 'uint256' and npt_name in ['_rewardPerBlock', '_rewardAmount']:
                args[npt_name] = interface.WeiAmount(
                    value=value, decimals=self.interface.rewardToken.decimals
                )
            elif npt_type == 'uint256' and abi_name == 'recoverWrongTokens':
                contract = MainProvider.web3.eth.contract(
                    address=args['_tokenAddress'].value(), abi=tokenABI
                )
                args[npt_name] = interface.WeiAmount(
                    value=value, decimals=contract.functions.decimals().call()
                )
            else:
                args[npt_name] = value

        tx = method.buildTransaction({'from': self.sender.value()})
        tx[Metadata.NONCE] = MainProvider.web3.eth.get_transaction_count(self.sender.value())
        self.latestTransactionDetails.update({
            'abi': abi, 'args': args, 'data': tx['data']
        })

        return tx


__all__ = ['get_all', 'add_new', 'remove', 'data_export', 'data_import', 'StakeEngine']
