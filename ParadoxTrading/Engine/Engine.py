from collections import deque
from datetime import datetime

import typing

from ParadoxTrading.Engine.Event import EventAbstract
from ParadoxTrading.Engine.Execution import ExecutionAbstract
from ParadoxTrading.Engine.MarketSupply import MarketSupplyAbstract
from ParadoxTrading.Engine.Portfolio import PortfolioAbstract
from ParadoxTrading.Engine.Strategy import StrategyAbstract
from ParadoxTrading.Utils import DataStruct


class EngineAbstract:
    def __init__(
            self,
            _market_supply: MarketSupplyAbstract,
            _execution: ExecutionAbstract,
            _portfolio: PortfolioAbstract,
            _strategy: typing.Union[StrategyAbstract, typing.Iterable[StrategyAbstract]]
    ):
        self.event_queue: deque = deque()  # store event
        self.strategy_dict: typing.Dict[str, StrategyAbstract] = {}

        self.market_supply: MarketSupplyAbstract = None
        self.execution: ExecutionAbstract = None
        self.portfolio: PortfolioAbstract = None

        self._addMarketSupply(_market_supply)
        self._addExecution(_execution)
        self._addPortfolio(_portfolio)
        if isinstance(_strategy, StrategyAbstract):
            self._addStrategy(_strategy)
        else:
            for s in _strategy:
                self._addStrategy(s)

    def addEvent(self, _event: EventAbstract):
        """
        Add event into queue

        :param _event: MarketEvent, SignalEvent ...
        :return: None
        """
        assert isinstance(_event, EventAbstract)
        self.event_queue.append(_event)

    def _addMarketSupply(self, _market_supply: MarketSupplyAbstract):
        """
        set marketsupply
        
        :param _market_supply: 
        :return: 
        """
        assert self.market_supply is None

        self.market_supply = _market_supply
        _market_supply.setEngine(self)

    def _addExecution(self, _execution: ExecutionAbstract):
        """
        set execution

        :param _execution:
        :return:
        """
        assert self.execution is None

        self.execution = _execution
        _execution.setEngine(self)

    def _addPortfolio(self, _portfolio: PortfolioAbstract):
        """
        set portfolio

        :param _portfolio: _portfolio for this backtest
        :return:
        """
        assert self.portfolio is None

        self.portfolio = _portfolio
        _portfolio.setEngine(self)

    def _addStrategy(self, _strategy: StrategyAbstract):
        """
        Register strategy to engine

        :param _strategy: object
        :return: None
        """
        assert self.market_supply is not None
        assert self.portfolio is not None
        assert _strategy.name not in self.strategy_dict.keys()

        self.strategy_dict[_strategy.name] = _strategy
        _strategy.setEngine(self)

        self.market_supply.addStrategy(_strategy)
        self.portfolio.addStrategy(_strategy)

    def getTradingDay(self) -> str:
        """
        Return cur tradingday of market

        :return: str
        """
        return self.market_supply.getTradingDay()

    def getDatetime(self) -> typing.Union[None, datetime]:
        """
        Return latest datetime of market

        :return: datetime
        """
        return self.market_supply.getDatetime()

    def getSymbolList(self) -> typing.List[str]:
        """
        get the symbol list
        
        :return: 
        """
        return self.market_supply.getSymbolList()

    def getSymbolData(self, _symbol: str) -> DataStruct:
        """
        Return data

        :param _symbol:
        :return:
        """
        return self.market_supply.getSymbolData(_symbol)

    def run(self):
        raise NotImplementedError('run not implemented')
