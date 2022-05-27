from plibs import *
from pheader import *
from pcontroller import payromasdk, event, ThreadingResult, ThreadingArea
from pui import stakelist
from pmodel import stakeitem


class StakeListModel(stakelist.UiForm, event.EventForm):
    def __init__(self, parent):
        super(StakeListModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__dataImportThread = ThreadingArea(self.__data_import_core)
        self.__dataImportThread.signal.resultSignal.connect(self.__data_import_ui)
        self.__dataImportThread.finished.connect(self.refresh)

        self.__updateThread = ThreadingArea(self.__update_core)
        self.__updateThread.signal.resultSignal.connect(self.__update_ui)

        # Variables
        self.__currentWalletEngine = None
        self.__currentBlockNumber = None
        self.__currentTab = None
        self.__stakeItems = []

    def showEvent(self, a0: QShowEvent):
        super(StakeListModel, self).showEvent(a0)
        self.__updateThread.start()

    def hideEvent(self, a0: QHideEvent):
        super(StakeListModel, self).hideEvent(a0)
        self.__updateThread.stop()

    def wallet_changed_event(self, engine: payromasdk.engine.wallet.WalletEngine):
        self.__currentWalletEngine = engine
        self.live_clicked()

    def network_changed_event(self, name: str, status: bool):
        if status:
            self.__dataImportThread.start()

    def network_block_changed_event(self, block_number: int):
        self.__currentBlockNumber = block_number

    def upcoming_clicked(self):
        self.__currentTab = payromasdk.tools.interface.Stake.UPCOMING
        self.refresh()

    def live_clicked(self):
        super(StakeListModel, self).live_clicked()
        self.__currentTab = payromasdk.tools.interface.Stake.LIVE
        self.refresh()

    def ended_clicked(self):
        self.__currentTab = payromasdk.tools.interface.Stake.ENDED
        self.refresh()

    @pyqtSlot(QListWidgetItem)
    def item_clicked(self, item: QListWidgetItem):
        widget = super(StakeListModel, self).item_clicked(item)
        event.stakePairChanged.notify(engine=widget.engine())
        event.mainTabChanged.notify(tab=Tab.STAKE_PAIR, recordable=False)

    def reset(self):
        super(StakeListModel, self).reset()
        self.__stakeItems.clear()

    def refresh(self):
        if not self.__currentWalletEngine or not self.__currentBlockNumber:
            return

        self.reset()

        for stake in payromasdk.engine.stake.get_all(filter_by_network=True):
            if stake.status(self.__currentBlockNumber) != self.__currentTab:
                continue

            item = stakeitem.StakeItem(self)
            item.set_engine(
                payromasdk.engine.stake.StakeEngine(
                    stake_interface=stake, sender=self.__currentWalletEngine.address()
                )
            )

            self.add_item(item)
            self.__stakeItems.append(item)

        QTimer().singleShot(100, self.repaint)

    def __data_import_core(self):
        result = ThreadingResult()

        try:
            is_empty = (len(payromasdk.engine.stake.get_all()) == 0)
            if is_empty:
                payromasdk.engine.stake.data_import(api_url=Website.STAKE_CONTRACTS_API)
                result.isValid = True

        except requests.exceptions.ConnectionError:
            pass

        except Exception as err:
            result.error(str(err))

        self.__dataImportThread.signal.resultSignal.emit(result)

    @staticmethod
    def __data_import_ui(result: ThreadingResult):
        if result.isError:
            result.show_message()

    def __update_core(self):
        while self.__updateThread.isRunning():
            result = ThreadingResult(
                params={
                    'tvl': 0,
                    'items': {}
                }
            )

            try:
                for stake in payromasdk.engine.stake.get_all(filter_by_network=True):
                    if stake.stakeToken.symbol == PayromaToken.SYMBOL:
                        engine = payromasdk.engine.stake.StakeEngine(stake_interface=stake)
                        result.params['tvl'] += engine.total_supply().value()

                for item in self.__stakeItems:
                    result.params['items'].update({
                        item: {
                            'apr': item.engine().get_apr(),
                            'duration': None if item.durationDetected else item.engine().locked_to_end()
                        }
                    })

                result.isValid = True

                if result.isValid:
                    result.params['tvl'] = payromasdk.tools.interface.WeiAmount(
                        value=result.params['tvl'], decimals=PayromaToken.DECIMALS
                    )

            except requests.exceptions.ConnectionError:
                pass

            except Exception as err:
                result.error(str(err))

            self.__updateThread.signal.resultSignal.emit(result)
            time.sleep(10)

    def __update_ui(self, result: ThreadingResult):
        if result.isValid:
            self.set_data(result.params['tvl'].to_ether_string(), PayromaToken.SYMBOL)

            for item, info in result.params['items'].items():
                try:
                    item.set_apr(info['apr'])
                    if not item.durationDetected:
                        item.set_duration(
                            locked=info['duration'],
                            start_time=item.engine().interface.startTime,
                            end_time=item.engine().interface.endTime
                        )
                except RuntimeError:
                    continue

        elif result.isError:
            result.show_message()
