from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import addwallet, styles


class AddWalletModel(addwallet.UiForm):
    def __init__(self, parent):
        super(AddWalletModel, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__addWalletThread = ThreadingArea(self.__add_clicked_core)
        self.__addWalletThread.signal.resultSignal.connect(self.__add_clicked_ui)
        self.__addWalletThread.finished.connect(self.add_completed)

        # Variables
        self.__isTyping = False

    def showEvent(self, a0: QShowEvent):
        super(AddWalletModel, self).showEvent(a0)
        if self.__addWalletThread.isRunning():
            return

        self.reset()

    @pyqtSlot(str)
    def username_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1000, lambda: self.__username_changed(text))

    def __username_changed(self, text: str):
        valid = False
        if text != self.get_username_text():
            return

        if text:
            is_exists = any(text == i.username for i in payromasdk.engine.wallet.get_all())
            if not is_exists:
                valid = True

        self.__isTyping = False
        super(AddWalletModel, self).username_changed(text, valid)

    @pyqtSlot(str)
    def password_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1500, lambda: self.__password_changed(text))

    def __password_changed(self, text: str):
        valid = False
        if text != self.get_password_text():
            return

        if text:
            if self.get_confirm_password_text():
                self.__confirm_password_changed(self.get_confirm_password_text())

            if self.get_strength_text() in [
                SPInputmanager.StrengthState.good.text, SPInputmanager.StrengthState.excellent.text
            ]:
                valid = True

        self.__isTyping = False
        super(AddWalletModel, self).password_changed(text, valid)

    @pyqtSlot(str)
    def confirm_password_changed(self, text: str):
        self.__isTyping = True
        QTimer().singleShot(1500, lambda: self.__confirm_password_changed(text))

    def __confirm_password_changed(self, text: str):
        valid = False
        if text != self.get_confirm_password_text():
            return

        if text:
            if self.get_password_text() == self.get_confirm_password_text():
                valid = True

        self.__isTyping = False
        super(AddWalletModel, self).confirm_password_changed(text, valid)

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
        super(AddWalletModel, self).pin_code_changed(text, valid)

    @pyqtSlot()
    def add_clicked(self):
        if self.__isTyping or self.__addWalletThread.isRunning():
            return

        title = translator("Please note that:")
        description1 = translator("Username and password are sensitive to characters.")
        description2 = translator("Without PIN code you cannot access your wallet again.")
        description3 = translator("Password and PIN code are not changeable or recoverable.")
        description4 = translator("Your private key and PIN code not stored anywhere.")
        description5 = translator("Do not share your password and PIN code with anyone.")
        description6 = translator("Recommended to backup all your wallets to an external file.")
        html_message = '''
            <h2>%s</h2><ul>* %s</ul><ul>* %s</ul><ul>* %s</ul><ul>* %s</ul><ul>* %s</ul><ul>* %s</ul>
        ''' % (title, description1, description2, description3, description4, description5, description6)
        messagebox = SPGraphics.MessageBoxConfirm(
            parent=self,
            text=html_message,
            color=styles.data.colors.font.name(),
            accept=translator("I Understand"),
            window_size=QSize(451, 321)
        )
        messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
        messagebox.labelMessage.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        messagebox.exec_()

        if messagebox.clickedOn is not SPGraphics.Button.ACCEPT:
            return

        super(AddWalletModel, self).add_clicked()
        self.__addWalletThread.start()

    def __add_clicked_core(self):
        result = ThreadingResult(
            message=translator("Failed to add wallet, Please try again."),
            params={
                'engine': None
            }
        )

        try:
            address = None
            username = self.get_username_text()
            password = self.get_password_text()
            pin_code = self.get_pin_code_text()
            otp_hash = payromasdk.tools.walletcreator.otp_hash(
                username=username, password=password, pin_code=pin_code
            )
            otp_code = pyotp.TOTP(otp_hash)

            if payromasdk.engine.wallet.add_new(
                username=username, password=password, pin_code=pin_code, otp_code=otp_code.now()
            ):
                try:
                    address, _, _ = payromasdk.tools.walletcreator.access(
                        username=username, password=password, pin_code=pin_code, otp_code=otp_code.now()
                    )
                    result.isValid = True
                except TypeError:
                    # Fails if access method returned False
                    pass

            if result.isValid:
                result.message = translator("Let's setup your 2FA code")
                for wallet in payromasdk.engine.wallet.get_all():
                    if wallet.address.value() == address.value():
                        result.params['engine'] = payromasdk.engine.wallet.WalletEngine(wallet)
                        break

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__addWalletThread.signal.resultSignal.emit(result)

    @staticmethod
    def __add_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.walletEdited.notify()
            event.walletChanged.notify(engine=result.params['engine'])
            event.mainTabChanged.notify(tab=Tab.AUTHENTICATOR_SETUP, recordable=False)

        result.show_message()
