from plibs import *
from pheader import *
from pcontroller import event, url_open
from pui import authenticatordownload


class AuthenticatorDownloadModel(authenticatordownload.UiForm):
    def __init__(self, parent):
        super(AuthenticatorDownloadModel, self).__init__(parent)

        self.setup()

    @pyqtSlot()
    def google_play_clicked(self):
        url_open(Website.Authenticator.GOOGLE_PLAY)

    @pyqtSlot()
    def app_store_clicked(self):
        url_open(Website.Authenticator.APP_STORE)

    @pyqtSlot()
    def authy_clicked(self):
        url_open(Website.Authenticator.AUTHY)

    @pyqtSlot()
    def next_clicked(self):
        event.authenticatorSetupTabChanged.notify(tab=Tab.AuthenticatorSetupTab.VERIFICATION)
