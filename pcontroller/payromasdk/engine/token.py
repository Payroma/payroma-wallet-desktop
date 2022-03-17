from .provider import MainProvider
from ..abis import tokenABI
from ..tools import interface


class TokenEngine(object):
    def __init__(self, token_interface: interface.Token, sender: interface.Address = None):
        self.interface = token_interface
        self.sender = sender
        self.contract = MainProvider.web3.eth.contract(
            address=token_interface.contract.value(), abi=tokenABI
        )

    def name(self) -> str:
        return self.contract.functions.name().call()

    def symbol(self) -> str:
        return self.contract.functions.symbol().call()

    def decimals(self) -> int:
        return self.contract.functions.decimals().call()

    def total_supply(self) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.totalSupply().call(),
            decimals=self.interface.decimals
        )

    def balance_of(self, address: interface.Address) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.balanceOf(address.value()).call(),
            decimals=self.interface.decimals
        )

    def allowance(self, owner: interface.Address, spender: interface.Address) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.allowance(owner.value(), spender.value()).call(),
            decimals=self.interface.decimals
        )

    def approve(self, spender: interface.Address, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.approve(spender.value(), amount.to_wei())
        )

    def transfer(self, recipient: interface.Address, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.transfer(recipient.value(), amount.to_wei())
        )

    def transfer_from(
            self, sender: interface.Address, recipient: interface.Address, amount: interface.EtherAmount
    ) -> dict:
        return self._build_transaction(
            self.contract.functions.transferFrom(sender.value(), recipient.value(), amount.to_wei())
        )

    def increase_allowance(self, spender: interface.Address, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.increaseAllowance(spender.value(), amount.to_wei())
        )

    def decrease_allowance(self, spender: interface.Address, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.decreaseAllowance(spender.value(), amount.to_wei())
        )

    def _build_transaction(self, method) -> dict:
        if not isinstance(self.sender, interface.Address):
            raise ValueError("The sender must not be a zero address")

        return method.buildTransaction({'from': self.sender.value()})


class PayromaTokenEngine(TokenEngine):
    def __init__(self, token_interface: interface.Token, sender: interface.Address = None):
        super(PayromaTokenEngine, self).__init__(token_interface, sender)

    def owner(self) -> interface.Address:
        return interface.Address(self.contract.functions.owner().call())

    def inflation_rate_annually(self) -> int:
        return self.contract.functions.inflationRateAnnually().call()

    def inflation_duration_end_date(self) -> int:
        return self.contract.functions.inflationDurationEndDate().call()

    def available_to_mint_current_year(self) -> interface.WeiAmount:
        return interface.WeiAmount(
            value=self.contract.functions.availableToMintCurrentYear().call(),
            decimals=self.interface.decimals
        )

    def transfer_multiple(self, addresses: list, amounts: list) -> dict:
        _addresses = [i.value() if isinstance(i, interface.Address) else i for i in addresses]
        _amounts = [i.to_wei() if isinstance(i, interface.EtherAmount) else i for i in amounts]

        return self._build_transaction(
            self.contract.functions.transferMultiple(_addresses, _amounts)
        )

    def burn(self, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.burn(amount.to_wei())
        )

    def burn_from(self, spender: interface.Address, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.burnFrom(spender.value(), amount.to_wei())
        )

    # Owner functions
    def mint(self, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.mint(amount.to_wei())
        )

    def recover_token(self, token_address: interface.Address, amount: interface.EtherAmount) -> dict:
        return self._build_transaction(
            self.contract.functions.recoverToken(token_address.value(), amount.to_wei())
        )

    def renounce_ownership(self) -> dict:
        return self._build_transaction(
            self.contract.functions.renounceOwnership()
        )

    def transfer_ownership(self, new_owner: interface.Address) -> dict:
        return self._build_transaction(
            self.contract.functions.transferOwnership(new_owner.value())
        )


__all__ = ['TokenEngine', 'PayromaTokenEngine']
