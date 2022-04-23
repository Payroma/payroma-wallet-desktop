from plibs import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import tokenslist
from pmodel import tokenitem


class TokensListModel(tokenslist.UiForm, event.EventForm):
    def __init__(self, parent):
        super(TokensListModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__balanceUpdateThread = ThreadingArea(self.__balance_update_core)
        self.__balanceUpdateThread.signal.resultSignal.connect(self.__balance_update_ui)

        # Variables
        self.__currentWalletEngine = None
        self.__tokenItems = []

    def showEvent(self, a0: QShowEvent):
        super(TokensListModel, self).showEvent(a0)
        self.__balanceUpdateThread.start()

    def hideEvent(self, a0: QHideEvent):
        super(TokensListModel, self).hideEvent(a0)
        self.__balanceUpdateThread.terminate()
        self.__balanceUpdateThread.wait()

    def token_edited_event(self):
        self.refresh()

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine
        self.refresh()

    def network_changed_event(self, name: str, status: bool):
        self.refresh()

    def reset(self):
        super(TokensListModel, self).reset()
        self.__tokenItems.clear()

    def refresh(self):
        if not self.__currentWalletEngine:
            return

        self.reset()

        # Network coin
        item = tokenitem.TokenItem(self)
        item.set_master()
        self.add_item(item)
        self.__tokenItems.append(item)

        # Wallet tokens
        for token in self.__currentWalletEngine.tokens():
            item = tokenitem.TokenItem(self)
            item.set_engine(
                token_engine=payromasdk.engine.token.TokenEngine(
                    token_interface=token, sender=self.__currentWalletEngine.address()
                ),
                wallet_engine=self.__currentWalletEngine
            )

            self.add_item(item)
            self.__tokenItems.append(item)

        QTimer().singleShot(100, self.repaint)

    def __balance_update_core(self):
        result = ThreadingResult(
            message=translator("Unable to connect, make sure you are connected to the internet")
        )

        while self.__balanceUpdateThread.isRunning():
            try:
                for token in self.__tokenItems:
                    self.__balanceUpdateThread.signal.resultSignal.emit(ThreadingResult(
                        is_valid=True,
                        params={
                            'token': token,
                            'balance': token.engine().balance_of(self.__currentWalletEngine.address())
                        }
                    ))

                continue

            except requests.exceptions.ConnectionError:
                pass

            except Exception as err:
                result.error(str(err))

            finally:
                time.sleep(10)

            self.__balanceUpdateThread.signal.resultSignal.emit(result)

    @staticmethod
    def __balance_update_ui(result: ThreadingResult):
        if result.isValid:
            try:
                result.params['token'].set_balance(result.params['balance'].to_ether_string())
            except RuntimeError:
                pass
        else:
            result.show_message()
