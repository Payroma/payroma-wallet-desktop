from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import addnetwork


class AddNetworkModel(addnetwork.UiForm):
    def __init__(self, parent):
        super(AddNetworkModel, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__addNetworkThread = ThreadingArea(self.__add_clicked_core)
        self.__addNetworkThread.signal.resultSignal.connect(self.__add_clicked_ui)

        # Variables
        self.__isTyping = False

    def showEvent(self, a0: QShowEvent):
        super(AddNetworkModel, self).showEvent(a0)
        if self.__addNetworkThread.isRunning():
            return

        self.reset()

    @pyqtSlot(str)
    def name_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__name_changed(text))

    def __name_changed(self, text: str):
        valid = False
        if text != self.get_name_text():
            return

        if text:
            is_exists = any(text == i.name for i in payromasdk.engine.network.get_all())
            if not is_exists:
                valid = True

        self.__isTyping = False
        super(AddNetworkModel, self).name_changed(text, valid)

    @pyqtSlot(str)
    def rpc_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__rpc_changed(text))

    def __rpc_changed(self, text: str):
        valid = False
        if text != self.get_rpc_text():
            return

        if len(text) > 10:
            if self.get_chain_id_text():
                self.__chain_id_changed(self.get_chain_id_text())

            provider = web3.Web3(web3.Web3.HTTPProvider(text))
            if provider.isConnected():
                valid = True

        self.__isTyping = False
        super(AddNetworkModel, self).rpc_changed(text, valid)

    @pyqtSlot(str)
    def symbol_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__symbol_changed(text))

    def __symbol_changed(self, text: str):
        valid = False
        if text != self.get_symbol_text():
            return

        if len(text) >= 2:
            valid = True

        self.__isTyping = False
        super(AddNetworkModel, self).symbol_changed(text, valid)

    @pyqtSlot(str)
    def chain_id_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__chain_id_changed(text))

    def __chain_id_changed(self, text: str):
        valid = False
        if text != self.get_chain_id_text():
            return

        if text and self.get_rpc_text():
            provider = web3.Web3(web3.Web3.HTTPProvider(self.get_rpc_text()))
            if provider.isConnected() and provider.eth.chain_id == int(self.get_chain_id_text()):
                valid = True

        self.__isTyping = False
        super(AddNetworkModel, self).chain_id_changed(text, valid)

    @pyqtSlot(str)
    def explorer_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__explorer_changed(text))

    def __explorer_changed(self, text: str):
        valid = False
        if text != self.get_explorer_text():
            return

        if len(text) > 10:
            valid = True

        self.__isTyping = False
        super(AddNetworkModel, self).explorer_changed(text, valid)

    @pyqtSlot()
    def add_clicked(self):
        if self.__isTyping or self.__addNetworkThread.isRunning():
            return

        super(AddNetworkModel, self).add_clicked()
        self.__addNetworkThread.start()

    def __add_clicked_core(self):
        result = ThreadingResult(
            message=translator("Failed to add network, Please try again")
        )

        try:
            result.isValid = payromasdk.engine.network.add_new(
                rpc=self.get_rpc_text(),
                name=self.get_name_text(),
                chain_id=int(self.get_chain_id_text()),
                symbol=self.get_symbol_text(),
                explorer=self.get_explorer_text()
            )
            if result.isValid:
                result.message = translator("Network added successfully")

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__addNetworkThread.signal.resultSignal.emit(result)

    def __add_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            event.networkEdited.notify()
            event.mainTabChanged.notify(tab=Tab.NETWORKS_LIST)

        result.show_message()
        self.add_completed()
