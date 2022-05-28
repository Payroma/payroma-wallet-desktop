from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import authenticator


class AuthenticatorModel(authenticator.UiForm, event.EventForm):
    def __init__(self, parent):
        super(AuthenticatorModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__confirmThread = ThreadingArea(self.__confirm_clicked_core)
        self.__confirmThread.signal.resultSignal.connect(self.__confirm_clicked_ui)
        self.__confirmThread.finished.connect(self.confirm_completed)

        # Variables
        self.__isTyping = False
        self.__currentWalletEngine = None
        self.__forward = None
        self.__passwordValue = None

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.reset()
        self.__currentWalletEngine = engine

    def authenticator_forward_event(self, method, password: str = ''):
        self.__forward = method
        self.__passwordValue = password
        event.mainTabChanged.notify(tab=Tab.AUTHENTICATOR, recordable=False)

    @pyqtSlot()
    def forgot_clicked(self):
        event.mainTabChanged.notify(tab=Tab.AUTHENTICATOR_SETUP, recordable=False)

    @pyqtSlot(str)
    def otp_code_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__otp_code_changed(text))

    def __otp_code_changed(self, text: str):
        valid = False
        if text != self.get_otp_code_text():
            return

        if len(text) == 6:
            valid = True

        self.__isTyping = False
        super(AuthenticatorModel, self).otp_code_changed(text, valid)

    @pyqtSlot()
    def confirm_clicked(self):
        if self.__isTyping or self.__confirmThread.isRunning():
            return

        super(AuthenticatorModel, self).confirm_clicked()
        self.__confirmThread.start()

    def __confirm_clicked_core(self):
        result = ThreadingResult(
            message=translator("The OTP code is wrong!"),
            params={
                'privateKey': ''
            }
        )

        try:
            if not self.__currentWalletEngine.is_logged():
                self.__currentWalletEngine.login(self.__passwordValue, self.get_otp_code_text())

            private_key = self.__currentWalletEngine.private_key(self.get_otp_code_text())
            if private_key and len(private_key) == 66:
                result.isValid = True

            if result.isValid:
                result.message = translator("OTP code has been confirmed successfully.")
                result.params['privateKey'] = private_key

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__confirmThread.signal.resultSignal.emit(result)

    def __confirm_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            self.__forward(result.params['privateKey'])
            event.walletEdited.notify()

        result.show_message()
