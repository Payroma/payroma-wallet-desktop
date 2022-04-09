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
        self.__engine = None
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
        self.__engine = engine
        self.refresh()

    def network_changed_event(self, name: str, status: bool):
        self.refresh()

    def reset(self):
        super(TokensListModel, self).reset()
        self.__tokenItems.clear()

    def refresh(self):
        if not self.__engine:
            return

        self.reset()

        item = tokenitem.TokenItem(self)
        item.set_master()
        self.add_item(item)
        self.__tokenItems.append(item)

        for token in self.__engine.tokens():
            item = tokenitem.TokenItem(self)
            item.set_engine(
                token_engine=payromasdk.engine.token.TokenEngine(
                    token_interface=token, sender=self.__engine.address()
                ),
                wallet_engine=self.__engine
            )

            self.add_item(item)
            self.__tokenItems.append(item)

        QTimer().singleShot(100, self.repaint)

    def __balance_update_core(self):
        result = ThreadingResult()

        while True:
            try:
                for token in self.__tokenItems:
                    if not token.isMaster:
                        engine = token.engine()
                    else:
                        engine = payromasdk.MainProvider

                    self.__balanceUpdateThread.signal.resultSignal.emit(ThreadingResult(
                        is_valid=True,
                        params={
                            'token': token,
                            'balance': engine.balance_of(self.__engine.address())
                        }
                    ))

                continue

            except requests.exceptions.ConnectionError:
                result.message = translator("Unable to connect, make sure you are connected to the internet")

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
