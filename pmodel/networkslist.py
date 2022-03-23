from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, translator, ThreadingResult, ThreadingArea
from pui import networkslist
from pmodel import networkitem


class NetworksListModel(networkslist.UiForm):
    def __init__(self, parent):
        super(NetworksListModel, self).__init__(parent)

        self.setup()

        # Global Methods
        globalmethods.NetworksListModel._refresh = self.refresh

        # Threading Methods
        self.__setCurrentNetworkThread = ThreadingArea(self.__set_current_network_core)
        self.__setCurrentNetworkThread.signal.resultSignal.connect(self.__set_current_network_ui)

        # Variables
        self.__networks = []
        self.__currentNetwork = None

        # Run
        self.refresh()

    def showEvent(self, event: QShowEvent):
        super(NetworksListModel, self).showEvent(event)
        self.refresh()

    @pyqtSlot()
    def add_new_clicked(self):
        globalmethods.MainModel.setCurrentTab(Tab.ADD_NETWORK)

    @pyqtSlot(QListWidgetItem)
    def item_clicked(self, item: QListWidgetItem):
        widget = super(NetworksListModel, self).item_clicked(item)
        self.set_current_network(widget.interface())

    def reset(self):
        super(NetworksListModel, self).reset()
        self.__networks.clear()
        self.__currentNetwork = None

    def refresh(self):
        interface = None
        default_network = Global.settings.get_option(SettingsOption.networkID, default=True)
        current_network = Global.settings.get_option(SettingsOption.networkID)
        self.reset()

        for network in payromasdk.engine.network.get_all():
            item = networkitem.NetworkItem(self)
            item.set_interface(network)
            item.set_name(network.name)
            item.set_symbol(network.symbol)

            if default_network == network.networkID:
                item.set_master()

            if not interface or current_network == network.networkID:
                interface = network

            self.add_item(item)
            self.__networks.append(item)

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
            Global.settings.update_option(SettingsOption.networkID, self.__currentNetwork.networkID)
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
        for item in self.__networks:
            item.set_status(
                item.interface() is payromasdk.MainProvider.interface and result.params['isConnected']
            )

        result.show_message()
        QTimer().singleShot(100, self.repaint)
