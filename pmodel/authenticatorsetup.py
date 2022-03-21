from plibs import *
from pheader import *
from pcontroller import globalmethods
from pui import authenticatorsetup
from pmodel.authenticatordownload import AuthenticatorDownloadModel
from pmodel.authenticatorverification import AuthenticatorVerificationModel
from pmodel.authenticatorscan import AuthenticatorScanModel
from pmodel.authenticatorfinished import AuthenticatorFinishedModel


class AuthenticatorSetupModel(authenticatorsetup.UiForm):
    def __init__(self, parent):
        super(AuthenticatorSetupModel, self).__init__(parent)

        self.setup()

        # Global Methods
        globalmethods.AuthenticatorSetupModel._setData = self.set_data
        globalmethods.AuthenticatorSetupModel._getData = self.get_data
        globalmethods.AuthenticatorSetupModel._setCurrentTab = self.set_current_tab

        # Tabs
        self.add_tab(AuthenticatorDownloadModel(self), Tab.AuthenticatorSetupTab.DOWNLOAD)
        self.add_tab(AuthenticatorVerificationModel(self), Tab.AuthenticatorSetupTab.VERIFICATION)
        self.add_tab(AuthenticatorScanModel(self), Tab.AuthenticatorSetupTab.SCAN)
        self.add_tab(AuthenticatorFinishedModel(self), Tab.AuthenticatorSetupTab.FINISHED)

        # Variables
        self.__usernameValue = ''
        self.__passwordValue = ''
        self.__PINCodeValue = ''
        self.__addressValue = ''

    def showEvent(self, event: QShowEvent):
        super(AuthenticatorSetupModel, self).showEvent(event)
        self.reset()

    def set_data(self, username: str, password: str, pin_code: Union[str, bytes], address: str = ''):
        self.__usernameValue = username
        self.__passwordValue = password
        self.__PINCodeValue = pin_code
        self.__addressValue = address

    def get_data(self) -> tuple[str, str, Union[str, bytes], str]:
        return self.__usernameValue, self.__passwordValue, self.__PINCodeValue, self.__addressValue
