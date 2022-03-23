from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, ThreadingArea, translator
from pui import authenticatorverification


class AuthenticatorVerificationModel(authenticatorverification.UiForm):
    def __init__(self, parent):
        super(AuthenticatorVerificationModel, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__verifyThread = ThreadingArea(self.__verify_clicked_core)
        self.__verifyThread.signal.dictSignal.connect(self.__verify_clicked_ui)

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
        result = {
            'status': False,
            'error': None,
            'message': translator("This wallet's PIN code doesn't match"),
            'params': {
                'username': '',
                'key': ''
            }
        }

        try:
            username, password, pin_code, _ = globalmethods.AuthenticatorSetupModel.getData()

            if isinstance(pin_code, str):
                result['status'] = (self.get_pin_code_text() == pin_code)
            elif isinstance(pin_code, bytes):
                try:
                    payromasdk.tools.walletcreator.access(username, password, pin_code, '')
                    result['status'] = True
                except PermissionError:
                    pass

            if result['status']:
                result['message'] = translator("PIN code has been confirmed successfully")
                result['params']['username'] = username
                result['params']['key'] = payromasdk.tools.walletcreator.otp_hash(
                    username, password, self.get_pin_code_text()
                )

        except Exception as err:
            result['error'] = "{}: {}".format(translator("Failed"), str(err))

        time.sleep(3)
        self.__verifyThread.signal.dictSignal.emit(result)

    def __verify_clicked_ui(self, result: dict):
        if result['status']:
            globalmethods.AuthenticatorScanModel.setData(
                username=result['params']['username'], key=result['params']['key']
            )
            globalmethods.AuthenticatorFinishedModel.setData(key=result['params']['key'])
            globalmethods.AuthenticatorSetupModel.setCurrentTab(Tab.AuthenticatorSetupTab.SCAN)
            QApplication.quickNotification.successfully(result['message'])
        elif result['error']:
            QApplication.quickNotification.failed(result['error'])
        else:
            QApplication.quickNotification.warning(result['message'])

        self.verify_completed()
