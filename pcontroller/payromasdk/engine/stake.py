from .provider import MainProvider, Metadata
from ..abis import tokenABI, stakeABI
from ..tools import interface
from ..data import stakecontracts
import requests


def __fetching(url: str) -> dict:
    try:
        return requests.get(url).json()
    except requests.exceptions.ConnectionError:
        return {}


def get_all(filter_by_network: bool = False) -> list:
    result = []

    if filter_by_network:
        try:
            current_network = MainProvider.interface.id
            result = stakecontracts.db.get_item(current_network)
        except KeyError:
            pass

    else:
        result = list(stakecontracts.db.get_data().values())

    return result


def data_import(api_url: str) -> bool:
    valid = False
    data_fetched = __fetching(api_url)

    for network_id, contracts in data_fetched.items():
        contracts_list = []

        for contract, info in contracts.items():
            stake_token = interface.Token(
                contract=interface.Address(info['stakeToken']['contract']),
                symbol=info['stakeToken']['symbol'],
                decimals=info['stakeToken']['decimals']
            )
            reward_token = interface.Token(
                contract=interface.Address(info['rewardToken']['contract']),
                symbol=info['rewardToken']['symbol'],
                decimals=info['rewardToken']['decimals']
            )
            contracts_list.append(
                interface.Stake(
                    contract=interface.Address(contract),
                    stake_token=stake_token,
                    reward_token=reward_token,
                    stake_website=info['stakeWebsite'],
                    reward_website=info['rewardWebsite'],
                    start_block=info['startBlock'],
                    end_block=info['endBlock'],
                    start_time=info['startTime'],
                    end_time=info['endTime']
                )
            )

        stakecontracts.db.update_item(
            value=contracts_list, item_id=int(network_id), ignore_item_exists=True, dump=False
        )
        valid = True

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
            value=self.contract.functions.accTokenPerShare().call(),
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
            self.contract.functions.initialize(
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

    def get_apr(self) -> str:
        result = '0%'

        if self.interface.endBlock > MainProvider.block_number():
            try:
                year = 86400 * 365
                stake_period = self.interface.endTime - self.interface.startTime
                blocks = self.interface.endBlock - self.interface.startBlock
                reward = self.reward_per_block().to_ether() * blocks
                interest = (reward / self.total_supply().to_ether()) * 100
                apr = int(year / stake_period) * interest
                result = '{:.2f}%'.format(apr)
            except ZeroDivisionError:
                pass

        return result

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


__all__ = ['get_all', 'data_import', 'StakeEngine']
