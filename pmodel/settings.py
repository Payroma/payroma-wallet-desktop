from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, translator, ThreadingResult, ThreadingArea
from pui import settings


class SettingsModel(settings.UiForm):
    def __init__(self, parent):
        super(SettingsModel, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__networkDetectionThread = ThreadingArea(self.__network_detection_core)
        self.__networkDetectionThread.signal.resultSignal.connect(self.__network_detection_ui)

    def showEvent(self, event: QShowEvent):
        super(SettingsModel, self).showEvent(event)
        self.__networkDetectionThread.start()

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

    def __network_detection_core(self):
        result = ThreadingResult(
            message=translator("Unable to connect, make sure you are connected to the internet"),
            params={
                'isConnected': False,
                'networkName': payromasdk.MainProvider.interface.name
            }
        )

        try:
            result.isValid = result.params['isConnected'] = payromasdk.MainProvider.is_connected()
        except Exception as err:
            result.error(str(err))

        self.__networkDetectionThread.signal.resultSignal.emit(result)

    def __network_detection_ui(self, result: ThreadingResult):
        self.set_data(result.params['isConnected'], result.params['networkName'])

        if not result.isValid:
            result.show_message()
