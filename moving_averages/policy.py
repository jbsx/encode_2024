from collections import deque
from decimal import Decimal
from typing import Any, List

import numpy as np 
import itertools

from dojo.actions.base_action import BaseAction
from dojo.actions.uniswapV3 import UniswapV3Trade
from dojo.agents import BaseAgent
from dojo.environments.uniswapV3 import UniswapV3Observation
from dojo.policies import BasePolicy


    
# SNIPPET 1 START
class MovingAveragePolicy(BasePolicy):  # type: ignore
    """Moving average trading policy for a UniswapV3Env with a single pool.

    :param agent: The agent which is using this policy.
    :param short_window: The short window length for the moving average.
    :param long_window: The long window length for the moving average.
    """

    def __init__(
        self, agent: BaseAgent, pool: str, short_window: int, long_window: int
    ) -> None:
        super().__init__(agent=agent)
        self.stop_loss = float('-inf')
        self._short_window_len: int = short_window
        self._long_window_len: int = long_window
        self.long_window: deque[float] = deque(maxlen=long_window)
        self.short_window: deque[float] = deque(maxlen=short_window)
        self.pool: str = pool

    # SNIPPET 1 END

    def _clear_windows(self) -> None:
        self.long_window = deque(maxlen=self._long_window_len)
        self.short_window = deque(maxlen=self._short_window_len)

    def exponential_moving_average(self, prices, N, period=30):
        ema = np.zeros(len(prices))
        l = list(itertools.islice(prices, 0, period))
        sma = sum(l)/len(l)
        ema[period-1] = sma
        w = 2/(N+1)
        for i in range(period, len(prices)):
            ema[i] = prices[i]*w + ema[i-1]*(1-w)
        return ema[-1]
        

    def _x_to_y_indicated(self, pool_tokens: tuple[str, str]) -> bool:
        """If the short window crosses above the long window, convert asset y to asset 4      x.

        Only do so if there are tokens left to trade.
        """
        return bool(
            self.exponential_moving_average(self.short_window, self._short_window_len) > self.exponential_moving_average(self.long_window, self._long_window_len)
            and self.agent.quantity(pool_tokens[1]) > 0
        )

    def _y_to_x_indicated(self, pool_tokens: tuple[str, str]) -> bool:
        """If the short window crosses below the long window, convert asset x to asset
        y.

        Only do so if there are tokens left to trade.
        """
        return bool(
            self.exponential_moving_average(self.short_window, self._short_window_len) < self.exponential_moving_average(self.long_window, self._long_window_len)
            and self.agent.quantity(pool_tokens[0]) > 0
        )

    def predict(self, obs: UniswapV3Observation) -> List[BaseAction[Any]]:
        """Make a trade if the mean of the short window crosses the mean of the long
        window."""
        pool_tokens = obs.pool_tokens(pool=self.pool)
        price = obs.price(token=pool_tokens[0], unit=pool_tokens[1], pool=self.pool)
        self.short_window.append(float(price))
        self.long_window.append(float(price))
        obs.add_signal(
            "LongShortDiff",
            float(np.mean(self.short_window) - np.mean(self.long_window)),
        )
        obs.add_signal(
            "portfolio_value",
            float(self.agent.quantity(pool_tokens[1])),
        )

        # Only start trading when the windows are full
        if len(self.short_window) < self._short_window_len:
            obs.add_signal("Locked", float(True))
            return []
        if len(self.long_window) < self._long_window_len:
            obs.add_signal("Locked", float(True))
            return []
        obs.add_signal("Locked", float(False))

        # Sell if price lower than or equal to stop loss
        if price <= self.stop_loss:
            x_quantity = self.agent.quantity(pool_tokens[0])
            self._clear_windows()
            self.stop_loss = float('-inf')
            return [
                UniswapV3Trade(
                    agent=self.agent,
                    pool=self.pool,
                    quantities=(x_quantity, Decimal(0)),
                )
            ]

        # SNIPPET 2 START
        if self._x_to_y_indicated(pool_tokens):
            y_quantity = self.agent.quantity(pool_tokens[1])
            self._clear_windows()
            self.stop_loss = price * Decimal(0.95)
            return [
                UniswapV3Trade(
                    agent=self.agent,
                    pool=self.pool,
                    quantities=(Decimal(0), y_quantity),
                )
            ]
        # SNIPPET 2 END

        if self._y_to_x_indicated(pool_tokens):
            x_quantity = self.agent.quantity(pool_tokens[0])
            self._clear_windows()
            self.stop_loss = float('-inf')
            return [
                UniswapV3Trade(
                    agent=self.agent,
                    pool=self.pool,
                    quantities=(x_quantity, Decimal(0)),
                )
            ]
        return []
