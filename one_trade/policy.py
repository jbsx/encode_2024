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
        pool = obs.pools[0]
        #Trade only once
        if self.one_trade:
            self.one_trade = False
            quantities = [self.agent.quantity(obs.pool_tokens(pool)[0]), self.agent.quantity(obs.pool_tokens(pool)[1])]
            if self.agent.quantity(obs.pool_tokens(pool)[1]) != 0:
                #If you own WETH, trade all WETH for USDC
                return [
                    UniswapV3Trade(
                        agent=self.agent,
                        pool=pool,
                        quantities=(Decimal(0), max(quantities)),
                    )
                ]
            else:
                #If you do not own WETH, trade 1 USDC for WETH
                return [
                    UniswapV3Trade(
                        agent=self.agent,
                        pool=pool,
                        quantities=(Decimal(1), Decimal(0)),
                    )
                ]
        else:
            #If you own WETH, trade all WETH for USDC
            if self.agent.quantity(obs.pool_tokens(pool)[1]) != 0:
                return [
                    UniswapV3Trade(
                        agent=self.agent,
                        pool=pool,
                        quantities=(Decimal(0), Decimal(self.agent.quantity("WETH"))),
                    )
                ]
            else:
                return []
