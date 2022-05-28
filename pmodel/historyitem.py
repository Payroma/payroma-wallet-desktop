from plibs import *
from pcontroller import payromasdk, translator, ThreadingResult, ThreadingArea
from pui import historyitem


class HistoryItem(historyitem.UiForm):
    def __init__(self, parent):
        super(HistoryItem, self).__init__(parent)

        self.setup()

        # Threading Methods
        self.__updateThread = ThreadingArea(self.__update_core)
        self.__updateThread.signal.resultSignal.connect(self.__update_ui)

        # Variables
        self.__interface = None

    def explorer_clicked(self):
        self.__interface.txHash.explorer_view()

    def interface(self) -> payromasdk.tools.interface.Transaction:
        return self.__interface

    def set_interface(self, interface: payromasdk.tools.interface.Transaction):
        self.__interface = interface
        self.set_icon(interface.symbol)
        self.set_function_name(interface.function)
        self.set_status(interface.status_text())
        self.set_balance(interface.amount.to_ether_string(), interface.symbol)
        self.set_address(interface.toAddress.value())
        self.set_date(interface.dateCreated)

        if self.__interface.status == payromasdk.tools.interface.Transaction.Status.PENDING:
            self.__updateThread.start()

    def __update_core(self):
        result = ThreadingResult(
            message=translator("Transaction failed!")
        )

        try:
            while True:
                try:
                    status = payromasdk.MainProvider.get_transaction_receipt(
                        transaction_hash=self.__interface.txHash
                    ).status

                except (AttributeError, requests.exceptions.ConnectionError):
                    time.sleep(10)

                else:
                    self.__interface.status = status
                    payromasdk.data.transactions.db.dump()
                    break

            if status == payromasdk.tools.interface.Transaction.Status.SUCCESS:
                result.isValid = True

            if result.isValid:
                result.message = translator("Transaction confirmed successfully.")

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__updateThread.signal.resultSignal.emit(result)

    def __update_ui(self, result: ThreadingResult):
        self.set_status(self.__interface.status_text())
        result.show_message()
