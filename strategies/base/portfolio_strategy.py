"""
Portfolio Strategy Base Class

Portfolio mode strategy where ONE Cerebro instance manages ALL stocks in a SINGLE account.

Key Difference from single-stock strategy:
- Single: One stock per Cerebro, one strategy instance
- Portfolio: All stocks in ONE Cerebro, strategy walks ALL stocks daily

Usage:
    class MyPortfolioStrategy(PortfolioStrategy):
        def calculate_score(self, data) -> float:
            # Calculate score for each stock
            return score

    # Cerebro setup for portfolio mode:
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MyPortfolioStrategy, threshold=8.0)

    # Add ALL stocks to single Cerebro
    for code in stock_codes:
        data = bt.feeds.PandasData(dataname=df_dict[code])
        cerebro.adddata(data, name=code)

    # Single account manages all stocks
    cerebro.run()
"""
import backtrader as bt
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class PortfolioStrategy(bt.Strategy):
    """
    Portfolio Strategy Base Class

    One Cerebro instance manages all stocks in a single account.
    The strategy walks ALL stocks daily to generate signals.

    Attributes:
        daily_values: List of portfolio daily values
        daily_signals: List of daily signal records [{date, signals: [(code, action, score), ...]}]
    """

    params = (
        ('threshold', 8.0),
        ('stop_loss_pct', 0.05),
        ('min_data_points', 60),
        ('max_positions', 10),
        ('debug_mode', False),
    )

    def __init__(self, **kwargs):
        self.daily_values = [self.broker.getvalue()]
        self.daily_dates = []
        self.daily_signals = []
        self._current_date = None
        self.pending_orders = {}

    def _get_current_date(self) -> datetime:
        """Get current bar date from first data"""
        if self._current_date is None and len(self.datas) > 0:
            self._current_date = self.datas[0].datetime.datetime(0)
        return self._current_date

    def next(self):
        """
        Main loop - Cerebro calls this DAILY

        Walks ALL stocks via self.datas to generate signals
        """
        self._current_date = self.datas[0].datetime.datetime(0) if len(self.datas) > 0 else None

        signals = []
        for data in self.datas:
            position = self.getposition(data)
            if position.size > 0:
                s1_score = self.calculate_s1_score(data)
                if s1_score > 10:
                    signals.append(('sell', data._name, s1_score))
                elif s1_score > 5:
                    signals.append(('sell_half', data._name, s1_score))
            else:
                score = self.calculate_score(data)
                if score >= self.params.threshold:
                    signals.append(('buy', data._name, score))

        self.execute_signals(signals)

        self.daily_values.append(self.broker.getvalue())
        self.daily_dates.append(self._current_date)

        self.daily_signals.append({
            'date': self._current_date,
            'signals': signals
        })

        if self.params.debug_mode and signals:
            print(f"{self._current_date} - Signals: {signals}")

    def calculate_score(self, data) -> float:
        """
        Calculate score for a single stock data feed.

        MUST be implemented by subclass.

        Args:
            data: Single stock data feed from self.datas

        Returns:
            float: Score for this stock
        """
        raise NotImplementedError("Subclass must implement calculate_score(data)")

    def calculate_s1_score(self, data) -> float:
        """
        Calculate S1 sell score for a single stock data feed.

        Default implementation returns 0 (no sell signal).
        Subclasses should override to implement actual sell logic.

        S1 >= 10: Full sell
        S1 >= 5: Half sell

        Args:
            data: Single stock data feed from self.datas

        Returns:
            float: S1 sell score
        """
        return 0.0

    def execute_signals(self, signals: List[Tuple[str, str, float]]):
        """
        Execute buy/sell signals based on available cash and positions.

        Default implementation: buy if cash allows, sell positions based on signals.

        Args:
            signals: List of (action, code, score) tuples
        """
        if not signals:
            return

        # Get available cash
        cash = self.broker.getcash()
        available_cash = cash * 0.95  # Keep 5% buffer

        for action, code, score in signals:
            if action == 'buy':
                # Find data by name
                data = self._get_data_by_name(code)
                if data is None:
                    continue

                # Check if already holding this stock
                position = self.getposition(data)
                if position.size > 0:
                    continue  # Already holding

                # Calculate position size
                price = data.close[0]
                if price <= 0:
                    continue

                size = self._calculate_position_size(price, cash)
                if size < 100:
                    continue

                # Execute buy
                self.buy(data=data, size=size)

                if self.params.debug_mode:
                    print(f"  BUY {code}: price={price:.2f}, size={size}, score={score:.2f}")

            elif action == 'sell':
                data = self._get_data_by_name(code)
                if data is None:
                    continue
                position = self.getposition(data)
                if position.size > 0:
                    self.close(data=data)
                    if self.params.debug_mode:
                        print(f"  SELL {code}: score={score:.2f}")

            elif action == 'sell_half':
                data = self._get_data_by_name(code)
                if data is None:
                    continue
                position = self.getposition(data)
                if position.size > 0:
                    half_size = position.size // 2
                    if half_size > 0:
                        self.close(data=data, size=half_size)
                        if self.params.debug_mode:
                            print(f"  SELL_HALF {code}: half_size={half_size}, score={score:.2f}")

    def _get_data_by_name(self, name: str) -> Optional[Any]:
        """Find data feed by name"""
        for data in self.datas:
            if data._name == name:
                return data
        return None

    def _calculate_position_size(self, price: float, cash: float) -> int:
        """
        Calculate position size based on available cash.

        Args:
            price: Current price
            cash: Available cash

        Returns:
            int: Number of shares to buy (in 100-share lots)
        """
        available_cash = cash * 0.95
        size = int(available_cash / price / 100) * 100
        return max(size, 100)

    def get_portfolio_value(self) -> List[float]:
        """Get portfolio daily values"""
        return self.daily_values

    def get_daily_values(self) -> List[float]:
        """Get daily values (alias for compatibility)"""
        return self.daily_values

    def get_daily_dates(self) -> List[datetime]:
        """Get daily dates"""
        return self.daily_dates

    def get_daily_signals(self) -> List[Dict]:
        """Get daily signals"""
        return self.daily_signals

    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """
        Calculate portfolio-level metrics from daily_values.

        Returns:
            Dict containing portfolio performance metrics
        """
        if len(self.daily_values) < 2:
            return {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'max_drawdown': 0.0,
                ' sharpe_ratio': 0.0
            }

        values = np.array(self.daily_values)
        initial_value = values[0]
        final_value = values[-1]

        # Total return
        total_return = (final_value - initial_value) / initial_value * 100

        # Calculate daily returns
        daily_returns = np.diff(values) / values[:-1]
        daily_returns = np.where(np.isfinite(daily_returns), daily_returns, 0)

        # Annualized return (252 trading days)
        n_days = len(values)
        annualized_return = ((final_value / initial_value) ** (252 / n_days) - 1) * 100 if n_days > 1 else 0

        # Max drawdown
        cummax = np.maximum.accumulate(values)
        drawdowns = (values - cummax) / cummax * 100
        max_drawdown = np.min(drawdowns)

        # Sharpe ratio (assuming 0.03 risk-free rate)
        if len(daily_returns) > 1 and np.std(daily_returns) > 0:
            sharpe_ratio = (np.mean(daily_returns) - 0.03 / 252) / np.std(daily_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0

        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'initial_value': initial_value,
            'final_value': final_value,
            'trading_days': n_days - 1
        }

    # =========================================
    # Position Management Helpers
    # =========================================

    def get_position_size(self, data) -> int:
        """Get current position size for a data feed"""
        position = self.getposition(data)
        return position.size if position else 0

    def get_position_avg_cost(self, data) -> float:
        """Get average cost for a position"""
        position = self.getposition(data)
        return position.price if position and position.size > 0 else 0.0

    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all current positions.

        Returns:
            Dict[code, {'size': int, 'avg_cost': float, 'current_value': float}]
        """
        positions = {}
        for data in self.datas:
            pos = self.getposition(data)
            if pos and pos.size > 0:
                positions[data._name] = {
                    'size': pos.size,
                    'avg_cost': pos.price,
                    'current_value': pos.size * data.close[0]
                }
        return positions

    def close_position(self, data) -> bool:
        """
        Close position for a specific data feed.

        Args:
            data: Data feed to close

        Returns:
            True if order submitted, False otherwise
        """
        position = self.getposition(data)
        if position and position.size > 0:
            self.close(data=data)
            return True
        return False

    def close_all_positions(self):
        """Close all positions"""
        for data in self.datas:
            self.close_position(data)