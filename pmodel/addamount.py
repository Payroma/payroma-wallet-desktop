from plibs import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import addamount


class AddAmountModel(addamount.UiForm, event.EventForm):
    def __init__(self, parent):
        super(AddAmountModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__tokenChangedThread = ThreadingArea(self.__token_changed_core)
        self.__tokenChangedThread.signal.resultSignal.connect(self.__token_changed_ui)

        self.__continueThread = ThreadingArea(self.__continue_clicked_core)
        self.__continueThread.signal.resultSignal.connect(self.__continue_clicked_ui)

        # Variables
        self.__isTyping = False
        self.__currentWalletEngine = None
        self.__recipientAddress = None
        self.__tokenItems = {}
        self.__currentTokenIndex = 0
        self.__currentTokenBalance = payromasdk.tools.interface.WeiAmount(0, 18)

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine

    def network_changed_event(self, name: str, status: bool):
        self.refresh()

    def withdraw_address_changed_event(self, address: str):
        try:
            self.__recipientAddress = payromasdk.tools.interface.Address(address)
            self.refresh()
        except ValueError:
            self.__recipientAddress = None

    @pyqtSlot(int)
    def token_changed(self, index: int):
        if index < 0:
            return

        self.__currentTokenIndex = index

        if self.__tokenChangedThread.isRunning():
            self.__tokenChangedThread.terminate()
            self.__tokenChangedThread.wait()

        self.__tokenChangedThread.start()

    def __token_changed_core(self):
        result = ThreadingResult(
            message=translator("Unable to connect, make sure you are connected to the internet")
        )

        try:
            self.__currentTokenBalance = self.__tokenItems[self.__currentTokenIndex].balance_of(
                self.__currentWalletEngine.address()
            )
            result.isValid = True

        except requests.exceptions.ConnectionError:
            pass

        except Exception as err:
            result.error(str(err))

        self.__tokenChangedThread.signal.resultSignal.emit(result)

    def __token_changed_ui(self, result: ThreadingResult):
        if result.isValid:
            super(AddAmountModel, self).token_changed(
                self.__currentTokenIndex, self.__currentTokenBalance.to_ether_string()
            )
        else:
            result.show_message()

    @pyqtSlot(str)
    def amount_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__amount_changed(text))

    def __amount_changed(self, text: str):
        valid = False
        if text != self.get_amount_text():
            return

        if text:
            amount = float(self.get_amount_text())
            balance = self.__currentTokenBalance.to_ether()
            if (amount <= balance) and (amount > 0):
                valid = True

        self.__isTyping = False
        super(AddAmountModel, self).amount_changed(text, valid)

    @pyqtSlot()
    def max_clicked(self):
        super(AddAmountModel, self).max_clicked(
            self.__currentTokenBalance.to_ether_string(currency_format=False)
        )

    @pyqtSlot()
    def continue_clicked(self):
        if self.__isTyping or self.__continueThread.isRunning():
            return

        super(AddAmountModel, self).continue_clicked()
        self.__continueThread.start()

    def __continue_clicked_core(self):
        result = ThreadingResult(
            message=translator("Transaction creation failed, please try again"),
            params={
                'tx': {},
                'details': {},
                'symbol': payromasdk.MainProvider.interface.symbol
            }
        )

        try:
            engine = self.__tokenItems[self.__currentTokenIndex]

            # Transaction building
            if isinstance(engine, payromasdk.engine.token.TokenEngine):
                # Token builder
                tx = engine.transfer(
                    recipient=self.__recipientAddress,
                    amount=payromasdk.tools.interface.EtherAmount(
                        value=self.get_amount_text(), decimals=engine.interface.decimals
                    )
                )
            else:
                # Coin builder
                tx = engine.build_transaction(
                    from_address=self.__currentWalletEngine.address(),
                    to_address=self.__recipientAddress,
                    value=payromasdk.tools.interface.EtherAmount(
                        value=self.get_amount_text(), decimals=18
                    )
                )

            # Add gas fee and estimated amount
            gas = payromasdk.MainProvider.add_gas(
                tx_data=tx, eip1559_enabled=payromasdk.MainProvider.eip1559_supported()
            )
            max_fee = gas[payromasdk.engine.provider.Metadata.MAX_FEE].value()
            max_amount = gas[payromasdk.engine.provider.Metadata.MAX_AMOUNT].value()
            balance = self.__currentTokenBalance.value()
            if max_amount > balance:
                amount = balance - max_fee
                if amount <= 0:
                    raise ValueError
                tx[payromasdk.engine.provider.Metadata.VALUE] = balance - max_fee

            result.isValid = True

            if result.isValid:
                result.params['tx'] = tx
                try:
                    result.params['details'] = engine.latestTransactionDetails
                    result.params['symbol'] = engine.symbol()
                except AttributeError:
                    pass

        except ValueError:
            result.message = translator("Insufficient funds for transfer, maybe it needs gas fee.")

        except Exception as err:
            result.error(str(err))

        self.__continueThread.signal.resultSignal.emit(result)

    def __continue_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            event.transactionSenderChanged.notify(
                tx=result.params['tx'],
                details=result.params['details'],
                symbol=result.params['symbol']
            )
        else:
            result.show_message()

        self.continue_completed()

    def reset(self):
        super(AddAmountModel, self).reset()
        self.__tokenItems.clear()

    def refresh(self):
        if not self.__currentWalletEngine:
            return

        self.reset()

        assets = [payromasdk.MainProvider] + self.__currentWalletEngine.tokens()

        # Add assets to combobox
        for index, asset in enumerate(assets):
            if isinstance(asset, payromasdk.tools.interface.Token):
                engine = payromasdk.engine.token.TokenEngine(
                    token_interface=asset, sender=self.__currentWalletEngine.address()
                )
            else:
                engine = asset

            self.add_item(engine.interface.symbol)
            self.__tokenItems[index] = engine
