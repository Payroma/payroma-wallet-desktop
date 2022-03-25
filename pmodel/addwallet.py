from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, translator
from pui import addwallet, styles


class AddWalletModel(addwallet.UiForm):
    def __init__(self, parent):
        super(AddWalletModel, self).__init__(parent)

        self.setup()

        # Variables
        self.__isTyping = False

    def hideEvent(self, event: QHideEvent):
        super(AddWalletModel, self).hideEvent(event)
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
        QTimer().singleShot(1000, lambda: self.__password_changed(text))

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
        QTimer().singleShot(1000, lambda: self.__confirm_password_changed(text))

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
        if self.__isTyping:
            return

        super(AddWalletModel, self).add_clicked()

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

        if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
            globalmethods.AuthenticatorSetupModel.setData(
                username=self.get_username_text(),
                password=self.get_password_text(),
                pin_code=self.get_pin_code_text()
            )
            globalmethods.MainModel.setCurrentTab(Tab.AUTHENTICATOR_SETUP, recordable=False)
            QApplication.quickNotification.information(translator("Authenticator setup required to access"))

        self.add_completed()
