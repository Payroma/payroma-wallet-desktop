from pcontroller import payromasdk, event
from pui import historylist
from pmodel import historyitem


class HistoryListModel(historylist.UiForm, event.EventForm):
    def __init__(self, parent):
        super(HistoryListModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Variables
        self.__currentWalletEngine = None

    def transaction_history_edited_event(self):
        self.refresh()

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine
        self.refresh()

    def network_changed_event(self, name: str, status: bool):
        self.refresh()

    def refresh(self):
        if not self.__currentWalletEngine:
            return

        self.reset()

        for transaction in self.__currentWalletEngine.transactions(latest=20):
            item = historyitem.HistoryItem(self)
            item.set_interface(transaction)

            self.add_item(item)
