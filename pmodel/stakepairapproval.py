from plibs import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import stakepairapproval


class StakePairApprovalModel(stakepairapproval.UiForm, event.EventForm):
    def __init__(self, parent):
        super(StakePairApprovalModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__updateThread = ThreadingArea(self.__update_core)
        self.__updateThread.signal.resultSignal.connect(self.__update_ui)

        self.__approvalThread = ThreadingArea(self.__approval_clicked_core)
        self.__approvalThread.signal.resultSignal.connect(self.__transaction_sender)
        self.__approvalThread.finished.connect(self.approval_completed)

        # Variables
        self.__currentWalletEngine = None
        self.__stakeEngine = None
        self.__stakeTokenEngine = None

    def showEvent(self, a0: QShowEvent):
        super(StakePairApprovalModel, self).showEvent(a0)
        self.__updateThread.start()

    def hideEvent(self, a0: QHideEvent):
        super(StakePairApprovalModel, self).hideEvent(a0)
        self.__updateThread.stop()

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine

    def stake_pair_changed_event(self, engine: payromasdk.engine.stake.StakeEngine):
        self.reset()
        self.__stakeEngine = engine
        self.__stakeTokenEngine = payromasdk.engine.token.TokenEngine(
            token_interface=engine.interface.stakeToken, sender=self.__currentWalletEngine.address()
        )

    @pyqtSlot()
    def approval_clicked(self):
        if self.__approvalThread.isRunning():
            return

        super(StakePairApprovalModel, self).approval_clicked()
        self.__approvalThread.start()

    def __approval_clicked_core(self):
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
            tx = self.__stakeTokenEngine.approve(
                spender=self.__stakeEngine.interface.contract,
                amount=payromasdk.tools.interface.EtherAmount(
                    value=115792089237316195423570985008687907853269984665640564039457,
                    decimals=self.__stakeTokenEngine.interface.decimals
                )
            )

            # Add gas fee and estimated amount
            payromasdk.MainProvider.add_gas(
                tx_data=tx, eip1559_enabled=payromasdk.MainProvider.eip1559_supported()
            )

            result.isValid = True

            if result.isValid:
                result.params['tx'] = tx
                result.params['details'] = self.__stakeTokenEngine.latestTransactionDetails
                result.params['symbol'] = self.__stakeTokenEngine.interface.symbol

        except requests.exceptions.ConnectionError:
            pass

        except ValueError:
            result.message = translator("Insufficient funds for transfer, maybe it needs gas fee.")

        except Exception as err:
            result.error(str(err))

        self.__approvalThread.signal.resultSignal.emit(result)

    def __update_core(self):
        result = ThreadingResult(
            message=translator("This staking contract needs approval.")
        )

        try:
            owner = self.__currentWalletEngine.address()
            balance = self.__stakeTokenEngine.balance_of(owner)
            allowance = self.__stakeTokenEngine.allowance(
                owner=owner, spender=self.__stakeEngine.interface.contract
            )

            if allowance.value() > balance.value():
                result.isValid = True

        except requests.exceptions.ConnectionError:
            result.message = translator("Unable to connect, make sure you are connected to the internet.")

        except Exception as err:
            result.error(str(err))

        self.__updateThread.signal.resultSignal.emit(result)

    def __update_ui(self, result: ThreadingResult):
        if result.isValid:
            event.stakePairApproved.notify()
        else:
            result.show_message()
            if not result.isError:
                self.unlock()

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
