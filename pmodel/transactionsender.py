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
        self.__confirmThread.finished.connect(self.confirm_completed)

        # Variables
        self.__currentWalletEngine = None
        self.__tx = None
        self.__abi = None
        self.__args = None
        self.__data = None
        self.__symbol = None
        self.__privateKey = None

    def showEvent(self, a0: QShowEvent):
        super(TransactionSenderModel, self).showEvent(a0)
        self.__gasUpdateThread.start()

    def hideEvent(self, a0: QHideEvent):
        super(TransactionSenderModel, self).hideEvent(a0)
        self.__gasUpdateThread.stop()

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine

    def transaction_sender_changed_event(self, tx: dict, details: dict, symbol: str):
        self.__tx = tx
        self.__abi = details.get('abi', {})
        self.__args = details.get('args', {})
        self.__data = details.get('data', '')
        self.__symbol = symbol

        fn_name = self.__abi.get('name', "transfer")

        to_address = self.__args.get('recipient', self.__args.get('spender'))
        if not to_address:
            to_address = payromasdk.tools.interface.Address(tx[payromasdk.engine.provider.Metadata.TO])

        amount = self.__args.get('amount', self.__args.get('_amount'))
        if not amount:
            amount = payromasdk.tools.interface.WeiAmount(
                value=tx[payromasdk.engine.provider.Metadata.VALUE], decimals=18
            )

        self.reset()
        self.set_data(
            network=payromasdk.MainProvider.interface.name,
            function=translator(fn_name),
            address=to_address.value(),
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
                args[kay] = value.to_ether_string(currency_format=False)
            else:
                args[kay] = str(value)

        details_widget = transactiondetails.TransactionDetailsModel(self)
        details_widget.set_data(
            function_type=self.__abi.get('name', "transfer"),
            from_address=tx[payromasdk.engine.token.Metadata.FROM],
            to_address=tx[payromasdk.engine.token.Metadata.TO],
            tx=json.dumps(tx, sort_keys=False, indent=4),
            abi=json.dumps(self.__abi, sort_keys=False, indent=4),
            args=json.dumps(args, sort_keys=False, indent=4),
            data=tx[payromasdk.engine.token.Metadata.DATA]
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
            message=translator("Transaction failed, Please try again.")
        )

        try:
            tx_hash = payromasdk.MainProvider.send_transaction(
                tx_data=self.__tx, private_key=self.__privateKey
            )

            fn_name = self.__abi.get('name', "transfer")
            from_address = payromasdk.tools.interface.Address(
                self.__tx[payromasdk.engine.provider.Metadata.FROM]
            )

            to_address = self.__args.get('recipient', self.__args.get('spender'))
            if not to_address:
                to_address = payromasdk.tools.interface.Address(
                    self.__tx[payromasdk.engine.provider.Metadata.TO]
                )

            amount = self.__args.get('amount', self.__args.get('_amount'))
            if not amount:
                amount = payromasdk.tools.interface.WeiAmount(
                    value=self.__tx[payromasdk.engine.provider.Metadata.VALUE], decimals=18
                )

            transaction = payromasdk.tools.interface.Transaction(
                tx_hash=tx_hash,
                function=fn_name,
                from_address=from_address,
                to_address=to_address,
                amount=amount,
                symbol=self.__symbol,
                date_created=time.ctime(),
                status=payromasdk.tools.interface.Transaction.Status.PENDING
            )

            if self.__currentWalletEngine.add_transaction(transaction_interface=transaction):
                result.isValid = True

            if result.isValid:
                result.message = translator("Please wait, Transaction in processing.")

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__confirmThread.signal.resultSignal.emit(result)

    @staticmethod
    def __confirm_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.transactionHistoryEdited.notify()
            event.mainTabChanged.notify(tab=Tab.HISTORY_LIST)

        result.show_message()

    def __gas_update_core(self):
        while self.__gasUpdateThread.isRunning():
            result = ThreadingResult(
                message=translator("Unable to connect, make sure you are connected to the internet."),
                params={
                    payromasdk.engine.provider.Metadata.ESTIMATED_GAS: '--',
                    payromasdk.engine.provider.Metadata.MAX_FEE: '--',
                    payromasdk.engine.provider.Metadata.TOTAL: '--',
                    payromasdk.engine.provider.Metadata.MAX_AMOUNT: '--'
                }
            )

            try:
                gas = payromasdk.MainProvider.add_gas(
                    tx_data=self.__tx, eip1559_enabled=payromasdk.MainProvider.eip1559_supported()
                )

                for key, value in gas.items():
                    result.params[key] = value.to_ether_string()

                max_amount = gas[payromasdk.engine.provider.Metadata.MAX_AMOUNT]
                balance = payromasdk.MainProvider.balance_of(self.__currentWalletEngine.address())
                if max_amount.value() > balance.value():
                    raise ValueError

                result.isValid = True

            except requests.exceptions.ConnectionError:
                pass

            except ValueError:
                result.message = translator("Insufficient funds for transfer, maybe it needs gas fee.")

            except Exception as err:
                result.error(str(err))

            self.__gasUpdateThread.signal.resultSignal.emit(result)
            time.sleep(15)

    def __gas_update_ui(self, result: ThreadingResult):
        self.update_gas(
            symbol=payromasdk.MainProvider.interface.symbol,
            estimated_gas=result.params[payromasdk.engine.provider.Metadata.ESTIMATED_GAS],
            max_fee=result.params[payromasdk.engine.provider.Metadata.MAX_FEE],
            total=result.params[payromasdk.engine.provider.Metadata.TOTAL],
            max_amount=result.params[payromasdk.engine.provider.Metadata.MAX_AMOUNT],
            confirmable=result.isValid
        )

        if not result.isValid:
            result.show_message()

    def __authenticator_forward(self, private_key: str):
        self.__privateKey = private_key
        event.mainTabChanged.notify(tab=Tab.TRANSACTION_SENDER, recordable=False)
