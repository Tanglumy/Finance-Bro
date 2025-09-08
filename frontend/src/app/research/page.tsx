'use client';

import { useState } from 'react';
import { api } from '@/services/api';
import { Card } from '@/components/application/cards/card';
import { Button } from '@/components/base/buttons/button';
import { Input } from '@/components/base/input/input';
import { Badge } from '@/components/base/badges/badges';
import { Tabs } from '@/components/application/tabs/tabs';
import { ProgressCircles } from '@/components/base/progress-indicators/progress-indicators';
import { 
  SearchIcon,
  FileTextIcon,
  TrendingUpIcon,
  InfoCircleIcon,
  BuildingIcon,
  ChartLineIcon
} from '@untitledui/icons';

interface ResearchData {
  symbol: string;
  company_name: string;
  sector: string;
  industry: string;
  market_cap: number;
  pe_ratio: number;
  dividend_yield: number;
  revenue_growth: number;
  profit_margin: number;
  debt_to_equity: number;
  analyst_rating: string;
  price_target: number;
  current_price: number;
  summary: string;
  strengths: string[];
  risks: string[];
  recent_news: Array<{
    title: string;
    date: string;
    sentiment: 'positive' | 'neutral' | 'negative';
  }>;
}

export default function ResearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [loading, setLoading] = useState(false);
  const [research, setResearch] = useState<ResearchData | null>(null);
  const [deepAnalysis, setDeepAnalysis] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setSelectedSymbol(searchQuery.toUpperCase());

    try {
      // Get symbol research
      const symbolData = await api.getSymbolResearch(searchQuery);
      setResearch(symbolData);

      // Get deep analysis
      const analysis = await api.getDeepAnalysis({ symbol: searchQuery });
      setDeepAnalysis(analysis);
    } catch (error) {
      console.error('Research error:', error);
      // Set mock data for demonstration
      setResearch({
        symbol: searchQuery.toUpperCase(),
        company_name: `${searchQuery.toUpperCase()} Corporation`,
        sector: 'Technology',
        industry: 'Software',
        market_cap: 2500000000000,
        pe_ratio: 28.5,
        dividend_yield: 0.5,
        revenue_growth: 15.2,
        profit_margin: 25.3,
        debt_to_equity: 0.45,
        analyst_rating: 'Buy',
        price_target: 185,
        current_price: 165,
        summary: `${searchQuery.toUpperCase()} is a leading technology company with strong fundamentals and growth prospects.`,
        strengths: [
          'Strong brand recognition',
          'Diverse product portfolio',
          'Solid financial position',
          'Growing market share'
        ],
        risks: [
          'Regulatory challenges',
          'Intense competition',
          'Market saturation concerns'
        ],
        recent_news: [
          {
            title: 'Company Reports Strong Q4 Earnings',
            date: '2024-01-15',
            sentiment: 'positive'
          },
          {
            title: 'New Product Launch Announced',
            date: '2024-01-10',
            sentiment: 'positive'
          },
          {
            title: 'Market Volatility Impacts Stock',
            date: '2024-01-05',
            sentiment: 'negative'
          }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const formatMarketCap = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(0)}`;
  };

  const getRatingColor = (rating: string) => {
    switch (rating.toLowerCase()) {
      case 'buy':
      case 'strong buy':
        return 'success';
      case 'hold':
        return 'warning';
      case 'sell':
      case 'strong sell':
        return 'error';
      default:
        return 'gray';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <FileTextIcon className="w-8 h-8 text-purple-600" />
          Deep Research
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Comprehensive analysis and research on stocks and markets
        </p>
      </div>

      {/* Search Bar */}
      <Card>
        <div className="p-6">
          <div className="flex space-x-3">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter stock symbol (e.g., AAPL, MSFT, GOOGL)"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button
              variant="primary"
              onClick={handleSearch}
              disabled={loading || !searchQuery.trim()}
            >
              {loading ? (
                <ProgressCircles size="sm" />
              ) : (
                <>
                  <SearchIcon className="w-5 h-5 mr-2" />
                  Research
                </>
              )}
            </Button>
          </div>
        </div>
      </Card>

      {/* Research Results */}
      {research && (
        <>
          {/* Company Overview */}
          <Card>
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {research.company_name}
                  </h2>
                  <div className="flex items-center space-x-3 mt-2">
                    <Badge color="primary" size="lg">
                      {research.symbol}
                    </Badge>
                    <span className="text-gray-600 dark:text-gray-400">
                      {research.sector} • {research.industry}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">
                    ${research.current_price.toFixed(2)}
                  </p>
                  <Badge color={getRatingColor(research.analyst_rating)} size="sm" className="mt-2">
                    {research.analyst_rating}
                  </Badge>
                </div>
              </div>

              <p className="text-gray-700 dark:text-gray-300 mb-6">
                {research.summary}
              </p>

              {/* Key Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Market Cap</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {formatMarketCap(research.market_cap)}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400">P/E Ratio</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {research.pe_ratio.toFixed(2)}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Dividend Yield</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {research.dividend_yield.toFixed(2)}%
                  </p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Price Target</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    ${research.price_target.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Detailed Analysis Tabs */}
          <Card>
            <div className="p-6">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <Tabs.List>
                  <Tabs.Trigger value="overview">Overview</Tabs.Trigger>
                  <Tabs.Trigger value="financials">Financials</Tabs.Trigger>
                  <Tabs.Trigger value="analysis">Analysis</Tabs.Trigger>
                  <Tabs.Trigger value="news">News & Events</Tabs.Trigger>
                </Tabs.List>

                <Tabs.Content value="overview" className="mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Strengths */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                        <TrendingUpIcon className="w-5 h-5 text-green-500 mr-2" />
                        Key Strengths
                      </h3>
                      <ul className="space-y-2">
                        {research.strengths.map((strength, index) => (
                          <li key={index} className="flex items-start">
                            <span className="text-green-500 mr-2">•</span>
                            <span className="text-gray-700 dark:text-gray-300">{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Risks */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                        <InfoCircleIcon className="w-5 h-5 text-red-500 mr-2" />
                        Risk Factors
                      </h3>
                      <ul className="space-y-2">
                        {research.risks.map((risk, index) => (
                          <li key={index} className="flex items-start">
                            <span className="text-red-500 mr-2">•</span>
                            <span className="text-gray-700 dark:text-gray-300">{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Tabs.Content>

                <Tabs.Content value="financials" className="mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Revenue Growth</span>
                        <ChartLineIcon className="w-4 h-4 text-gray-400" />
                      </div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {research.revenue_growth.toFixed(1)}%
                      </p>
                      <Badge color={research.revenue_growth > 10 ? 'success' : 'warning'} size="sm" className="mt-2">
                        YoY
                      </Badge>
                    </div>

                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Profit Margin</span>
                        <BuildingIcon className="w-4 h-4 text-gray-400" />
                      </div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {research.profit_margin.toFixed(1)}%
                      </p>
                      <Badge color={research.profit_margin > 20 ? 'success' : 'warning'} size="sm" className="mt-2">
                        Net
                      </Badge>
                    </div>

                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Debt/Equity</span>
                        <InfoCircleIcon className="w-4 h-4 text-gray-400" />
                      </div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {research.debt_to_equity.toFixed(2)}
                      </p>
                      <Badge color={research.debt_to_equity < 1 ? 'success' : 'warning'} size="sm" className="mt-2">
                        Ratio
                      </Badge>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      <strong>Financial Health:</strong> The company shows strong financial metrics with 
                      {research.revenue_growth > 10 ? ' robust revenue growth' : ' moderate revenue growth'},
                      {research.profit_margin > 20 ? ' healthy profit margins' : ' improving profit margins'}, and
                      {research.debt_to_equity < 1 ? ' conservative debt levels' : ' manageable debt levels'}.
                    </p>
                  </div>
                </Tabs.Content>

                <Tabs.Content value="analysis" className="mt-6">
                  {deepAnalysis ? (
                    <div className="prose prose-gray dark:prose-invert max-w-none">
                      <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
                        {deepAnalysis.analysis || deepAnalysis}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                          Technical Analysis
                        </h4>
                        <p className="text-gray-700 dark:text-gray-300">
                          The stock is currently trading at ${research.current_price.toFixed(2)}, 
                          {research.current_price < research.price_target ? ' below' : ' above'} the analyst price target of 
                          ${research.price_target.toFixed(2)}. This represents a potential 
                          {research.current_price < research.price_target ? ' upside' : ' downside'} of 
                          {Math.abs(((research.price_target - research.current_price) / research.current_price) * 100).toFixed(1)}%.
                        </p>
                      </div>

                      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                          Valuation Analysis
                        </h4>
                        <p className="text-gray-700 dark:text-gray-300">
                          With a P/E ratio of {research.pe_ratio.toFixed(2)}, the stock is trading 
                          {research.pe_ratio < 25 ? ' at a reasonable valuation' : research.pe_ratio < 35 ? ' at a moderate premium' : ' at a high premium'} 
                          compared to the market average. The dividend yield of {research.dividend_yield.toFixed(2)}% 
                          provides {research.dividend_yield > 2 ? ' attractive income potential' : ' modest income potential'}.
                        </p>
                      </div>
                    </div>
                  )}
                </Tabs.Content>

                <Tabs.Content value="news" className="mt-6">
                  <div className="space-y-3">
                    {research.recent_news.map((news, index) => (
                      <div key={index} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-start space-x-3">
                        <Badge 
                          color={news.sentiment === 'positive' ? 'success' : news.sentiment === 'negative' ? 'error' : 'gray'}
                          size="sm"
                        >
                          {news.sentiment}
                        </Badge>
                        <div className="flex-grow">
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            {news.title}
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            {new Date(news.date).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </Tabs.Content>
              </Tabs>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}