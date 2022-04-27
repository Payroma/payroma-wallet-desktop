from plibs import *
from pheader import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import transactionsender, fonts, styles, Size
from pmodel import transactiondetails


class TransactionSenderModel(transactionsender.UiForm, event.EventForm):
    def __init__(self, parent):
        super(TransactionSenderModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__gasUpdateThread = ThreadingArea(self.__gas_update_core)
        self.__gasUpdateThread.signal.resultSignal.connect(self.__gas_update_ui)

        self.__confirmThread = ThreadingArea(self.__confirm_clicked_core)
        self.__confirmThread.signal.resultSignal.connect(self.__confirm_clicked_ui)

        # Variables
        self.__currentWalletEngine = None
        self.__tx = None
        self.__abi = None
        self.__args = None
        self.__data = None
        self.__privateKey = None

    def showEvent(self, a0: QShowEvent):
        super(TransactionSenderModel, self).showEvent(a0)
        self.__gasUpdateThread.start()

    def hideEvent(self, a0: QHideEvent):
        super(TransactionSenderModel, self).hideEvent(a0)
        self.__gasUpdateThread.terminate()
        self.__gasUpdateThread.wait()

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine

    def transaction_sender_changed_event(self, tx: dict, details: dict, symbol: str):
        self.__tx = tx
        self.__abi = details.get('abi', {})
        self.__args = details.get('args', {})
        self.__data = details.get('data', '')

        fn_name = self.__abi.get('name', "transfer").title()

        address = self.__args.get('recipient', self.__args.get('spender'))
        if not address:
            address = payromasdk.tools.interface.Address(tx[payromasdk.engine.provider.Metadata.TO])

        amount = self.__args.get('amount', self.__args.get('_amount'))
        if not amount:
            amount = payromasdk.tools.interface.WeiAmount(
                value=tx[payromasdk.engine.provider.Metadata.VALUE], decimals=18
            )

        self.reset()
        self.set_data(
            network=payromasdk.MainProvider.interface.name,
            function=translator(fn_name),
            address=address.value(),
            amount=amount.to_ether_string(),
            symbol=symbol
        )

        if self.__currentWalletEngine.is_logged():
            event.authenticatorForward.notify(method=self.__authenticator_forward)
        else:
            QApplication.quickNotification.warning(
                translator("A login is required to create the transaction."), timeout=2500
            )
            event.loginForward.notify(method=self.__authenticator_forward)

    @pyqtSlot()
    def network_clicked(self):
        event.mainTabChanged.notify(tab=Tab.NETWORKS_LIST)

    @pyqtSlot()
    def details_clicked(self):
        tx = self.__tx.copy()
        tx[payromasdk.engine.token.Metadata.DATA] = self.__data

        args = {}
        for kay, value in self.__args.items():
            if isinstance(value, payromasdk.tools.interface.Address):
                args[kay] = value.value()
            elif isinstance(value, payromasdk.tools.interface.WeiAmount):
                args[kay] = value.to_ether_string()
            else:
                args[kay] = str(value)

        details_widget = transactiondetails.TransactionDetailsModel(self)
        details_widget.set_data(
            function_type=self.__abi.get('name', 'transfer'),
            from_address=tx[payromasdk.engine.token.Metadata.FROM],
            to_address=tx[payromasdk.engine.token.Metadata.TO],
            tx=json.dumps(tx, sort_keys=False, indent=4),
            abi=json.dumps(self.__abi, sort_keys=False, indent=4),
            args=json.dumps(args, sort_keys=False, indent=4),
            data=self.__data
        )

        messagebox = SPGraphics.MessageBox(
            parent=self,
            text=translator("Transaction Details"),
            font_size=fonts.data.size.title,
            color=styles.data.colors.font.name(),
            window_size=QSize(Size.messageBox.width(), 451)
        )
        messagebox.frame.layout().setContentsMargins(0, 21, 0, 11)
        messagebox.frame.layout().setSpacing(11)
        messagebox.frame.layout().addWidget(details_widget)
        messagebox.exec_()

    @pyqtSlot()
    def confirm_clicked(self):
        if self.__confirmThread.isRunning():
            return

        super(TransactionSenderModel, self).confirm_clicked()
        self.__confirmThread.start()

    def __confirm_clicked_core(self):
        result = ThreadingResult(
            message=translator("Transaction confirmation failed, Please try again"),
            params={
                'txHash': None
            }
        )

        try:
            tx_hash = payromasdk.MainProvider.send_transaction(
                tx_data=self.__tx, private_key=self.__privateKey
            )
            result.isValid = True

            if result.isValid:
                result.message = translator("Transaction confirmed successfully")
                result.params['txHash'] = tx_hash

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__confirmThread.signal.resultSignal.emit(result)

    def __confirm_clicked_ui(self, result: ThreadingResult):
        if result.isValid:
            event.mainTabChanged.notify(tab=Tab.HISTORY_LIST)

        result.show_message()
        self.confirm_completed()

    def __gas_update_core(self):
        while True:
            result = ThreadingResult(
                message=translator("Unable to connect, make sure you are connected to the internet"),
                params={
                    payromasdk.engine.provider.Metadata.ESTIMATED_GAS: None,
                    payromasdk.engine.provider.Metadata.MAX_FEE: None,
                    payromasdk.engine.provider.Metadata.TOTAL: None,
                    payromasdk.engine.provider.Metadata.MAX_AMOUNT: None
                }
            )

            try:
                gas = payromasdk.MainProvider.add_gas(
                    tx_data=self.__tx, eip1559_enabled=payromasdk.MainProvider.eip1559_supported()
                )
                result.params.update(gas)

                balance = payromasdk.MainProvider.balance_of(self.__currentWalletEngine.address()).value()
                max_amount = gas[payromasdk.engine.provider.Metadata.MAX_AMOUNT].value()
                if balance < max_amount:
                    raise ValueError

                result.isValid = True

            except requests.exceptions.ConnectionError:
                pass

            except ValueError:
                result.message = translator("Insufficient funds for transfer, maybe it needs gas fee.")

            except Exception as err:
                result.error(str(err))

            finally:
                self.__gasUpdateThread.signal.resultSignal.emit(result)
                time.sleep(15)

    def __gas_update_ui(self, result: ThreadingResult):
        try:
            estimated_gas = result.params[payromasdk.engine.provider.Metadata.ESTIMATED_GAS].to_ether_string()
            max_fee = result.params[payromasdk.engine.provider.Metadata.MAX_FEE].to_ether_string()
            total = result.params[payromasdk.engine.provider.Metadata.TOTAL].to_ether_string()
            max_amount = result.params[payromasdk.engine.provider.Metadata.MAX_AMOUNT].to_ether_string()
        except AttributeError:
            estimated_gas = max_fee = total = max_amount = '--'

        self.update_gas(
            symbol=payromasdk.MainProvider.interface.symbol,
            estimated_gas=estimated_gas,
            max_fee=max_fee,
            total=total,
            max_amount=max_amount,
            confirmable=result.isValid
        )

        if not result.isValid:
            result.show_message()

    def __authenticator_forward(self, private_key: str):
        self.__privateKey = private_key
        event.mainTabChanged.notify(tab=Tab.TRANSACTION_SENDER, recordable=False)
