from plibs import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import addressbookitem, fonts, styles, images, Size


class AddressBookItem(addressbookitem.UiForm):
    def __init__(self, parent):
        super(AddressBookItem, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__removeThread = ThreadingArea(self.__remove_clicked_core)
        self.__removeThread.signal.resultSignal.connect(self.__remove_clicked_ui)

        # Variables
        self.__interface = None

    def remove_clicked(self):
        if self.__removeThread.isRunning():
            return

        messagebox = SPGraphics.MessageBoxConfirm(
            parent=self,
            text=translator("Are you sure you want to remove this address?"),
            icon=images.data.icons.warning41,
            font_size=fonts.data.size.title,
            color=styles.data.colors.font.name(),
            accept="Remove",
            window_size=Size.messageBox
        )
        messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
        messagebox.frame.layout().setSpacing(11)
        messagebox.exec_()

        if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
            self.__removeThread.start()

    def __remove_clicked_core(self):
        result = ThreadingResult(
            message=translator("Failed to remove address, Please try again.")
        )

        try:
            result.isValid = payromasdk.engine.addressbook.remove(self.__interface)
            if result.isValid:
                result.message = translator("Address removed successfully.")

        except Exception as err:
            result.error(str(err))

        self.__removeThread.signal.resultSignal.emit(result)

    @staticmethod
    def __remove_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.addressBookEdited.notify()

        result.show_message()

    def interface(self) -> payromasdk.tools.interface.AddressBook:
        return self.__interface

    def set_interface(self, interface: payromasdk.tools.interface.AddressBook):
        self.__interface = interface
        self.set_username(interface.username)
        self.set_address(interface.address.value())
