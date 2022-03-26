from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, translator, ThreadingResult, ThreadingArea
from pui import authenticatorverification


class AuthenticatorVerificationModel(authenticatorverification.UiForm):
    def __init__(self, parent):
        super(AuthenticatorVerificationModel, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__verifyThread = ThreadingArea(self.__verify_clicked_core)
        self.__verifyThread.signal.resultSignal.connect(self.__verify_clicked_ui)

        # Variables
        self.__isTyping = False

    def showEvent(self, event: QShowEvent):
        super(AuthenticatorVerificationModel, self).showEvent(event)
        username, _, _, address = globalmethods.AuthenticatorSetupModel.getData()
        self.reset()
        self.set_data(username, address)

    @pyqtSlot()
    def back_clicked(self):
        globalmethods.AuthenticatorSetupModel.setCurrentTab(Tab.AuthenticatorSetupTab.DOWNLOAD)

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
            message=translator("This wallet's PIN code doesn't match"),
            params={
                'username': '',
                'key': ''
            }
        )

        try:
            username, password, pin_code, address = globalmethods.AuthenticatorSetupModel.getData()
            otp_hash = payromasdk.tools.walletcreator.otp_hash(username, password, self.get_pin_code_text())

            if isinstance(pin_code, str):
                result.isValid = (self.get_pin_code_text() == pin_code)
            elif isinstance(pin_code, bytes):
                otp_code = pyotp.TOTP(otp_hash).now()
                try:
                    address_, _, pin_code_ = payromasdk.tools.walletcreator.access(
                        username, password, pin_code, otp_code
                    )
                    if address_.value() == address and pin_code_ == pin_code:
                        result.isValid = True
                except TypeError:
                    pass

            if result.isValid:
                result.message = translator("PIN code has been confirmed successfully")
                result.params['username'] = username
                result.params['key'] = otp_hash

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__verifyThread.signal.resultSignal.emit(result)

    def __verify_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            globalmethods.AuthenticatorScanModel.setData(
                username=result.params['username'], key=result.params['key']
            )
            globalmethods.AuthenticatorFinishedModel.setData(key=result.params['key'])
            globalmethods.AuthenticatorSetupModel.setCurrentTab(Tab.AuthenticatorSetupTab.SCAN)

        result.show_message()
        self.verify_completed()
