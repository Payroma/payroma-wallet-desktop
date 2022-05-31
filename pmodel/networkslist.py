from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import networkslist
from pmodel import networkitem


class NetworksListModel(networkslist.UiForm, event.EventForm):
    def __init__(self, parent):
        super(NetworksListModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__updateThread = ThreadingArea(self.__update_core)
        self.__updateThread.signal.resultSignal.connect(self.__update_ui)

        # Variables
        self.__currentNetworkItem = None

    def app_started_event(self):
        hide_testnet = Global.settings.get_option(SettingsOption.hideTestNet)
        super(NetworksListModel, self).switch_clicked(hide_testnet)
        self.refresh()

    def network_edited_event(self):
        self.refresh()

    @pyqtSlot(bool)
    def switch_clicked(self, state: bool):
        super(NetworksListModel, self).switch_clicked(state)
        Global.settings.update_option(SettingsOption.hideTestNet, state)
        self.refresh()

    @pyqtSlot()
    def add_new_clicked(self):
        event.mainTabChanged.notify(tab=Tab.ADD_NETWORK)

    @pyqtSlot(QListWidgetItem)
    def item_clicked(self, item: QListWidgetItem):
        widget = super(NetworksListModel, self).item_clicked(item)
        if widget.is_checked():
            return

        Global.settings.update_option(SettingsOption.networkID, widget.interface().id)
        self.__current_network(widget)
        self.__updateThread.start()

    def refresh(self):
        default_network = Global.settings.get_option(SettingsOption.networkID, default=True)
        current_network = Global.settings.get_option(SettingsOption.networkID)
        hide_testnet = Global.settings.get_option(SettingsOption.hideTestNet)
        item_checked = None

        self.reset()

        for network in payromasdk.engine.network.get_all():
            if hide_testnet and 'testnet' in network.name.lower():
                continue

            item = networkitem.NetworkItem(self)
            item.set_interface(network)

            if network.id == default_network:
                item.set_master()

            if network.id == current_network or not item_checked:
                item_checked = item

            self.add_item(item)

        self.__current_network(item_checked)
        self.__updateThread.start()

        QTimer().singleShot(100, self.repaint)

    def __current_network(self, item: QWidget):
        # Uncheck the previous network
        if self.__currentNetworkItem:
            self.__currentNetworkItem.set_checked(False)

        # Check the new network
        self.__currentNetworkItem = item
        self.__currentNetworkItem.set_checked(True)

    def __update_core(self):
        current_network = self.__currentNetworkItem.interface()
        payromasdk.MainProvider.connect(network_interface=current_network)
        latest_status = None

        while self.__updateThread.isRunning():
            result = ThreadingResult(
                message=translator("Unable to connect, make sure you are connected to the internet."),
                params={
                    'statusChanged': False,
                    'isConnected': False,
                    'blockNumber': 0
                }
            )

            try:
                current_status = payromasdk.MainProvider.is_connected()
                if current_status != latest_status:
                    result.params['statusChanged'] = True
                    latest_status = current_status

                block_number = payromasdk.MainProvider.block_number()
                result.isValid = True

                if result.isValid:
                    result.message = "{}: {}".format(translator("Current Network"), current_network.name)
                    result.params['isConnected'] = current_status
                    result.params['blockNumber'] = block_number

            except requests.exceptions.ConnectionError:
                pass

            except Exception as err:
                result.error(str(err))

            self.__updateThread.signal.resultSignal.emit(result)
            time.sleep(10)

    @staticmethod
    def __update_ui(result: ThreadingResult):
        if result.params['statusChanged']:
            event.networkChanged.notify(
                name=payromasdk.MainProvider.interface.name,
                status=result.params['isConnected']
            )

        if result.isValid:
            event.networkBlockChanged.notify(block_number=result.params['blockNumber'])

        if not result.isValid or result.params['statusChanged']:
            result.show_message()
