from plibs import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import tokenitem, fonts, styles, images, Size


class TokenItem(tokenitem.UiForm):
    def __init__(self, parent):
        super(TokenItem, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__removeThread = ThreadingArea(self.__remove_clicked_core)
        self.__removeThread.signal.resultSignal.connect(self.__remove_clicked_ui)

        # Variables
        self.__tokenEngine = None
        self.__walletEngine = None
        self.isMaster = False

    def remove_clicked(self):
        if self.__removeThread.isRunning():
            return

        messagebox = SPGraphics.MessageBoxConfirm(
            parent=self,
            text=translator("Are you sure you want to remove this token?"),
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
            message=translator("Failed to remove token, Please try again.")
        )

        try:
            result.isValid = self.__walletEngine.remove_token(self.__tokenEngine.interface)
            if result.isValid:
                result.message = translator("Token removed successfully.")

        except Exception as err:
            result.error(str(err))

        self.__removeThread.signal.resultSignal.emit(result)

    @staticmethod
    def __remove_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.tokenEdited.notify()

        result.show_message()

    def explorer_clicked(self):
        self.__tokenEngine.interface.contract.explorer_view()

    def set_master(self):
        super(TokenItem, self).set_master()
        self.isMaster = True
        self.__tokenEngine = payromasdk.MainProvider
        self.set_name(self.__tokenEngine.interface.symbol)
        self.set_symbol(self.__tokenEngine.interface.symbol)

    def engine(self) -> payromasdk.engine.token.TokenEngine:
        return self.__tokenEngine

    def set_engine(
            self, token_engine: payromasdk.engine.token.TokenEngine,
            wallet_engine: payromasdk.engine.wallet.WalletEngine
    ):
        self.__tokenEngine = token_engine
        self.__walletEngine = wallet_engine
        self.set_name(token_engine.interface.symbol)
        self.set_symbol(token_engine.interface.symbol)
