from plibs import *
from pheader import *
from pcontroller import payromasdk, event
from pui import walletdetails


class WalletDetailsModel(walletdetails.UiForm, event.EventForm):
    def __init__(self, parent):
        super(WalletDetailsModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Variables
        self.__engine = None

    def hideEvent(self, a0: QHideEvent):
        super(WalletDetailsModel, self).hideEvent(a0)
        self.reset()
        self.set_data(self.__engine.address().value(), self.__engine.date_created())

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.reset()
        self.set_data(engine.address().value(), engine.date_created())
        self.__engine = engine

    @pyqtSlot()
    def back_clicked(self):
        event.walletTabChanged.notify(tab=Tab.WalletTab.TOKENS_LIST)

    @pyqtSlot()
    def private_key_clicked(self):
        if self.__engine.is_logged():
            event.authenticatorForward.notify(method=self.__authenticator_forward)
        else:
            event.loginForward.notify(method=self.__authenticator_forward)

    def __authenticator_forward(self, private_key: str):
        super(WalletDetailsModel, self).private_key_clicked()
        self.set_private_key(private_key)
        event.mainTabChanged.notify(tab=Tab.WALLET)
