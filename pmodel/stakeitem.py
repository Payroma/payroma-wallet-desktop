from pcontroller import payromasdk
from pui import stakeitem


class StakeItem(stakeitem.UiForm):
    def __init__(self, parent):
        super(StakeItem, self).__init__(parent)

        self.setup()

        # Variables
        self.__stakeEngine = None
        self.durationDetected = False

    def set_duration(self, locked: bool, start_time: int = None, end_time: int = None):
        super(StakeItem, self).set_duration(locked, start_time, end_time)
        self.durationDetected = True

    def engine(self) -> payromasdk.engine.stake.StakeEngine:
        return self.__stakeEngine

    def set_engine(self, engine: payromasdk.engine.stake.StakeEngine):
        self.__stakeEngine = engine
        self.set_pair_symbols(
            stake=engine.interface.stakeToken.symbol,
            earn=engine.interface.rewardToken.symbol
        )
