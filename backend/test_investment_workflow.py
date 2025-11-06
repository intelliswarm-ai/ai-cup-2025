"""
Test script for investment workflow
Run manually to test stock analysis
"""

import asyncio
import sys
from investment_workflow import investment_workflow


async def test_stock_analysis(company: str):
    """
    Test the investment workflow with a specific company/ticker

    Args:
        company: Company name or ticker symbol (e.g., 'AAPL', 'Tesla', 'Microsoft')
    """
    print(f"\n{'='*80}")
    print(f"INVESTMENT ANALYSIS TEST FOR: {company}")
    print(f"{'='*80}\n")

    # Progress callback to show real-time updates
    async def progress_callback(update):
        print(f"\n[{update['icon']} {update['role']}]")
        if update.get('is_progress'):
            print(f"Status: {update['text']}")
        else:
            print(update['text'])
        print("-" * 80)

    try:
        # Run the analysis
        print("Starting comprehensive stock analysis...\n")
        results = await investment_workflow.analyze_stock(
            company,
            on_progress_callback=progress_callback
        )

        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE!")
        print(f"{'='*80}\n")

        # Print summary
        print(f"Company: {results['company']}")
        print(f"Analysis Date: {results['timestamp']}")
        print(f"Total Stages: {len(results['stages'])}")
        print("\nStages completed:")
        for stage in results['stages']:
            print(f"  ✓ {stage['stage']} (Agent: {stage['agent']})")

        # Print final recommendation
        if results.get('final_recommendation'):
            print(f"\n{'='*80}")
            print("FINAL RECOMMENDATION")
            print(f"{'='*80}")
            rec = results['final_recommendation']
            print(f"\n{rec.get('executive_summary', 'N/A')}")

        return results

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function"""
    # Default to AAPL if no argument provided
    if len(sys.argv) > 1:
        company = sys.argv[1]
    else:
        # Interactive mode
        print("\n" + "="*80)
        print("INVESTMENT WORKFLOW TEST")
        print("="*80)
        print("\nEnter a company name or stock ticker to analyze.")
        print("Examples: AAPL, Tesla, Microsoft, NVDA, TSLA")
        print("-"*80)
        company = input("\nCompany/Ticker: ").strip()

        if not company:
            print("❌ No company provided. Exiting.")
            return

    # Run the test
    await test_stock_analysis(company)


if __name__ == "__main__":
    # Run the async test
    asyncio.run(main())
