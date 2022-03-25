from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, translator, ThreadingResult, ThreadingArea
from pui import networkitem, fonts, styles, images


class NetworkItem(networkitem.UiForm):
    def __init__(self, parent):
        super(NetworkItem, self).__init__(parent)

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
            text=translator("Are you sure you want to remove this network?"),
            icon=images.data.icons.warning41,
            font_size=fonts.data.size.title,
            color=styles.data.colors.font.name(),
            accept="Remove"
        )
        messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
        messagebox.frame.layout().setSpacing(11)
        messagebox.exec_()
        if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
            self.__removeThread.start()

    def __remove_clicked_core(self):
        result = ThreadingResult(
            message=translator("Failed to remove network, Please try again")
        )

        try:
            result.isValid = payromasdk.engine.network.remove(self.__interface)
            if result.isValid:
                result.message = translator("Network removed successfully")

        except Exception as err:
            result.error(str(err))

        self.__removeThread.signal.resultSignal.emit(result)

    @staticmethod
    def __remove_clicked_ui(result: ThreadingResult):
        globalmethods.NetworksListModel.refresh()
        result.show_message()

    def interface(self) -> payromasdk.tools.interface.Network:
        return self.__interface

    def set_interface(self, interface: payromasdk.tools.interface.Network):
        self.__interface = interface
        self.set_name(interface.name)
        self.set_symbol(interface.symbol)
