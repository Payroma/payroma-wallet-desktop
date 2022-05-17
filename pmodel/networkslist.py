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
        self.__networkStatusThread = ThreadingArea(self.__network_status_core)
        self.__networkStatusThread.signal.resultSignal.connect(self.__network_status_ui)
        self.__networkStatusThread.signal.normalSignal.connect(self.refresh)

        self.__setCurrentNetworkThread = ThreadingArea(self.__set_current_network_core)
        self.__setCurrentNetworkThread.signal.resultSignal.connect(self.__set_current_network_ui)

        # Variables
        self.__networkItems = []
        self.__currentNetwork = None

    def app_started_event(self):
        self.__networkStatusThread.start()

    def network_edited_event(self):
        self.refresh()

    @pyqtSlot()
    def add_new_clicked(self):
        event.mainTabChanged.notify(tab=Tab.ADD_NETWORK)

    @pyqtSlot(QListWidgetItem)
    def item_clicked(self, item: QListWidgetItem):
        widget = super(NetworksListModel, self).item_clicked(item)
        self.set_current_network(widget.interface())

    def reset(self):
        super(NetworksListModel, self).reset()
        self.__networkItems.clear()
        self.__currentNetwork = None

    def refresh(self):
        interface = None
        default_network = Global.settings.get_option(SettingsOption.networkID, default=True)
        current_network = Global.settings.get_option(SettingsOption.networkID)
        self.reset()

        for network in payromasdk.engine.network.get_all():
            item = networkitem.NetworkItem(self)
            item.set_interface(network)

            if default_network == network.id:
                item.set_master()

            if not interface or current_network == network.id:
                interface = network

            self.add_item(item)
            self.__networkItems.append(item)

        self.set_current_network(interface)

    def set_current_network(self, interface: payromasdk.tools.interface.Network):
        if self.__currentNetwork is interface:
            return

        self.__currentNetwork = interface
        self.__setCurrentNetworkThread.start()

    def __set_current_network_core(self):
        result = ThreadingResult(
            message=translator("Unable to connect, make sure you are connected to the internet"),
            params={
                'isConnected': False
            }
        )

        try:
            Global.settings.update_option(SettingsOption.networkID, self.__currentNetwork.id)
            result.isValid = payromasdk.MainProvider.connect(network_interface=self.__currentNetwork)
            if result.isValid:
                result.params['isConnected'] = payromasdk.MainProvider.is_connected()
                result.message = translator(
                    "{}: {}".format(translator("Current network"), payromasdk.MainProvider.interface.name)
                )

        except Exception as err:
            result.error(str(err))

        self.__setCurrentNetworkThread.signal.resultSignal.emit(result)

    def __set_current_network_ui(self, result: ThreadingResult):
        for item in self.__networkItems:
            item.set_status(
                item.interface() is payromasdk.MainProvider.interface and result.params['isConnected']
            )

        event.networkChanged.notify(
            name=payromasdk.MainProvider.interface.name,
            status=result.params['isConnected']
        )
        result.show_message()
        QTimer().singleShot(100, self.repaint)

    def __network_status_core(self):
        result = ThreadingResult()

        while True:
            try:
                try:
                    status = payromasdk.MainProvider.is_connected()
                except AttributeError:
                    status = True

                if result.isValid != status:
                    result.isValid = status
                    self.__networkStatusThread.signal.normalSignal.emit()

                continue

            except Exception as err:
                result.error(str(err))

            finally:
                time.sleep(60)

            self.__networkStatusThread.signal.resultSignal.emit(result)

    @staticmethod
    def __network_status_ui(result: ThreadingResult):
        if not result.isValid:
            result.show_message()
