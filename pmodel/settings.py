from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk
from pui import settings


class SettingsModel(settings.UiForm):
    def __init__(self, parent):
        super(SettingsModel, self).__init__(parent)

        self.setup()

    def showEvent(self, event: QShowEvent):
        super(SettingsModel, self).showEvent(event)

        self.set_data(
            network_connected=payromasdk.MainProvider.is_connected(),
            network_name=payromasdk.MainProvider.interface.name
        )

    @pyqtSlot(bool)
    def switch_clicked(self, state: bool):
        theme_name = 'dark' if state else ''
        globalmethods.MainModel.setThemeMode(theme_name)
        Global.settings.update_option(SettingsOption.themeName, theme_name)

    @pyqtSlot()
    def network_clicked(self):
        globalmethods.MainModel.setCurrentTab(Tab.NETWORKS_LIST)

    @pyqtSlot()
    def backup_clicked(self):
        super(SettingsModel, self).backup_clicked()

    @pyqtSlot()
    def import_clicked(self):
        super(SettingsModel, self).import_clicked()
