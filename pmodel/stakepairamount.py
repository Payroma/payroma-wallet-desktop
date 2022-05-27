from plibs import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import stakepairamount


class StakePairAmountModel(stakepairamount.UiForm, event.EventForm):
    def __init__(self, parent):
        super(StakePairAmountModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__updateThread = ThreadingArea(self.__update_core)
        self.__updateThread.signal.resultSignal.connect(self.__update_ui)

        self.__depositThread = ThreadingArea(self.__deposit_clicked_core)
        self.__depositThread.signal.resultSignal.connect(self.__transaction_sender)
        self.__depositThread.finished.connect(self.deposit_completed)

        self.__withdrawThread = ThreadingArea(self.__withdraw_clicked_core)
        self.__withdrawThread.signal.resultSignal.connect(self.__transaction_sender)
        self.__withdrawThread.finished.connect(self.withdraw_completed)

        self.__claimThread = ThreadingArea(self.__claim_clicked_core)
        self.__claimThread.signal.resultSignal.connect(self.__transaction_sender)
        self.__claimThread.finished.connect(self.claim_completed)

        # Variables
        self.__isTyping = False
        self.__currentWalletEngine = None
        self.__stakeEngine = None
        self.__stakeTokenEngine = None
        self.__balanceAmount = None
        self.__stakedAmount = None
        self.__claimAmount = None

    def showEvent(self, a0: QShowEvent):
        super(StakePairAmountModel, self).showEvent(a0)
        self.__updateThread.start()

    def hideEvent(self, a0: QHideEvent):
        super(StakePairAmountModel, self).hideEvent(a0)
        self.__updateThread.stop()

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine

    def stake_pair_changed_event(self, engine: payromasdk.engine.stake.StakeEngine):
        self.reset()
        self.__stakeEngine = engine
        self.__stakeTokenEngine = payromasdk.engine.token.TokenEngine(
            token_interface=engine.interface.stakeToken, sender=self.__currentWalletEngine.address()
        )

    @pyqtSlot(str)
    def deposit_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__deposit_changed(text))

    def __deposit_changed(self, text: str):
        valid = False
        if text != self.get_deposit_text():
            return

        if text and self.__balanceAmount:
            amount = float(self.get_deposit_text())
            balance = self.__balanceAmount.to_ether()
            if (amount <= balance) and (amount > 0):
                valid = True

        self.__isTyping = False
        super(StakePairAmountModel, self).deposit_changed(text, valid)

    @pyqtSlot(str)
    def withdraw_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__withdraw_changed(text))

    def __withdraw_changed(self, text: str):
        valid = False
        if text != self.get_withdraw_text():
            return

        if text and self.__stakedAmount:
            amount = float(self.get_withdraw_text())
            staked = self.__stakedAmount.to_ether()
            if (amount <= staked) and (amount > 0):
                valid = True

        self.__isTyping = False
        super(StakePairAmountModel, self).withdraw_changed(text, valid)

    @pyqtSlot(str)
    def claim_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__claim_changed(text))

    def __claim_changed(self, text: str):
        valid = False

        if text and self.__claimAmount:
            amount = self.__claimAmount.to_ether()
            if amount > 0:
                valid = True

        self.__isTyping = False
        super(StakePairAmountModel, self).claim_changed(text, valid)

    @pyqtSlot()
    def deposit_clicked(self):
        if self.__isTyping or self.__depositThread.isRunning():
            return

        super(StakePairAmountModel, self).deposit_clicked()
        self.__depositThread.start()

    def __deposit_clicked_core(self):
        result = ThreadingResult(
            message=translator("Transaction creation failed, please try again."),
            params={
                'tx': None,
                'details': None,
                'symbol': None
            }
        )

        try:
            # Transaction builder
            tx = self.__stakeEngine.deposit(
                amount=payromasdk.tools.interface.EtherAmount(
                    value=float(self.get_deposit_text()),
                    decimals=self.__stakeEngine.interface.stakeToken.decimals
                )
            )

            # Add gas fee and estimated amount
            payromasdk.MainProvider.add_gas(
                tx_data=tx, eip1559_enabled=payromasdk.MainProvider.eip1559_supported()
            )

            result.isValid = True

            if result.isValid:
                result.params['tx'] = tx
                result.params['details'] = self.__stakeEngine.latestTransactionDetails
                result.params['symbol'] = self.__stakeEngine.interface.stakeToken.symbol

        except requests.exceptions.ConnectionError:
            pass

        except ValueError:
            result.message = translator("Insufficient funds for transfer, maybe it needs gas fee.")

        except Exception as err:
            result.error(str(err))

        self.__depositThread.signal.resultSignal.emit(result)

    @pyqtSlot()
    def withdraw_clicked(self):
        if self.__isTyping or self.__withdrawThread.isRunning():
            return

        super(StakePairAmountModel, self).withdraw_clicked()
        self.__withdrawThread.start()

    def __withdraw_clicked_core(self):
        result = ThreadingResult(
            message=translator("Transaction creation failed, please try again."),
            params={
                'tx': None,
                'details': None,
                'symbol': None
            }
        )

        try:
            # Transaction builder
            tx = self.__stakeEngine.withdraw(
                amount=payromasdk.tools.interface.EtherAmount(
                    value=float(self.get_withdraw_text()),
                    decimals=self.__stakeEngine.interface.stakeToken.decimals
                )
            )

            # Add gas fee and estimated amount
            payromasdk.MainProvider.add_gas(
                tx_data=tx, eip1559_enabled=payromasdk.MainProvider.eip1559_supported()
            )

            result.isValid = True

            if result.isValid:
                result.params['tx'] = tx
                result.params['details'] = self.__stakeEngine.latestTransactionDetails
                result.params['symbol'] = self.__stakeEngine.interface.stakeToken.symbol

        except requests.exceptions.ConnectionError:
            pass

        except ValueError:
            result.message = translator("Insufficient funds for transfer, maybe it needs gas fee.")

        except Exception as err:
            result.error(str(err))

        self.__withdrawThread.signal.resultSignal.emit(result)

    @pyqtSlot()
    def claim_clicked(self):
        if self.__isTyping or self.__claimThread.isRunning():
            return

        super(StakePairAmountModel, self).claim_clicked()
        self.__claimThread.start()

    def __claim_clicked_core(self):
        result = ThreadingResult(
            message=translator("Transaction creation failed, please try again."),
            params={
                'tx': None,
                'details': None,
                'symbol': None
            }
        )

        try:
            # Transaction builder
            tx = self.__stakeEngine.get_reward()

            # Add gas fee and estimated amount
            payromasdk.MainProvider.add_gas(
                tx_data=tx, eip1559_enabled=payromasdk.MainProvider.eip1559_supported()
            )

            result.isValid = True

            if result.isValid:
                result.params['tx'] = tx
                result.params['details'] = self.__stakeEngine.latestTransactionDetails
                result.params['symbol'] = self.__stakeEngine.interface.rewardToken.symbol

        except requests.exceptions.ConnectionError:
            pass

        except ValueError:
            result.message = translator("Insufficient funds for transfer, maybe it needs gas fee.")

        except Exception as err:
            result.error(str(err))

        self.__claimThread.signal.resultSignal.emit(result)

    def reset(self):
        super(StakePairAmountModel, self).reset()
        self.__balanceAmount = None
        self.__stakedAmount = None
        self.__claimAmount = None

    def __update_core(self):
        while self.__updateThread.isRunning():
            result = ThreadingResult()

            try:
                owner = self.__currentWalletEngine.address()
                self.__balanceAmount = self.__stakeTokenEngine.balance_of(owner)
                self.__stakedAmount = self.__stakeEngine.balance_of(owner)
                self.__claimAmount = self.__stakeEngine.pending_reward(owner)

                result.isValid = True

            except requests.exceptions.ConnectionError:
                pass

            except Exception as err:
                result.error(str(err))

            self.__updateThread.signal.resultSignal.emit(result)
            time.sleep(10)

    def __update_ui(self, result: ThreadingResult):
        if result.isValid:
            self.set_data(
                balance=self.__balanceAmount.to_ether_string(),
                staked=self.__stakedAmount.to_ether_string(),
                claim=self.__claimAmount.to_ether_string(),
                stake_symbol=self.__stakeEngine.interface.stakeToken.symbol,
                earn_symbol=self.__stakeEngine.interface.rewardToken.symbol
            )
        elif result.isError:
            result.show_message()

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
