from plibs import *
from pheader import *
from pcontroller import globalmethods, payromasdk, ThreadingArea, translator
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
        self.__setCurrentNetworkThread.signal.dictSignal.connect(self.__set_current_network_ui)

        # Variables
        self.__networks = []
        self.__currentNetwork = None

        # Run
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
                if not interface:
                    interface = network

            if current_network == network.networkID:
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
        result = {
            'status': False,
            'message': translator("Unable to connect, make sure you are connected to the internet")
        }

        try:
            Global.settings.update_option(SettingsOption.networkID, self.__currentNetwork.networkID)
            result['status'] = payromasdk.MainProvider.connect(network_interface=self.__currentNetwork)
            if result['status']:
                result['message'] = translator(
                    "{}: {}".format(translator("Current network"), self.__currentNetwork.name)
                )

        except Exception as err:
            result['message'] = "{}: {}".format(translator("Failed"), str(err))

        self.__setCurrentNetworkThread.signal.dictSignal.emit(result)

    def __set_current_network_ui(self, result: dict):
        for item in self.__networks:
            item.set_status(
                item.interface().networkID == self.__currentNetwork.networkID and result['status']
            )

        if result['status']:
            QApplication.quickNotification.successfully(result['message'])
        else:
            QApplication.quickNotification.warning(result['message'])

        QTimer().singleShot(100, self.repaint)
