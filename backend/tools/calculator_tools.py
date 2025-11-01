"""
Calculator Tools for financial calculations
Provides safe mathematical computation capabilities
"""

import re
from typing import Union


class CalculatorTools:
    """Tools for performing financial calculations"""

    @staticmethod
    def calculate(expression: str) -> str:
        """
        Safely evaluate a mathematical expression

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Result of the calculation as a string

        Examples:
            >>> calculate("100 * 1.5")
            "150.0"
            >>> calculate("(1000 + 500) / 2")
            "750.0"
        """
        try:
            # Remove any non-mathematical characters for safety
            # Only allow numbers, operators, parentheses, and decimal points
            safe_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression)

            # Evaluate the expression
            result = eval(safe_expr, {"__builtins__": {}}, {})

            return str(result)
        except Exception as e:
            return f"Calculation error: {str(e)}"

    @staticmethod
    def percentage(value: float, total: float) -> str:
        """
        Calculate percentage

        Args:
            value: The value
            total: The total

        Returns:
            Percentage as a string
        """
        try:
            if total == 0:
                return "Error: Division by zero"
            pct = (value / total) * 100
            return f"{pct:.2f}%"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def growth_rate(initial: float, final: float) -> str:
        """
        Calculate growth rate between two values

        Args:
            initial: Initial value
            final: Final value

        Returns:
            Growth rate as a percentage string
        """
        try:
            if initial == 0:
                return "Error: Initial value cannot be zero"
            growth = ((final - initial) / initial) * 100
            return f"{growth:.2f}%"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def compound_annual_growth_rate(initial: float, final: float, years: float) -> str:
        """
        Calculate CAGR (Compound Annual Growth Rate)

        Args:
            initial: Initial value
            final: Final value
            years: Number of years

        Returns:
            CAGR as a percentage string
        """
        try:
            if initial <= 0 or years <= 0:
                return "Error: Initial value and years must be positive"
            cagr = (pow(final / initial, 1 / years) - 1) * 100
            return f"{cagr:.2f}%"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def pe_ratio(price: float, earnings_per_share: float) -> str:
        """
        Calculate Price-to-Earnings ratio

        Args:
            price: Stock price
            earnings_per_share: Earnings per share

        Returns:
            P/E ratio as a string
        """
        try:
            if earnings_per_share == 0:
                return "N/A (EPS is zero)"
            pe = price / earnings_per_share
            return f"{pe:.2f}"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def price_to_book(price: float, book_value_per_share: float) -> str:
        """
        Calculate Price-to-Book ratio

        Args:
            price: Stock price
            book_value_per_share: Book value per share

        Returns:
            P/B ratio as a string
        """
        try:
            if book_value_per_share == 0:
                return "N/A (Book value is zero)"
            pb = price / book_value_per_share
            return f"{pb:.2f}"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def return_on_equity(net_income: float, shareholder_equity: float) -> str:
        """
        Calculate Return on Equity

        Args:
            net_income: Net income
            shareholder_equity: Shareholder equity

        Returns:
            ROE as a percentage string
        """
        try:
            if shareholder_equity == 0:
                return "N/A (Equity is zero)"
            roe = (net_income / shareholder_equity) * 100
            return f"{roe:.2f}%"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def debt_to_equity(total_debt: float, total_equity: float) -> str:
        """
        Calculate Debt-to-Equity ratio

        Args:
            total_debt: Total debt
            total_equity: Total equity

        Returns:
            D/E ratio as a string
        """
        try:
            if total_equity == 0:
                return "N/A (Equity is zero)"
            de = total_debt / total_equity
            return f"{de:.2f}"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def dividend_yield(annual_dividend: float, price: float) -> str:
        """
        Calculate dividend yield

        Args:
            annual_dividend: Annual dividend per share
            price: Current stock price

        Returns:
            Dividend yield as a percentage string
        """
        try:
            if price == 0:
                return "N/A (Price is zero)"
            div_yield = (annual_dividend / price) * 100
            return f"{div_yield:.2f}%"
        except Exception as e:
            return f"Error: {str(e)}"
