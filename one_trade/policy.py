from decimal import Decimal
from typing import List, Tuple, Union

from dojo.actions.base_action import BaseAction
from dojo.actions.uniswapV3 import UniswapV3Trade
from dojo.agents import BaseAgent
from dojo.observations.uniswapV3 import UniswapV3Observation
from dojo.policies import BasePolicy


# SNIPPET 1 START
class OneTradePolicy(BasePolicy):  # type: ignore
    """One Trade trading policy for a UniswapV3Env

    :param agent: The agent which is using this policy.
    """

    def __init__(self, agent: BaseAgent) -> None:
        super().__init__(agent=agent)
        self.one_trade = True

    def predict(self, obs: UniswapV3Observation) -> List[BaseAction]:  # type: ignore
        # Make first trade
        if self.one_trade:
            self.one_trade = False
            pool = obs.pools[0]
            return [
                UniswapV3Trade(
                    agent=self.agent,
                    pool=pool,
                    quantities=(Decimal(0), Decimal(1)),
                )
            ]
        else:
            return []
