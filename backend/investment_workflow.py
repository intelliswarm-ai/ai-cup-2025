"""
Investment Research Workflow
Specialized workflow for stock analysis using research tools
Based on crewAI stock_analysis pattern
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import AsyncOpenAI

from tools import BrowserTools, SearchTools, CalculatorTools, SECTools


class InvestmentResearchWorkflow:
    """
    Orchestrates investment research using specialized tools and agents
    """

    def __init__(self):
        self.browser_tools = BrowserTools()
        self.search_tools = SearchTools()
        self.calculator_tools = CalculatorTools()
        self.sec_tools = SECTools()

        # Initialize OpenAI for data analysis
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def analyze_stock(
        self,
        company_or_ticker: str,
        on_progress_callback=None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive stock analysis following CrewAI pattern

        Args:
            company_or_ticker: Company name or stock ticker
            on_progress_callback: Optional callback for progress updates

        Returns:
            Complete analysis results
        """
        analysis_results = {
            "company": company_or_ticker,
            "timestamp": datetime.now().isoformat(),
            "stages": []
        }

        # Task 1: Financial Analysis
        # Evaluate financial health via P/E ratio, EPS growth, revenue trends, and debt-to-equity metrics
        await self._update_progress(
            on_progress_callback,
            "Financial Analyst",
            "📊",
            "Analyzing financial health and performance metrics..."
        )

        financial_analysis = await self._financial_analysis_task(company_or_ticker)
        analysis_results["stages"].append({
            "stage": "financial_analysis",
            "agent": "Financial Analyst",
            "data": financial_analysis
        })

        # Task 2: Research
        # Compile recent news, press releases, and market analyses
        await self._update_progress(
            on_progress_callback,
            "Research Analyst",
            "🔍",
            "Compiling recent news and market sentiment..."
        )

        research_data = await self._research_task(company_or_ticker)
        analysis_results["stages"].append({
            "stage": "research",
            "agent": "Research Analyst",
            "data": research_data
        })

        # Task 3: Filings Analysis
        # Review latest 10-Q and 10-K EDGAR filings
        await self._update_progress(
            on_progress_callback,
            "Filings Analyst",
            "📋",
            "Reviewing SEC filings (10-K and 10-Q)..."
        )

        filings_analysis = await self._filings_analysis_task(company_or_ticker)
        analysis_results["stages"].append({
            "stage": "filings_analysis",
            "agent": "Filings Analyst",
            "data": filings_analysis
        })

        # Task 4: Recommendation
        # Synthesize all analyses into unified investment guidance
        await self._update_progress(
            on_progress_callback,
            "Investment Advisor",
            "💼",
            "Formulating final investment recommendation..."
        )

        recommendation = await self._recommendation_task(
            company_or_ticker,
            financial_analysis,
            research_data,
            filings_analysis
        )
        analysis_results["stages"].append({
            "stage": "recommendation",
            "agent": "Investment Advisor",
            "data": recommendation
        })

        analysis_results["final_recommendation"] = recommendation
        return analysis_results

    async def _financial_analysis_task(self, company: str) -> Dict[str, Any]:
        """
        Task 1: Financial Analysis
        Evaluate financial health via P/E ratio, EPS growth, revenue trends, and debt-to-equity metrics.
        Compare performance against industry peers and market trends.
        """
        # Gather financial data
        tasks = [
            self.search_tools.search_financial_data(company),
            self.browser_tools.get_company_website_info(company)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        financial_search = str(results[0]) if not isinstance(results[0], Exception) else "N/A"
        company_website = str(results[1]) if not isinstance(results[1], Exception) else "N/A"

        # Use LLM to perform financial analysis
        prompt = f"""You are a Financial Analyst evaluating {company}'s financial health.

FINANCIAL DATA AVAILABLE:
{financial_search[:2000]}

COMPANY INFORMATION:
{company_website[:1000]}

Task: Evaluate {company}'s financial health and provide a clear assessment.

Your analysis should cover:

1. **Valuation Metrics**: Analyze P/E ratio, price-to-book ratio, EV/EBITDA if available
2. **Growth Metrics**: Evaluate EPS growth, revenue growth trends, margin evolution
3. **Financial Health**: Assess debt-to-equity ratio, current ratio, interest coverage
4. **Profitability**: Analyze ROE, ROA, profit margins
5. **Competitive Positioning**: How does the company compare to industry peers?
6. **Key Strengths**: What are the financial strengths?
7. **Key Weaknesses**: What are the concerning financial indicators?

Expected Output: A clear assessment of the stock's financial standing, its strengths and weaknesses, and competitive positioning.

Use specific numbers and metrics where available. Keep your analysis under 600 words."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            analysis = response.choices[0].message.content
        except Exception as e:
            analysis = f"Financial analysis unavailable: {str(e)}"

        return {
            "analysis": analysis,
            "data_sources": ["Financial search results", "Company website"]
        }

    async def _research_task(self, company: str) -> Dict[str, Any]:
        """
        Task 2: Research
        Compile recent news, press releases, and market analyses.
        Highlight significant events, market sentiment shifts, and analyst perspectives.
        """
        # Search for recent news and market information
        news_results = await self.search_tools.search_news(company, days=30)

        # Use LLM to compile and analyze research
        prompt = f"""You are a Research Analyst compiling recent news and market analyses for {company}.

RECENT NEWS AND MARKET DATA:
{news_results[:2500]}

Task: Compile a comprehensive summary of latest news, press releases, and market analyses for {company}.

Your summary should include:

1. **Recent Developments**: What are the most significant recent events or announcements?
2. **Market Sentiment**: What is the overall market sentiment toward the company? Any notable shifts?
3. **Analyst Perspectives**: What are financial analysts saying about the company?
4. **Upcoming Events**: Are there upcoming earnings dates, product launches, or other catalysts?
5. **Press Releases**: Any important company announcements or news?
6. **Potential Impact**: How might these developments impact the stock?

Expected Output: A comprehensive summary of latest developments with notable shifts in market sentiment and potential stock impacts.

Be specific with dates and sources where available. Keep your summary under 600 words."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            summary = response.choices[0].message.content
        except Exception as e:
            summary = f"Research compilation unavailable: {str(e)}"

        return {
            "summary": summary,
            "news_sources_count": news_results.count("http") if isinstance(news_results, str) else 0
        }

    async def _filings_analysis_task(self, company: str) -> Dict[str, Any]:
        """
        Task 3: Filings Analysis
        Review latest 10-Q and 10-K EDGAR filings.
        Extract insights from Management Discussion & Analysis, financial statements,
        insider transactions, and disclosed risk factors.
        """
        # Gather SEC filings
        tasks = [
            self.sec_tools.get_10k(company),
            self.sec_tools.get_10q(company)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        filing_10k = str(results[0]) if not isinstance(results[0], Exception) else "N/A"
        filing_10q = str(results[1]) if not isinstance(results[1], Exception) else "N/A"

        # Use LLM to analyze SEC filings
        prompt = f"""You are a Filings Analyst reviewing SEC EDGAR filings for {company}.

LATEST 10-K FILING:
{filing_10k[:2000]}

LATEST 10-Q FILING:
{filing_10q[:2000]}

Task: Review the latest 10-Q and 10-K EDGAR filings and extract key insights.

Your analysis should cover:

1. **Management Discussion & Analysis (MD&A)**: What are management's key points about business performance and outlook?
2. **Financial Statements**: What do the balance sheet, income statement, and cash flow reveal?
3. **Risk Factors**: What are the disclosed risk factors that could impact the business?
4. **Insider Transactions**: Any notable insider buying or selling activity?
5. **Red Flags**: Identify any concerning findings or warning signs
6. **Positive Indicators**: Highlight positive signals that could drive future performance

Expected Output: An expanded report identifying significant findings, emphasizing red flags and positive indicators affecting future performance.

Be specific with numbers and sections. Keep your analysis under 700 words."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1200
            )
            analysis = response.choices[0].message.content
        except Exception as e:
            analysis = f"Filings analysis unavailable: {str(e)}"

        return {
            "analysis": analysis,
            "filings_reviewed": {
                "10k_available": "N/A" not in filing_10k and len(filing_10k) > 100,
                "10q_available": "N/A" not in filing_10q and len(filing_10q) > 100
            }
        }

    async def _recommendation_task(
        self,
        company: str,
        financial_analysis: Dict[str, Any],
        research: Dict[str, Any],
        filings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Task 4: Recommendation
        Synthesize Financial Analysis, Research, and Filings analyses into unified investment guidance.
        Incorporate financial metrics, sentiment data, EDGAR insights, insider activity, and upcoming events.
        """
        # Generate comprehensive investment recommendation
        prompt = f"""You are an Investment Advisor providing a final investment recommendation for {company}.

FINANCIAL ANALYSIS (Task 1):
{financial_analysis.get('analysis', 'N/A')[:1500]}

RESEARCH SUMMARY (Task 2):
{research.get('summary', 'N/A')[:1500]}

FILINGS ANALYSIS (Task 3):
{filings.get('analysis', 'N/A')[:1500]}

Task: Synthesize all analyses into unified investment guidance.

Your recommendation must include:

1. **Investment Stance**: Clear recommendation (STRONG BUY, BUY, HOLD, SELL, or STRONG SELL)

2. **Supporting Evidence**: Key findings from:
   - Financial metrics (P/E, EPS growth, debt levels, etc.)
   - Market sentiment and recent news
   - SEC filings insights and risk factors
   - Insider activity if mentioned

3. **Investment Strategy**:
   - Entry points and price targets if appropriate
   - Time horizon (short-term, medium-term, long-term)
   - Position sizing recommendations

4. **Risk/Reward Assessment**:
   - Key upside drivers
   - Primary downside risks
   - Risk mitigation strategies

5. **Upcoming Events to Watch**:
   - Earnings dates
   - Product launches
   - Regulatory decisions

Expected Output: A full super detailed report delivering clear investment stance and strategy with supporting evidence, professionally formatted for client presentation.

Be decisive and specific. This is for an important client who expects actionable guidance.
Keep your response under 800 words."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1400
            )
            recommendation_text = response.choices[0].message.content
        except Exception as e:
            recommendation_text = f"Investment recommendation unavailable: {str(e)}"

        return {
            "company": company,
            "analysis_date": datetime.now().isoformat(),
            "executive_summary": recommendation_text,
            "data_quality": {
                "financial_analysis_available": bool(financial_analysis.get('analysis')),
                "research_available": bool(research.get('summary')),
                "filings_available": bool(filings.get('analysis')),
                "sources_consulted": [
                    "SEC Filings (10-K, 10-Q)",
                    "Financial News & Market Data",
                    "Company Website & Financial Search",
                    "Market Sentiment Analysis"
                ]
            }
        }

    async def _update_progress(
        self,
        callback,
        agent: str,
        icon: str,
        message: str
    ):
        """Send progress update via callback"""
        if callback:
            await callback({
                "role": agent,
                "icon": icon,
                "text": message,
                "timestamp": datetime.now().isoformat(),
                "is_progress": True
            })


# Global instance
investment_workflow = InvestmentResearchWorkflow()
