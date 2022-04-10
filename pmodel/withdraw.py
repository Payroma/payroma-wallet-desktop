from plibs import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import withdraw, fonts, styles, Size
from pmodel.addressesbooklist import AddressesBookListModel
from pmodel.addamount import AddAmountModel


class WithdrawModel(withdraw.UiForm, event.EventForm):
    def __init__(self, parent):
        super(WithdrawModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Tabs
        self.add_tab(AddressesBookListModel(self), '')
        self.add_tab(AddAmountModel(self), '')

        # Threading Methods
        self.__addAddressBookThread = ThreadingArea(self.__add_new_clicked_core)
        self.__addAddressBookThread.signal.resultSignal.connect(self.__add_new_clicked_ui)

        # Variables
        self.__nickname = None

    def hideEvent(self, a0: QHideEvent):
        super(WithdrawModel, self).hideEvent(a0)
        self.reset()

    def withdraw_address_changed_event(self, address: str):
        self.set_address(address)

    @pyqtSlot(str)
    def address_changed(self, text: str):
        QTimer().singleShot(1000, lambda: self.__address_changed(text))

    def __address_changed(self, text: str):
        valid = False
        if text != self.get_address_text():
            return

        addable = False
        if len(text) == 42:
            valid = True
            is_exists = any(text == i.address.value() for i in payromasdk.engine.addressbook.get_all())
            if not is_exists:
                addable = True

        event.withdrawAddressChanged.notify(address=text)
        super(WithdrawModel, self).address_changed(text, valid, addable)

    def add_new_clicked(self):
        messagebox = SPGraphics.MessageBoxPassword(
            parent=self,
            text=translator("Please enter a nickname for this wallet"),
            font_size=fonts.data.size.title,
            color=styles.data.colors.font.name(),
            window_size=Size.messageBox
        )
        messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
        messagebox.labelMessage.setAlignment(Qt.AlignCenter)
        messagebox.lineEdit.setPlaceholderText(translator("Nickname"))
        messagebox.lineEdit.setEchoMode(QLineEdit.Normal)
        messagebox.pushButtonEye.hide()
        messagebox.strengthBar.hide()
        messagebox.exec_()

        if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
            self.__nickname = messagebox.password
            self.__addAddressBookThread.start()

    def __add_new_clicked_core(self):
        result = ThreadingResult(
            message=translator("Failed to add new address, Please try again")
        )

        try:
            result.isValid = payromasdk.engine.addressbook.add_new(
                username=self.__nickname,
                address=payromasdk.tools.interface.Address(self.get_address_text())
            )

            if result.isValid:
                result.message = translator("Address added successfully")

        except Exception as err:
            result.error(str(err))

        self.__addAddressBookThread.signal.resultSignal.emit(result)

    @staticmethod
    def __add_new_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.addressBookEdited.notify()

        result.show_message()
