from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk
from pui import walletslist
from pmodel import walletitem


class WalletsListModel(walletslist.UiForm):
    def __init__(self, parent):
        super(WalletsListModel, self).__init__(parent)

        self.setup()

        # Global Methods
        globalmethods.WalletsListModel._currentWalletEngine = self.current_wallet_engine

        # Variables
        self.__currentWalletEngine = None

    def showEvent(self, event: QShowEvent):
        super(WalletsListModel, self).showEvent(event)
        self.refresh()

    @pyqtSlot()
    def add_new_clicked(self):
        globalmethods.MainModel.setCurrentTab(Tab.ADD_WALLET)

    @pyqtSlot(QListWidgetItem)
    def item_clicked(self, item: QListWidgetItem):
        widget = super(WalletsListModel, self).item_clicked(item)
        self.__currentWalletEngine = widget.engine()
        globalmethods.LoginModel.forward(Tab.WALLET)

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

    def current_wallet_engine(self) -> payromasdk.engine.wallet.WalletEngine:
        return self.__currentWalletEngine
