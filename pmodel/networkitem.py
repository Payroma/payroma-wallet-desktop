from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, ThreadingArea, translator
from pui import networkitem, fonts, styles, images


class NetworkItem(networkitem.UiForm):
    def __init__(self, parent):
        super(NetworkItem, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__removeThread = ThreadingArea(self.__remove_clicked_core)
        self.__removeThread.signal.dictSignal.connect(self.__remove_clicked_ui)

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
        result = {
            'status': False,
            'message': translator("Failed to remove network, Please try again")
        }

        try:
            result['status'] = payromasdk.engine.network.remove(self.__interface)
            if result['status']:
                result['message'] = translator("Network removed successfully")

        except Exception as err:
            result['message'] = "{}: {}".format(translator("Failed"), str(err))

        self.__removeThread.signal.dictSignal.emit(result)

    @staticmethod
    def __remove_clicked_ui(result: dict):
        globalmethods.NetworksListModel.refresh()
        if result['status']:
            QApplication.quickNotification.successfully(result['message'])
        else:
            QApplication.quickNotification.failed(result['message'])

    def interface(self) -> payromasdk.tools.interface.Network:
        return self.__interface

    def set_interface(self, interface: payromasdk.tools.interface.Network):
        self.__interface = interface
