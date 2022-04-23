from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import login


class LoginModel(login.UiForm, event.EventForm):
    def __init__(self, parent):
        super(LoginModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__loginThread = ThreadingArea(self.__login_clicked_core)
        self.__loginThread.signal.resultSignal.connect(self.__login_clicked_ui)

        # Variables
        self.__isTyping = False
        self.__currentWalletEngine = None
        self.__forward = None

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.reset()
        self.set_data(engine.username(), engine.address().value())
        self.__currentWalletEngine = engine

    def login_forward_event(self, method):
        self.__forward = method
        if self.__currentWalletEngine.is_logged():
            self.__forward('')
        else:
            event.mainTabChanged.notify(tab=Tab.LOGIN, recordable=False)

    @pyqtSlot()
    def skip_clicked(self):
        event.mainTabChanged.notify(tab=Tab.WALLET)

    @pyqtSlot(str)
    def password_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1500, lambda: self.__password_changed(text))

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
            username = self.__currentWalletEngine.username()
            password = self.get_password_text()
            pin_code = self.__currentWalletEngine.pin_code()
            otp_code = pyotp.TOTP(payromasdk.tools.walletcreator.otp_hash(username, password, '')).now()

            if not payromasdk.tools.walletcreator.access(username, password, pin_code, otp_code):
                result.isValid = True

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__loginThread.signal.resultSignal.emit(result)

    def __login_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            event.authenticatorForward.notify(method=self.__forward, password=self.get_password_text())
        else:
            result.show_message()

        self.login_completed()
