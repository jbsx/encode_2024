import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from datetime import timedelta
from decimal import Decimal
from typing import Any, Optional

from agents.uniswapV3_pool_wealth import UniswapV3PoolWealthAgent
from dateutil import parser as dateparser
from policy import OneTradePolicy

from dojo.common.constants import Chain
from dojo.environments import UniswapV3Env
from dojo.runners import backtest_run


def main(
    *,
    dashboard_server_port: Optional[int],
    simulation_status_bar: bool,
    auto_close: bool,
    run_length: timedelta = timedelta(minutes=10),
    **kwargs: dict[str, Any]
) -> None:
    pools = ["USDC/WETH-0.05"]
    start_time = dateparser.parse("2021-06-21 00:00:00 UTC")
    end_time = start_time + run_length

    # Agents
    one_agent = UniswapV3PoolWealthAgent(
        initial_portfolio={
            "USDC": Decimal(10000),
            "WETH": Decimal(0),
        },
        name="OneTrade_Agent",
    )

    # Simulation environment (Uniswap V3)
    env = UniswapV3Env(
        chain=Chain.ETHEREUM,
        date_range=(start_time, end_time),
        agents=[one_agent],
        pools=pools,
        backend_type="forked",
        market_impact="replay",
    )

    # Policies
    ontrd_policy = OneTradePolicy(agent=one_agent)

    backtest_run(
        env=env,
        policies=[ontrd_policy],
        dashboard_server_port=dashboard_server_port,
        output_file="one_trade.db",
        auto_close=auto_close,
        simulation_status_bar=simulation_status_bar,
        simulation_title="OneTrade",
        simulation_description="Trading Once",
    )


if __name__ == "__main__":
    main(
        dashboard_server_port=8768,
        simulation_status_bar=True,
        auto_close=False,
        run_length=timedelta(hours=2),
    )
