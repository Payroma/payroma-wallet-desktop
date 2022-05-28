from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import authenticatorverification


class AuthenticatorVerificationModel(authenticatorverification.UiForm, event.EventForm):
    def __init__(self, parent):
        super(AuthenticatorVerificationModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__verifyThread = ThreadingArea(self.__verify_clicked_core)
        self.__verifyThread.signal.resultSignal.connect(self.__verify_clicked_ui)
        self.__verifyThread.finished.connect(self.verify_completed)

        # Variables
        self.__isTyping = False
        self.__currentWalletEngine = None

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.reset()
        self.set_data(engine.username(), engine.address().value())
        self.__currentWalletEngine = engine

    @pyqtSlot()
    def back_clicked(self):
        event.authenticatorSetupTabChanged.notify(tab=Tab.AuthenticatorSetupTab.DOWNLOAD)

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
        super(AuthenticatorVerificationModel, self).password_changed(text, valid)

    @pyqtSlot(str)
    def pin_code_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__pin_code_changed(text))

    def __pin_code_changed(self, text: str):
        valid = False
        if text != self.get_pin_code_text():
            return

        if len(text) == 6:
            valid = True

        self.__isTyping = False
        super(AuthenticatorVerificationModel, self).pin_code_changed(text, valid)

    @pyqtSlot()
    def verify_clicked(self):
        if self.__isTyping or self.__verifyThread.isRunning():
            return

        super(AuthenticatorVerificationModel, self).verify_clicked()
        self.__verifyThread.start()

    def __verify_clicked_core(self):
        result = ThreadingResult(
            message=translator("Password or PIN code doesn't match!"),
            params={
                'username': '',
                'OTPHash': ''
            }
        )

        try:
            otp_hash = payromasdk.tools.walletcreator.otp_hash(
                self.__currentWalletEngine.username(), self.get_password_text(), self.get_pin_code_text()
            )
            otp_code = pyotp.TOTP(otp_hash)

            if self.__currentWalletEngine.login(
                password=self.get_password_text(),
                otp_code=otp_code.now()
            ):
                self.__currentWalletEngine.logout()
                result.isValid = True

            if result.isValid:
                result.message = translator("Let's scan and confirm your OTP code")
                result.params['username'] = self.__currentWalletEngine.username()
                result.params['OTPHash'] = otp_hash

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__verifyThread.signal.resultSignal.emit(result)

    @staticmethod
    def __verify_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.authenticatorSetupVerified.notify(
                username=result.params['username'], otp_hash=result.params['OTPHash']
            )
            event.authenticatorSetupTabChanged.notify(tab=Tab.AuthenticatorSetupTab.SCAN)

        result.show_message()
