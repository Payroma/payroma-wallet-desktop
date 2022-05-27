from plibs import *
from pcontroller import payromasdk, event, translator, ThreadingResult, ThreadingArea, url_open
from pui import stakepair
from pmodel.stakepairapproval import StakePairApprovalModel
from pmodel.stakepairamount import StakePairAmountModel


class StakePairModel(stakepair.UiForm, event.EventForm):
    def __init__(self, parent):
        super(StakePairModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__updateThread = ThreadingArea(self.__update_core)
        self.__updateThread.signal.resultSignal.connect(self.__update_ui)

        # Tabs
        self.add_tab(StakePairApprovalModel(self), '')
        self.add_tab(StakePairAmountModel(self), '')

        # Variables
        self.__currentBlockNumber = None
        self.__stakeEngine = None

    def showEvent(self, a0: QShowEvent):
        super(StakePairModel, self).showEvent(a0)
        self.__updateThread.start()

    def hideEvent(self, a0: QHideEvent):
        super(StakePairModel, self).hideEvent(a0)
        self.__updateThread.stop()

    def network_block_changed_event(self, block_number: int):
        self.__currentBlockNumber = block_number

    def stake_pair_changed_event(self, engine: payromasdk.engine.stake.StakeEngine):
        titles = {
            payromasdk.tools.interface.Stake.UPCOMING: "Start in",
            payromasdk.tools.interface.Stake.LIVE: "End in",
            payromasdk.tools.interface.Stake.ENDED: "Ended"
        }

        self.reset()
        self.set_data(
            block_title=translator(titles[engine.interface.status(self.__currentBlockNumber)]),
            stake_symbol=engine.interface.stakeToken.symbol,
            earn_symbol=engine.interface.rewardToken.symbol
        )
        self.__stakeEngine = engine

    def stake_pair_approved_event(self):
        self.set_approved()

    def staking_contract_clicked(self):
        self.__stakeEngine.interface.contract.explorer_view()

    def block_time_clicked(self):
        self.__stakeEngine.interface.explorer_view_countdown(self.__currentBlockNumber)

    def stake_website_clicked(self):
        url_open(self.__stakeEngine.interface.stakeWebsite)

    def stake_contract_clicked(self):
        self.__stakeEngine.interface.stakeToken.contract.explorer_view()

    def earn_website_clicked(self):
        url_open(self.__stakeEngine.interface.rewardWebsite)

    def earn_contract_clicked(self):
        self.__stakeEngine.interface.rewardToken.contract.explorer_view()

    def __update_core(self):
        while self.__updateThread.isRunning():
            result = ThreadingResult(
                params={
                    'blocks': None,
                    'totalStaked': None,
                    'symbol': None
                }
            )

            try:
                total_supply = self.__stakeEngine.total_supply().to_ether_string()
                symbol = self.__stakeEngine.interface.stakeToken.symbol
                blocks = int(self.__stakeEngine.interface.endBlock - self.__currentBlockNumber)
                if blocks < 0:
                    blocks = 0

                result.isValid = True

                if result.isValid:
                    result.params['blocks'] = blocks
                    result.params['totalStaked'] = total_supply
                    result.params['symbol'] = symbol

            except requests.exceptions.ConnectionError:
                pass

            except Exception as err:
                result.error(str(err))

            self.__updateThread.signal.resultSignal.emit(result)
            time.sleep(10)

    def __update_ui(self, result: ThreadingResult):
        if result.isValid:
            self.update_blocks(result.params['blocks'])
            self.update_total_staked(result.params['totalStaked'], result.params['symbol'])

        elif result.isError:
            result.show_message()
