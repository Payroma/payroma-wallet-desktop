from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, ThreadingArea, translator
from pui import authenticatorscan


class AuthenticatorScanModel(authenticatorscan.UiForm):
    def __init__(self, parent):
        super(AuthenticatorScanModel, self).__init__(parent)

        self.setup()

        # Global Methods
        globalmethods.AuthenticatorScanModel._setData = self.set_data

        # Threading Methods
        self.__confirmThread = ThreadingArea(self.__confirm_clicked_core)
        self.__confirmThread.signal.dictSignal.connect(self.__confirm_clicked_ui)

        # Variables
        self.__isTyping = False
        self.__totp = None

    def hideEvent(self, event: QHideEvent):
        super(AuthenticatorScanModel, self).hideEvent(event)
        self.reset()

    @pyqtSlot()
    def back_clicked(self):
        globalmethods.AuthenticatorSetupModel.setCurrentTab(Tab.AuthenticatorSetupTab.VERIFICATION)

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
        result = {
            'status': False,
            'error': None,
            'message': translator("The OTP code is wrong"),
            'params': {}
        }

        try:
            result['status'] = self.__totp.verify(self.get_otp_code_text())
            if result['status']:
                result['message'] = translator("OTP code has been confirmed successfully")
                self.__add_new_wallet()

        except Exception as err:
            result['error'] = "{}: {}".format(translator("Failed"), str(err))

        time.sleep(3)
        self.__confirmThread.signal.dictSignal.emit(result)

    def __confirm_clicked_ui(self, result: dict):
        if result['status']:
            globalmethods.AuthenticatorSetupModel.setCurrentTab(Tab.AuthenticatorSetupTab.FINISHED)
            QApplication.quickNotification.successfully(result['message'])
        elif result['error']:
            QApplication.quickNotification.failed(result['error'])
        else:
            QApplication.quickNotification.warning(result['message'])

        self.confirm_completed()

    def set_data(self, username: str, key: str):
        super(AuthenticatorScanModel, self).set_data(username, key)
        self.__totp = pyotp.TOTP(key)

    def __add_new_wallet(self):
        username, password, pin_code, _ = globalmethods.AuthenticatorSetupModel.getData()
        is_exists = any(username == i.username for i in payromasdk.engine.wallet.get_all())
        if not is_exists:
            payromasdk.engine.wallet.add_new(
                username=username,
                password=password,
                pin_code=pin_code,
                otp_code=self.get_otp_code_text()
            )
