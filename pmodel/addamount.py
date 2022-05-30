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
        self.__continueThread.signal.resultSignal.connect(self.__transaction_sender)
        self.__continueThread.finished.connect(self.continue_completed)

        # Variables
        self.__isTyping = False
        self.__currentWalletEngine = None
        self.__recipientAddress = None
        self.__tokenEngines = []
        self.__tokenEngine = None
        self.__tokenBalance = None

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine

    def network_changed_event(self, name: str, status: bool):
        self.refresh()

    def withdraw_address_changed_event(self, address: str):
        if self.__recipientAddress and self.__recipientAddress.value() == address:
            return

        try:
            self.__recipientAddress = payromasdk.tools.interface.Address(address)
            self.refresh()
        except ValueError:
            self.__recipientAddress = None

    @pyqtSlot(int)
    def token_changed(self, index: int):
        if index < 0:
            return

        self.__tokenEngine = self.__tokenEngines[index]
        self.__tokenChangedThread.start()

    def __token_changed_core(self):
        result = ThreadingResult(
            params={
                'index': None,
                'balance': None
            }
        )

        try:
            owner = self.__currentWalletEngine.address()
            self.__tokenBalance = self.__tokenEngine.balance_of(owner)

            result.isValid = True

            if result.isValid:
                result.params['index'] = self.__tokenEngines.index(self.__tokenEngine)
                result.params['balance'] = self.__tokenBalance.to_ether_string()

        except requests.exceptions.ConnectionError:
            pass

        except Exception as err:
            result.error(str(err))

        self.__tokenChangedThread.signal.resultSignal.emit(result)

    def __token_changed_ui(self, result: ThreadingResult):
        if result.isValid:
            super(AddAmountModel, self).token_changed(
                result.params['index'], result.params['balance']
            )

        elif result.isError:
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
            balance = self.__tokenBalance.to_ether()
            if (amount <= balance) and (amount > 0):
                valid = True

        self.__isTyping = False
        super(AddAmountModel, self).amount_changed(text, valid)

    @pyqtSlot()
    def max_clicked(self):
        super(AddAmountModel, self).max_clicked(
            self.__tokenBalance.to_ether_string(currency_format=False)
        )

    @pyqtSlot()
    def continue_clicked(self):
        if self.__isTyping or self.__continueThread.isRunning():
            return

        super(AddAmountModel, self).continue_clicked()
        self.__continueThread.start()

    def __continue_clicked_core(self):
        result = ThreadingResult(
            message=translator("Transaction creation failed, please try again."),
            params={
                'tx': None,
                'details': None,
                'symbol': None
            }
        )

        try:
            if isinstance(self.__tokenEngine, payromasdk.engine.token.TokenEngine):
                # Token builder
                tx = self.__tokenEngine.transfer(
                    recipient=self.__recipientAddress,
                    amount=payromasdk.tools.interface.EtherAmount(
                        value=self.get_amount_text(), decimals=self.__tokenEngine.interface.decimals
                    )
                )
            else:
                # Coin builder
                tx = self.__tokenEngine.build_transaction(
                    from_address=self.__currentWalletEngine.address(),
                    to_address=self.__recipientAddress,
                    value=payromasdk.tools.interface.EtherAmount(
                        value=self.get_amount_text(), decimals=18
                    )
                )

            # Add gas fee and estimated amount
            payromasdk.MainProvider.add_gas(
                tx_data=tx, amount_adjustment=True,
                eip1559_enabled=payromasdk.MainProvider.eip1559_supported()
            )

            result.isValid = True

            if result.isValid:
                result.params['tx'] = tx
                result.params['symbol'] = self.__tokenEngine.interface.symbol
                try:
                    result.params['details'] = self.__tokenEngine.latestTransactionDetails
                except AttributeError:
                    result.params['details'] = {}

        except requests.exceptions.ConnectionError:
            pass

        except ValueError:
            result.message = translator("Insufficient funds for transfer, maybe it needs gas fee.")

        except Exception as err:
            result.error(str(err))

        self.__continueThread.signal.resultSignal.emit(result)

    @staticmethod
    def __transaction_sender(result: ThreadingResult):
        if result.isValid:
            event.transactionSenderChanged.notify(
                tx=result.params['tx'],
                details=result.params['details'],
                symbol=result.params['symbol']
            )
        else:
            result.show_message()

    def reset(self):
        super(AddAmountModel, self).reset()
        self.__tokenEngines.clear()

    def refresh(self):
        if not self.__currentWalletEngine or not self.__recipientAddress:
            return

        self.reset()

        # Network coin
        self.__tokenEngines.append(payromasdk.MainProvider)
        self.add_item(payromasdk.MainProvider.interface.symbol)

        # Wallet tokens
        for token in self.__currentWalletEngine.tokens():
            engine = payromasdk.engine.token.TokenEngine(
                token_interface=token, sender=self.__currentWalletEngine.address()
            )

            self.__tokenEngines.append(engine)
            self.add_item(engine.interface.symbol)
