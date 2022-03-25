from pcontroller import payromasdk
from pui import walletitem


class WalletItem(walletitem.UiForm):
    def __init__(self, parent):
        super(WalletItem, self).__init__(parent)

        self.setup()

        # Variables
        self.__engine = None

    def favorite_clicked(self, state: bool):
        self.__engine.set_favorite(state)

    def engine(self) -> payromasdk.engine.wallet.WalletEngine:
        return self.__engine

    def set_engine(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__engine = engine
        self.set_username(engine.username())
        self.set_address(engine.address().value())

        if engine.is_favorite():
            self.set_favorite(True)

        if engine.is_logged():
            self.set_status(True)
