from plibs import *
from pheader import *
from pcontroller import payromasdk, event
from pui import walletslist
from pmodel import walletitem


class WalletsListModel(walletslist.UiForm, event.EventForm):
    def __init__(self, parent):
        super(WalletsListModel, self).__init__(parent)

        self.setup()
        self.events_listening()

    def app_started_event(self):
        self.refresh()

    def wallet_edited_event(self):
        self.refresh()

    @pyqtSlot()
    def add_new_clicked(self):
        event.mainTabChanged.notify(tab=Tab.ADD_WALLET)

    @pyqtSlot(QListWidgetItem)
    def item_clicked(self, item: QListWidgetItem):
        widget = super(WalletsListModel, self).item_clicked(item)
        event.walletChanged.notify(engine=widget.engine())
        event.loginForward.notify(method=self.__authenticator_forward)

    def refresh(self):
        self.reset()

        for wallet in payromasdk.engine.wallet.get_all():
            # Use wallet engine that created before or create a new one
            try:
                wallet = payromasdk.engine.wallet.recentWalletsEngine[wallet.addressID]
            except KeyError:
                wallet = payromasdk.engine.wallet.WalletEngine(wallet_interface=wallet)

            item = walletitem.WalletItem(self)
            item.set_engine(wallet)

            self.add_item(item)

    @staticmethod
    def __authenticator_forward(private_key: str):
        event.mainTabChanged.notify(tab=Tab.WALLET)
