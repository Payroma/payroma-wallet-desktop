from plibs import *
from pcontroller import payromasdk, event, ThreadingResult, ThreadingArea
from pui import tokenslist
from pmodel import tokenitem


class TokensListModel(tokenslist.UiForm, event.EventForm):
    def __init__(self, parent):
        super(TokensListModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__updateThread = ThreadingArea(self.__update_core)
        self.__updateThread.signal.resultSignal.connect(self.__update_ui)

        # Variables
        self.__currentWalletEngine = None
        self.__tokenItems = []

    def showEvent(self, a0: QShowEvent):
        super(TokensListModel, self).showEvent(a0)
        self.__updateThread.start()

    def hideEvent(self, a0: QHideEvent):
        super(TokensListModel, self).hideEvent(a0)
        self.__updateThread.stop()

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

    def __update_core(self):
        while self.__updateThread.isRunning():
            result = ThreadingResult()

            try:
                owner = self.__currentWalletEngine.address()
                for item in self.__tokenItems:
                    try:
                        result.params.update({
                            item: item.engine().balance_of(owner).to_ether_string()
                        })
                    except web3.exceptions.BadFunctionCallOutput:
                        continue

                result.isValid = True

            except requests.exceptions.ConnectionError:
                pass

            except Exception as err:
                result.error(str(err))

            self.__updateThread.signal.resultSignal.emit(result)
            time.sleep(10)

    @staticmethod
    def __update_ui(result: ThreadingResult):
        if result.isValid:
            for item, balance in result.params.items():
                try:
                    item.set_balance(balance)
                except RuntimeError:
                    continue

        elif result.isError:
            result.show_message()
