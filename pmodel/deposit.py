from plibs import *
from pheader import *
from pcontroller import payromasdk, event
from pui import deposit


class DepositModel(deposit.UiForm, event.EventForm):
    def __init__(self, parent):
        super(DepositModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Variables
        self.__currentWalletEngine = None

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.reset()
        self.set_data(engine.address().value(), payromasdk.MainProvider.interface.name)
        self.__currentWalletEngine = engine

    def network_changed_event(self, name: str, status: bool):
        self.reset()

        address = ''
        if self.__currentWalletEngine:
            address = self.__currentWalletEngine.address().value()

        self.set_data(address, name)

    @pyqtSlot()
    def network_clicked(self):
        event.mainTabChanged.notify(tab=Tab.NETWORKS_LIST)
