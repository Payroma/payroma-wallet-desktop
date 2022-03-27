from plibs import *
from pheader import *
from pcontroller import globalmethods, translator, ThreadingResult, ThreadingArea
from pui import authenticator


class AuthenticatorModel(authenticator.UiForm):
    def __init__(self, parent):
        super(AuthenticatorModel, self).__init__(parent)

        self.setup()

        # Global Methods
        globalmethods.AuthenticatorModel._forward = self.forward
        globalmethods.AuthenticatorModel._getPrivateKey = self.get_private_key

        # Threading Methods
        self.__confirmThread = ThreadingArea(self.__confirm_clicked_core)
        self.__confirmThread.signal.resultSignal.connect(self.__confirm_clicked_ui)

        # Variables
        self.__isTyping = False
        self.__forwardTab = None
        self.__forwardTabRecordable = None
        self.__passwordValue = None
        self.__privateKeyValue = None

    def hideEvent(self, event: QHideEvent):
        super(AuthenticatorModel, self).hideEvent(event)
        if self.__confirmThread.isRunning():
            return

        self.reset()

    @pyqtSlot()
    def forgot_clicked(self):
        wallet_engine = globalmethods.WalletsListModel.currentWalletEngine()
        globalmethods.AuthenticatorSetupModel.setData(
            username=wallet_engine.username(),
            password=self.__passwordValue,
            pin_code=wallet_engine.pin_code(),
            address=wallet_engine.address().value()
        )
        globalmethods.MainModel.setCurrentTab(Tab.AUTHENTICATOR_SETUP, recordable=False)

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
            message=translator("The OTP code is wrong")
        )

        try:
            wallet_engine = globalmethods.WalletsListModel.currentWalletEngine()
            if not wallet_engine.is_logged():
                wallet_engine.login(self.__passwordValue, self.get_otp_code_text())

            self.__privateKeyValue = wallet_engine.private_key(self.get_otp_code_text())
            if len(self.__privateKeyValue) == 66:
                result.isValid = True

            if result.isValid:
                result.message = translator("OTP code has been confirmed successfully")

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__confirmThread.signal.resultSignal.emit(result)

    def __confirm_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            globalmethods.MainModel.setCurrentTab(
                self.__forwardTab, recordable=self.__forwardTabRecordable
            )

        result.show_message()
        self.confirm_completed()

    def forward(self, tab: str, recordable: bool = True, password: str = ''):
        self.__forwardTab = tab
        self.__forwardTabRecordable = recordable
        self.__passwordValue = password
        self.__privateKeyValue = ''
        globalmethods.MainModel.setCurrentTab(Tab.AUTHENTICATOR, recordable=False)

    def get_private_key(self) -> str:
        result = self.__privateKeyValue
        self.__passwordValue = None
        self.__privateKeyValue = ''
        return result
