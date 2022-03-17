from .provider import MainProvider
from ..abis import stakeABI
from ..tools import interface


class StakeEngine(object):
    def __init__(self, stake_interface: interface.Stake, sender: interface.Address = None):
        self.interface = stake_interface
        self.sender = sender
        self.contract = MainProvider.web3.eth.contract(
            address=stake_interface.contract.value(), abi=stakeABI
        )

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

    def _build_transaction(self, method) -> dict:
        if not isinstance(self.sender, interface.Address):
            raise ValueError("The sender must not be a zero address")

        return method.buildTransaction({'from': self.sender.value()})


__all__ = ['StakeEngine']
