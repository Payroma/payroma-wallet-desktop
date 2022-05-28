from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import addtoken


class AddTokenModel(addtoken.UiForm, event.EventForm):
    def __init__(self, parent):
        super(AddTokenModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__addressThread = ThreadingArea(self.__address_changed_core)
        self.__addressThread.signal.resultSignal.connect(self.__address_changed_ui)

        self.__addTokenThread = ThreadingArea(self.__add_clicked_core)
        self.__addTokenThread.signal.resultSignal.connect(self.__add_clicked_ui)
        self.__addTokenThread.finished.connect(self.add_completed)

        # Variables
        self.__isTyping = False
        self.__currentWalletEngine = None

    def showEvent(self, a0: QShowEvent):
        super(AddTokenModel, self).showEvent(a0)
        if self.__addTokenThread.isRunning():
            return

        self.reset()

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine

    @pyqtSlot()
    def back_clicked(self):
        event.walletTabChanged.notify(tab=Tab.WalletTab.TOKENS_LIST)

    @pyqtSlot(str)
    def address_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__address_changed(text))

    def __address_changed(self, text: str):
        valid = False
        if text != self.get_address_text():
            return

        if len(text) == 42:
            self.__addressThread.start()
            valid = True

        self.__isTyping = False
        super(AddTokenModel, self).address_changed(text, valid)

    def __address_changed_core(self):
        result = ThreadingResult(
            message=translator("This contract is not available!"),
            params={
                'symbol': None,
                'decimals': None
            }
        )

        try:
            contract = payromasdk.tools.interface.Address(self.get_address_text())
            engine = payromasdk.engine.token.TokenEngine(
                payromasdk.tools.interface.Token(contract=contract, symbol='', decimals=0)
            )
            try:
                result.params['symbol'] = engine.symbol()
                result.params['decimals'] = str(engine.decimals())
                result.isValid = True
            except web3.exceptions.BadFunctionCallOutput:
                pass

            if result.isValid:
                result.message = translator("Contract has been detected.")

        except Exception as err:
            result.error(str(err))

        self.__addressThread.signal.resultSignal.emit(result)

    def __address_changed_ui(self, result: ThreadingResult):
        if result.isValid:
            self.set_data(result.params['symbol'], result.params['decimals'])

        result.show_message()

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
        super(AddTokenModel, self).symbol_changed(text, valid)

    @pyqtSlot(str)
    def decimals_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__decimals_changed(text))

    def __decimals_changed(self, text: str):
        valid = False
        if text != self.get_decimals_text():
            return

        if text:
            valid = True

        self.__isTyping = False
        super(AddTokenModel, self).decimals_changed(text, valid)

    @pyqtSlot()
    def add_clicked(self):
        if self.__isTyping or self.__addTokenThread.isRunning():
            return

        super(AddTokenModel, self).add_clicked()
        self.__addTokenThread.start()

    def __add_clicked_core(self):
        result = ThreadingResult(
            message=translator("Failed to add token, Please try again.")
        )

        try:
            contract = payromasdk.tools.interface.Address(self.get_address_text())
            is_exists = any(
                contract.value() == i.contract.value() for i in self.__currentWalletEngine.tokens()
            )
            if is_exists:
                result.message = translator("Token already exists!")
            else:
                result.isValid = self.__currentWalletEngine.add_token(
                    payromasdk.tools.interface.Token(
                        contract=contract,
                        symbol=self.get_symbol_text(),
                        decimals=int(self.get_decimals_text())
                    )
                )

            if result.isValid:
                result.message = translator("Token added successfully.")

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__addTokenThread.signal.resultSignal.emit(result)

    @staticmethod
    def __add_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.tokenEdited.notify()
            event.walletTabChanged.notify(tab=Tab.WalletTab.TOKENS_LIST)

        result.show_message()
