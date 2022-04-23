from plibs import *
from pcontroller import payromasdk, event
from pui import addressesbooklist
from pmodel import addressbookitem


class AddressesBookListModel(addressesbooklist.UiForm, event.EventForm):
    def __init__(self, parent):
        super(AddressesBookListModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Variables
        self.__currentWalletEngine = None

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine
        self.refresh()

    def address_book_edited_event(self):
        self.refresh()

    def withdraw_address_changed_event(self, address: str):
        self.search(address)

    @pyqtSlot(QListWidgetItem)
    def item_clicked(self, item: QListWidgetItem):
        widget = super(AddressesBookListModel, self).item_clicked(item)
        event.withdrawAddressChanged.notify(address=widget.interface().address.value())

    def refresh(self):
        self.reset()

        for wallet in payromasdk.engine.addressbook.get_all():
            if wallet.address.value() == self.__currentWalletEngine.address().value():
                # Skip current wallet if recorded
                continue

            item = addressbookitem.AddressBookItem(self)
            item.set_interface(wallet)

            self.add_item(item)

        QTimer().singleShot(100, self.repaint)
