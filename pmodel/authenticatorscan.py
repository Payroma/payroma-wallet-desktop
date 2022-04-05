from plibs import *
from pheader import *
from pcontroller import event, translator, ThreadingResult, ThreadingArea
from pui import authenticatorscan


class AuthenticatorScanModel(authenticatorscan.UiForm, event.EventForm):
    def __init__(self, parent):
        super(AuthenticatorScanModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__confirmThread = ThreadingArea(self.__confirm_clicked_core)
        self.__confirmThread.signal.resultSignal.connect(self.__confirm_clicked_ui)

        # Variables
        self.__isTyping = False
        self.__totp = None

    def authenticator_setup_verified_event(self, username: str, otp_hash: str):
        self.reset()
        self.set_data(username, otp_hash)
        self.__totp = pyotp.TOTP(otp_hash)

    @pyqtSlot()
    def back_clicked(self):
        event.authenticatorSetupTabChanged.notify(tab=Tab.AuthenticatorSetupTab.VERIFICATION)

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
        super(AuthenticatorScanModel, self).otp_code_changed(text, valid)

    @pyqtSlot()
    def confirm_clicked(self):
        if self.__isTyping or self.__confirmThread.isRunning():
            return

        super(AuthenticatorScanModel, self).confirm_clicked()
        self.__confirmThread.start()

    def __confirm_clicked_core(self):
        result = ThreadingResult(
            message=translator("The OTP code is wrong")
        )

        try:
            result.isValid = self.__totp.verify(self.get_otp_code_text())
            if result.isValid:
                result.message = translator("Your OTP code has been confirmed successfully")

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__confirmThread.signal.resultSignal.emit(result)

    def __confirm_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            event.authenticatorSetupTabChanged.notify(tab=Tab.AuthenticatorSetupTab.FINISHED)

        result.show_message()
        self.confirm_completed()
