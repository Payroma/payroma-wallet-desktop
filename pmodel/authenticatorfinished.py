from plibs import *
from pheader import *
from pcontroller import globalmethods
from pui import authenticatorfinished


class AuthenticatorFinishedModel(authenticatorfinished.UiForm):
    def __init__(self, parent):
        super(AuthenticatorFinishedModel, self).__init__(parent)

        self.setup()

        # Global Methods
        globalmethods.AuthenticatorFinishedModel._setData = self.set_data

    @pyqtSlot()
    def done_clicked(self):
        globalmethods.MainModel.setCurrentTab(Tab.WALLETS_LIST)
