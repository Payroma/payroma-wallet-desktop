from ..tools import interface
from web3 import Web3, exceptions, datastructures


class Metadata:
    FROM = 'from'
    TO = 'to'
    VALUE = 'value'
    GAS = 'gas'
    GAS_PRICE = 'gasPrice'
    MAX_FEE_PER_GAS = 'maxFeePerGas'
    MAX_PRIORITY_FEE_PER_GAS = 'maxPriorityFeePerGas'
    DATA = 'data'
    NONCE = 'nonce'
    CHAIN_ID = 'chainId'
    ESTIMATED_GAS = 'estimatedGas'
    MAX_FEE = 'maxFee'
    TOTAL = 'total'
    MAX_AMOUNT = 'maxAmount'


class EIP1559Metadata:
    SLOW = 'slow'
    MEDIUM = 'medium'
    FAST = 'fast'
    BLOCK_NUMBER = 'blockNumber'
    BASE_FEE_PER_GAS = 'baseFeePerGas'
    GAS_USED_RATIO = 'gasUsedRatio'
    PRIORITY_FEE_PER_GAS = 'priorityFeePerGas'


class __Provider(object):
    def __init__(self):
        self.__contract = None

        self.interface = None
        self.web3 = None

    def connect(self, network_interface: interface.Network) -> bool:
        valid = False
        if isinstance(network_interface, interface.Network):
            self.interface = network_interface
            self.web3 = Web3(Web3.HTTPProvider(self.interface.rpc))
            valid = self.web3.isConnected()

        return valid

    def is_connected(self) -> bool:
        return self.web3.isConnected()

    def build_transaction(
            self, from_address: interface.Address, to_address: interface.Address,
            value: interface.EtherAmount, data_bytes: bytes = b''
    ) -> dict:
        return {
            Metadata.FROM: from_address.value(),
            Metadata.TO: to_address.value(),
            Metadata.VALUE: value.to_wei(),
            Metadata.DATA: data_bytes,
            Metadata.NONCE: self.web3.eth.get_transaction_count(from_address.value()),
            Metadata.CHAIN_ID: self.interface.chainID
        }

    def add_gas(
            self, tx_data: dict, eip1559_enabled: bool = False, rate: str = EIP1559Metadata.MEDIUM
    ) -> dict:
        self.__remove_fee(tx_data)
        gas_limit = self.web3.eth.estimate_gas(tx_data)

        if eip1559_enabled:
            tx_data.update(
                self.__estimate_gas_eip1559()[rate]
            )
            estimated_gas = gas_limit * tx_data.pop(Metadata.ESTIMATED_GAS)
            max_fee = gas_limit * tx_data[Metadata.MAX_FEE_PER_GAS]
        else:
            tx_data.update({
                Metadata.GAS_PRICE: self.web3.eth.gas_price
            })
            estimated_gas = gas_limit * tx_data[Metadata.GAS_PRICE]
            max_fee = estimated_gas

        total = estimated_gas + tx_data[Metadata.VALUE]
        max_amount = max_fee + tx_data[Metadata.VALUE]

        tx_data.update({
            Metadata.GAS: gas_limit
        })

        return {
            Metadata.ESTIMATED_GAS: interface.WeiAmount(value=estimated_gas, decimals=18),
            Metadata.MAX_FEE: interface.WeiAmount(value=max_fee, decimals=18),
            Metadata.TOTAL: interface.WeiAmount(value=total, decimals=18),
            Metadata.MAX_AMOUNT: interface.WeiAmount(value=max_amount, decimals=18)
        }

    def send_transaction(self, tx_data: dict, private_key: str) -> interface.TXHash:
        signed_txn = self.web3.eth.account.sign_transaction(tx_data, private_key=private_key)
        self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return interface.TXHash(self.web3.toHex(signed_txn.hash))

    def get_transaction(self, transaction_hash: interface.TXHash) -> datastructures.AttributeDict:
        try:
            return self.web3.eth.get_transaction(transaction_hash.value())
        except exceptions.TransactionNotFound:
            return datastructures.AttributeDict(dict())

    def get_transaction_receipt(self, transaction_hash: interface.TXHash) -> datastructures.AttributeDict:
        try:
            return self.web3.eth.get_transaction_receipt(transaction_hash.value())
        except exceptions.TransactionNotFound:
            return datastructures.AttributeDict(dict())

    @staticmethod
    def __remove_fee(tx_data: dict):
        for param in [
            Metadata.GAS, Metadata.GAS_PRICE, Metadata.MAX_PRIORITY_FEE_PER_GAS, Metadata.MAX_FEE_PER_GAS
        ]:
            try:
                del tx_data[param]
            except KeyError:
                continue

    def __fee_history(self) -> list:
        historical_blocks = 10
        fee_history = self.web3.eth.fee_history(historical_blocks, 'pending', [25, 50, 75])
        oldest_block = fee_history.oldestBlock
        latest_block = oldest_block + historical_blocks

        return [
            {
                EIP1559Metadata.BLOCK_NUMBER: block_number,
                EIP1559Metadata.BASE_FEE_PER_GAS: fee_history.baseFeePerGas[index],
                EIP1559Metadata.GAS_USED_RATIO: fee_history.gasUsedRatio[index],
                EIP1559Metadata.PRIORITY_FEE_PER_GAS: fee_history.reward[index]
            } for index, block_number in enumerate(range(oldest_block, latest_block))
        ]

    def __estimate_gas_eip1559(self) -> dict:
        rates = [EIP1559Metadata.SLOW, EIP1559Metadata.MEDIUM, EIP1559Metadata.FAST]
        fee_history = self.__fee_history()
        base_fee = self.web3.eth.get_block('pending').baseFeePerGas
        result = {}

        for index, rate in enumerate(rates):
            all_priority_fee = [i[EIP1559Metadata.PRIORITY_FEE_PER_GAS][index] for i in fee_history]
            priority_fee = max(all_priority_fee)
            estimated_gas = int(0.9 * base_fee + priority_fee)
            max_fee = int(1.5 * estimated_gas)
            if priority_fee >= max_fee or priority_fee <= 0:
                raise ValueError("Max fee must exceed the priority fee")

            result.update({
                rate: {
                    Metadata.MAX_PRIORITY_FEE_PER_GAS: priority_fee,
                    Metadata.ESTIMATED_GAS: estimated_gas,
                    Metadata.MAX_FEE_PER_GAS: max_fee
                }
            })

        return result


class _MainProvider(__Provider):
    def connect(self, network_interface: interface.Network) -> bool:
        interface.Address.networkInterface = network_interface
        interface.TXHash.networkInterface = network_interface
        interface.Stake.networkInterface = network_interface
        return super(_MainProvider, self).connect(network_interface)

    def balance_of(self, address: interface.Address) -> interface.WeiAmount:
        return interface.WeiAmount(
            self.web3.eth.get_balance(address.value()), decimals=18
        )

    def block_number(self) -> int:
        return self.web3.eth.block_number

    def eip1559_supported(self) -> bool:
        valid = False

        if self.interface:
            if '.infura.io/v3' in self.interface.rpc and self.interface.symbol == 'ETH':
                valid = True

        return valid


class _PNSProvider(__Provider):
    def contract(self) -> interface.Address:
        return self.__contract

    def set_contract(self, address: interface.Address):
        self.__contract = address


MainProvider = _MainProvider()
PNSProvider = _PNSProvider()
__all__ = ['Metadata', 'MainProvider', 'PNSProvider']
