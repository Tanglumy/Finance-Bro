#!/usr/bin/env python3
"""
Final Demo: Finance-Bro Deep Research Report Generation
Showcase the complete research workflow with detailed output.
"""

import asyncio
import json
from datetime import datetime
from research_report_generator import DeepResearchReportGenerator

async def generate_showcase_report():
    """Generate a showcase research report"""
    
    print("🎯 Finance-Bro Deep Research Report Generation")
    print("🔬 Comprehensive Equity Research Showcase")
    print("="*70)
    
    generator = DeepResearchReportGenerator()
    
    # Test with Tesla - a volatile, high-interest stock
    symbol = "TSLA"
    
    print(f"📊 Generating comprehensive research report for Tesla Inc. ({symbol})")
    print("⏳ This process involves:")
    print("   • Real-time financial data collection")
    print("   • OpenAI GPT-4 analysis and report writing") 
    print("   • Peer comparison analysis")
    print("   • Investment recommendation generation")
    print("   • Risk assessment and price target calculation")
    
    start_time = datetime.now()
    
    try:
        report = await generator.generate_research_report(symbol, "comprehensive")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Research Report Generated Successfully!")
        print(f"⏱️  Generation Time: {duration:.1f} seconds")
        print(f"📄 Report Length: {report['word_count']} words")
        
        # Display key metrics
        print(f"\n{'='*70}")
        print("📈 INVESTMENT SUMMARY")
        print(f"{'='*70}")
        print(f"Company: {report['company_name']}")
        print(f"Symbol: {report['symbol']}")
        print(f"Analyst Rating: {report['analyst_rating']} ⭐")
        print(f"Current Price: ${report['current_price']:.2f}")
        print(f"Price Target: ${report['price_target']:.2f}")
        print(f"Upside Potential: {report['upside_potential']:+.1f}%")
        print(f"Report Date: {datetime.fromisoformat(report['report_date']).strftime('%B %d, %Y')}")
        
        # Display key financial metrics
        print(f"\n{'='*70}")
        print("💰 KEY FINANCIAL METRICS")
        print(f"{'='*70}")
        metrics = report['key_metrics']
        print(f"Market Cap: ${metrics['market_cap']:,.0f}")
        print(f"P/E Ratio: {metrics['pe_ratio']:.1f}")
        print(f"EPS (Forward): ${metrics['eps']:.2f}")
        print(f"Profit Margin: {metrics['profit_margin']*100:.1f}%")
        print(f"Return on Equity: {metrics['roe']*100:.1f}%")
        print(f"Debt-to-Equity: {metrics['debt_to_equity']:.2f}")
        print(f"Beta: {metrics['beta']:.2f}")
        print(f"YTD Performance: {metrics['ytd_performance']:+.1f}%")
        
        # Display investment highlights
        print(f"\n{'='*70}")
        print("🎯 INVESTMENT HIGHLIGHTS")
        print(f"{'='*70}")
        highlights = report['investment_highlights']
        print(highlights)
        
        # Display peer comparison
        print(f"\n{'='*70}")
        print("🏢 PEER COMPARISON")
        print(f"{'='*70}")
        peers = report['peer_comparison']
        print(f"{'Company':<8} {'P/E':<8} {'Margin':<8} {'ROE':<8}")
        print("-" * 35)
        print(f"{symbol:<8} {metrics['pe_ratio']:<8.1f} {metrics['profit_margin']*100:<8.1f}% {metrics['roe']*100:<8.1f}%")
        for peer, data in peers.items():
            print(f"{peer:<8} {data['pe_ratio']:<8.1f} {data['profit_margin']*100:<8.1f}% {data['roe']*100:<8.1f}%")
        
        # Display full report preview
        print(f"\n{'='*70}")
        print("📋 FULL RESEARCH REPORT")
        print(f"{'='*70}")
        full_report = report['full_report']
        # Show first 1500 characters for preview
        preview_length = 1500
        if len(full_report) > preview_length:
            print(full_report[:preview_length] + "...")
            print(f"\n[Report continues for {len(full_report) - preview_length} more characters...]")
        else:
            print(full_report)
        
        # Save the report
        filename = f"tesla_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n{'='*70}")
        print("💾 REPORT SAVED")
        print(f"{'='*70}")
        print(f"Full report saved to: {filename}")
        print("✅ Ready for investment decision making!")
        
        return report
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return None

async def main():
    """Main demo function"""
    report = await generate_showcase_report()
    
    if report:
        print(f"\n🚀 Finance-Bro Deep Research: MISSION COMPLETE")
        print("📊 Successfully generated institutional-quality equity research report")
        print("🎯 Features demonstrated:")
        print("   ✅ Real-time financial data integration")
        print("   ✅ OpenAI GPT-4 powered analysis")
        print("   ✅ Professional investment recommendations")
        print("   ✅ Comprehensive peer comparison")
        print("   ✅ Risk assessment and price targets")
        print("   ✅ Ready for production use")

if __name__ == "__main__":
    asyncio.run(main())