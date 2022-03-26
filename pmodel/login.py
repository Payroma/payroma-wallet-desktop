from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, translator, ThreadingResult, ThreadingArea
from pui import login


class LoginModel(login.UiForm):
    def __init__(self, parent):
        super(LoginModel, self).__init__(parent)

        self.setup()

        # Global Methods
        globalmethods.LoginModel._forward = self.forward

        # Threading Methods
        self.__loginThread = ThreadingArea(self.__login_clicked_core)
        self.__loginThread.signal.resultSignal.connect(self.__login_clicked_ui)

        # Variables
        self.__isTyping = False
        self.__forwardTab = None

    def showEvent(self, event: QShowEvent):
        super(LoginModel, self).showEvent(event)
        wallet_engine = globalmethods.WalletsListModel.currentWalletEnine()
        self.reset()
        self.set_data(wallet_engine.username(), wallet_engine.address().value())

    @pyqtSlot()
    def skip_clicked(self):
        globalmethods.MainModel.setCurrentTab(Tab.WALLET)

    @pyqtSlot(str)
    def password_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__password_changed(text))

    def __password_changed(self, text: str):
        valid = False
        if text != self.get_password_text():
            return

        if text:
            if self.get_strength_text() in [
                SPInputmanager.StrengthState.good.text, SPInputmanager.StrengthState.excellent.text
            ]:
                valid = True

        self.__isTyping = False
        super(LoginModel, self).password_changed(text, valid)

    @pyqtSlot()
    def login_clicked(self):
        if self.__isTyping or self.__loginThread.isRunning():
            return

        super(LoginModel, self).login_clicked()
        self.__loginThread.start()

    def __login_clicked_core(self):
        result = ThreadingResult(
            message=translator("Wrong password, Please try again")
        )

        try:
            wallet_engine = globalmethods.WalletsListModel.currentWalletEnine()
            username = wallet_engine.username()
            password = self.get_password_text()
            pin_code = wallet_engine.pin_code()
            otp_code = pyotp.TOTP(payromasdk.tools.walletcreator.otp_hash(username, password, '')).now()

            if not payromasdk.tools.walletcreator.access(username, password, pin_code, otp_code):
                result.isValid = True

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__loginThread.signal.resultSignal.emit(result)

    def __login_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            globalmethods.MainModel.setCurrentTab(Tab.AUTHENTICATOR, recordable=False)
        else:
            result.show_message()

        self.login_completed()

    def forward(self, tab: str):
        self.__forwardTab = tab
        wallet_engine = globalmethods.WalletsListModel.currentWalletEnine()

        if wallet_engine.is_logged():
            globalmethods.MainModel.setCurrentTab(tab)
        else:
            globalmethods.MainModel.setCurrentTab(Tab.LOGIN, recordable=False)
