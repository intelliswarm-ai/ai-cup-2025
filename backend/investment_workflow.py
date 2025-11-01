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
        Perform comprehensive stock analysis

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

        # Stage 1: Research & Data Collection
        await self._update_progress(
            on_progress_callback,
            "Research Analyst",
            "🔍",
            "Gathering financial data and SEC filings..."
        )

        research_data = await self._research_stage(company_or_ticker)
        analysis_results["stages"].append({
            "stage": "research",
            "agent": "Research Analyst",
            "data": research_data
        })

        # Stage 2: Financial Analysis
        await self._update_progress(
            on_progress_callback,
            "Financial Analyst",
            "📊",
            "Analyzing financial metrics and valuation..."
        )

        financial_analysis = await self._financial_analysis_stage(
            company_or_ticker,
            research_data
        )
        analysis_results["stages"].append({
            "stage": "financial_analysis",
            "agent": "Financial Analyst",
            "data": financial_analysis
        })

        # Stage 3: Market Context
        await self._update_progress(
            on_progress_callback,
            "Market Strategist",
            "🌐",
            "Evaluating market conditions and trends..."
        )

        market_analysis = await self._market_analysis_stage(company_or_ticker)
        analysis_results["stages"].append({
            "stage": "market_analysis",
            "agent": "Market Strategist",
            "data": market_analysis
        })

        # Stage 4: Investment Recommendation
        await self._update_progress(
            on_progress_callback,
            "Chief Investment Officer",
            "💼",
            "Formulating investment recommendation..."
        )

        recommendation = await self._recommendation_stage(
            company_or_ticker,
            research_data,
            financial_analysis,
            market_analysis
        )
        analysis_results["stages"].append({
            "stage": "recommendation",
            "agent": "Chief Investment Officer",
            "data": recommendation
        })

        analysis_results["final_recommendation"] = recommendation
        return analysis_results

    async def _research_stage(self, company: str) -> Dict[str, Any]:
        """Stage 1: Research and data collection"""
        tasks = [
            self.search_tools.search_financial_data(company),
            self.sec_tools.get_10k(company),
            self.sec_tools.get_10q(company),
            self.browser_tools.get_company_website_info(company)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Store raw data
        raw_data = {
            "financial_search": str(results[0]) if not isinstance(results[0], Exception) else "N/A",
            "10k_filing": str(results[1]) if not isinstance(results[1], Exception) else "N/A",
            "10q_filing": str(results[2]) if not isinstance(results[2], Exception) else "N/A",
            "company_website": str(results[3]) if not isinstance(results[3], Exception) else "N/A",
        }

        # Use LLM to analyze and summarize the collected data
        prompt = f"""You are a Research Analyst analyzing data for {company}.

Review the following data collected from multiple sources:

FINANCIAL SEARCH RESULTS:
{raw_data['financial_search'][:1500]}

SEC 10-K FILING:
{raw_data['10k_filing'][:1500]}

SEC 10-Q FILING:
{raw_data['10q_filing'][:1500]}

COMPANY WEBSITE:
{raw_data['company_website'][:1000]}

Based on this data, provide a concise research summary covering:
1. Company overview and business model
2. Key financial metrics found
3. Recent developments or filings
4. Data quality and availability

Focus on extracting concrete facts and numbers. Keep your response under 500 words."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            summary = response.choices[0].message.content
        except Exception as e:
            summary = f"Research data collected for {company}. Analysis unavailable: {str(e)}"

        return {
            **raw_data,
            "summary": summary
        }

    async def _financial_analysis_stage(
        self,
        company: str,
        research_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stage 2: Financial analysis and valuation"""

        # Use LLM to analyze financial data from research
        prompt = f"""You are a Financial Analyst conducting a detailed financial analysis for {company}.

Using the research data collected:

RESEARCH SUMMARY:
{research_data.get('summary', 'N/A')}

FINANCIAL DATA:
{research_data.get('financial_search', 'N/A')[:1500]}

SEC FILINGS:
{research_data.get('10k_filing', 'N/A')[:1000]}
{research_data.get('10q_filing', 'N/A')[:1000]}

Provide a comprehensive financial analysis covering:

1. **Valuation Metrics**: Analyze P/E ratio, P/B ratio, EV/EBITDA, and other valuation multiples if available
2. **Financial Health**: Assess profitability (ROE, ROA, margins), liquidity ratios, and leverage
3. **Growth Analysis**: Evaluate revenue growth, earnings trends, and margin evolution
4. **Competitive Position**: How does the company's financial profile compare to peers?
5. **Key Financial Risks**: Identify any concerning trends in the numbers

Extract actual numbers where available. If specific metrics aren't found, note their absence.
Keep your analysis under 600 words and be specific with numbers."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            analysis_text = response.choices[0].message.content
        except Exception as e:
            analysis_text = f"Financial analysis unavailable: {str(e)}"

        return {
            "analysis": analysis_text,
            "data_sources": {
                "research_summary": len(research_data.get('summary', '')),
                "financial_search": len(research_data.get('financial_search', '')),
                "sec_filings": "10-K and 10-Q reviewed"
            }
        }

    async def _market_analysis_stage(self, company: str) -> Dict[str, Any]:
        """Stage 3: Market and competitive analysis"""

        # Search for recent news and market context
        news_results = await self.search_tools.search_news(company, days=30)

        # Use LLM to analyze market conditions
        prompt = f"""You are a Market Strategist analyzing the market environment for {company}.

Recent news and market information:
{news_results[:2000]}

Provide a market and competitive analysis covering:

1. **Market Sentiment**: What is the current sentiment around this company based on recent news?
2. **Industry Trends**: What sector-specific trends are affecting this company?
3. **Competitive Position**: How is the company positioned relative to competitors?
4. **Market Catalysts**: What upcoming events or factors could drive price movement?
5. **Risk Factors**: What market, sector, or company-specific risks should investors watch?

Be specific and cite information from the news when available.
Keep your analysis under 500 words."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            analysis_text = response.choices[0].message.content
        except Exception as e:
            analysis_text = f"Market analysis unavailable: {str(e)}"

        return {
            "analysis": analysis_text,
            "recent_news": news_results[:500],  # Store sample of news data
            "news_sources_count": news_results.count("http") if isinstance(news_results, str) else 0
        }

    async def _recommendation_stage(
        self,
        company: str,
        research: Dict[str, Any],
        financials: Dict[str, Any],
        market: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stage 4: Final investment recommendation"""

        # Generate comprehensive executive summary using all collected data
        prompt = f"""You are the Chief Investment Officer providing a final investment recommendation for {company}.

RESEARCH SUMMARY:
{research.get('summary', 'N/A')[:1000]}

FINANCIAL ANALYSIS:
{financials.get('analysis', 'N/A')[:1500]}

MARKET ANALYSIS:
{market.get('analysis', 'N/A')[:1000]}

Based on all the research, financial analysis, and market context, provide an **Executive Investment Recommendation** with:

1. **Investment Rating**: Choose one: STRONG BUY, BUY, HOLD, SELL, STRONG SELL
2. **Confidence Level**: HIGH, MEDIUM, or LOW (based on data quality and consistency)
3. **Investment Thesis** (3-5 key points):
   - Main strengths/bull case
   - Primary concerns/bear case
   - Key catalysts to watch

4. **Target Price & Valuation**: If sufficient data is available, provide a fair value estimate
5. **Risk Assessment**: Major risks investors should consider
6. **Action Items**: Specific next steps for investors

Be decisive but balanced. Support your recommendation with specific evidence from the analysis.
If data is insufficient for a strong opinion, acknowledge it clearly.
Keep your response under 700 words."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,  # Slightly higher for more nuanced recommendations
                max_tokens=1200
            )
            recommendation_text = response.choices[0].message.content
        except Exception as e:
            recommendation_text = f"Investment recommendation unavailable: {str(e)}"

        return {
            "company": company,
            "analysis_date": datetime.now().isoformat(),
            "executive_summary": recommendation_text,
            "data_quality": {
                "research_data_available": bool(research.get('summary')),
                "financial_analysis_available": bool(financials.get('analysis')),
                "market_analysis_available": bool(market.get('analysis')),
                "sources_consulted": [
                    "SEC Filings (10-K, 10-Q)",
                    "Financial News & Market Data",
                    "Company Website & Investor Relations",
                    "Industry Analysis"
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
