from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import wallet, styles, images
from pmodel.tokenslist import TokensListModel
from pmodel.walletdetails import WalletDetailsModel
from pmodel.addtoken import AddTokenModel


class WalletModel(wallet.UiForm, event.EventForm):
    def __init__(self, parent):
        super(WalletModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Tabs
        self.add_tab(TokensListModel(self), Tab.WalletTab.TOKENS_LIST)
        self.add_tab(WalletDetailsModel(self), Tab.WalletTab.WALLET_DETAILS)
        self.add_tab(AddTokenModel(self), Tab.WalletTab.ADD_TOKEN)

        # Threading Methods
        self.__removeThread = ThreadingArea(self.__remove_clicked_core)
        self.__removeThread.signal.resultSignal.connect(self.__remove_clicked_ui)

        # Variables
        self.__engine = None

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.reset()
        self.set_data(engine.username(), engine.address().value())
        self.__engine = engine

    def wallet_tab_changed_event(self, tab: str):
        self.set_current_tab(tab)

    @pyqtSlot()
    def deposit_clicked(self):
        event.mainTabChanged.notify(tab=Tab.DEPOSIT)

    @pyqtSlot()
    def withdraw_clicked(self):
        event.mainTabChanged.notify(tab=Tab.WITHDRAW, recordable=False)

    @pyqtSlot()
    def stake_clicked(self):
        event.mainTabChanged.notify(tab=Tab.STAKE_LIST)

    @pyqtSlot()
    def history_clicked(self):
        event.mainTabChanged.notify(tab=Tab.HISTORY_LIST)

    @pyqtSlot()
    def swap_clicked(self):
        event.mainTabChanged.notify(tab=Tab.SWAP)

    @pyqtSlot()
    def details_clicked(self):
        super(WalletModel, self).details_clicked()
        event.walletTabChanged.notify(tab=Tab.WalletTab.WALLET_DETAILS)

    @pyqtSlot()
    def add_token_clicked(self):
        super(WalletModel, self).add_token_clicked()
        event.walletTabChanged.notify(tab=Tab.WalletTab.ADD_TOKEN)

    def explorer_clicked(self):
        super(WalletModel, self).explorer_clicked()
        self.__engine.address().explorer_view()

    def remove_clicked(self):
        super(WalletModel, self).remove_clicked()
        if self.__removeThread.isRunning():
            return

        message1 = translator("This wallet will be removed from the app.")
        message2 = translator(
            "Please make sure your wallet's username, password and PIN code are saved before continuing."
        )
        message3 = translator("You can import it again by adding a new wallet or importing the backup file.")
        messagebox = SPGraphics.MessageBoxConfirm(
            parent=self,
            text='%s\n\n%s\n\n%s' % (message1, message2, message3),
            icon=images.data.icons.warning41,
            color=styles.data.colors.font.name(),
            accept="Remove",
            window_size=QSize(401, 231)
        )
        messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
        messagebox.frame.layout().setSpacing(11)
        messagebox.exec_()
        if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
            self.__removeThread.start()

    def __remove_clicked_core(self):
        result = ThreadingResult(
            message=translator("Failed to remove wallet, Please try again")
        )

        try:
            result.isValid = payromasdk.engine.wallet.remove(wallet_interface=self.__engine.interface)
            if result.isValid:
                result.message = translator("Wallet removed successfully")

        except Exception as err:
            result.error(str(err))

        self.__removeThread.signal.resultSignal.emit(result)

    @staticmethod
    def __remove_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.walletEdited.notify()
            event.mainTabChanged.notify(tab=Tab.WALLETS_LIST)

        result.show_message()

    def logout_clicked(self):
        super(WalletModel, self).logout_clicked()
        self.__engine.logout()
        event.walletEdited.notify()
        event.mainTabChanged.notify(tab=Tab.WALLETS_LIST)
