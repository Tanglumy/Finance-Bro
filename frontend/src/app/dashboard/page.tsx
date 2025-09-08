'use client';

import { useEffect, useState } from 'react';
import { api, wsManager, type PortfolioSummary } from '@/services/api';
import { Card } from '@/components/application/cards/card';
import { Button } from '@/components/base/buttons/button';
import { Badge } from '@/components/base/badges/badges';
import { ProgressCircles } from '@/components/base/progress-indicators/progress-circles';
import { TrendingUpIcon, TrendingDownIcon, DollarSignIcon, BarChart3Icon } from '@untitledui/icons';

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [marketData, setMarketData] = useState<Record<string, any>>({});
  const [agentThoughts, setAgentThoughts] = useState<any[]>([]);

  useEffect(() => {
    // Load initial data
    loadPortfolioData();
    loadAgentThoughts();

    // Connect WebSocket for real-time updates
    wsManager.connect();

    // Subscribe to real-time updates
    const unsubMarket = wsManager.subscribe('market_update', (data) => {
      setMarketData(data);
    });

    const unsubThoughts = wsManager.subscribe('agent_thought', (data) => {
      setAgentThoughts(prev => [data, ...prev].slice(0, 5));
    });

    return () => {
      unsubMarket();
      unsubThoughts();
    };
  }, []);

  const loadPortfolioData = async () => {
    try {
      setLoading(true);
      const data = await api.getPortfolioSummary();
      setPortfolio(data);
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAgentThoughts = async () => {
    try {
      const thoughts = await api.getAgentThoughts();
      setAgentThoughts(thoughts.slice(0, 5));
    } catch (error) {
      console.error('Failed to load agent thoughts:', error);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value / 100);
    return value >= 0 ? `+${formatted}` : formatted;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <ProgressCircles size="lg" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Portfolio Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track your investments and market performance
          </p>
        </div>
        <Button variant="primary" size="lg" onClick={loadPortfolioData}>
          Refresh Data
        </Button>
      </div>

      {/* Portfolio Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <DollarSignIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Value</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {portfolio ? formatCurrency(portfolio.total_value) : '$0'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  portfolio && portfolio.daily_change >= 0 
                    ? 'bg-green-100 dark:bg-green-900' 
                    : 'bg-red-100 dark:bg-red-900'
                }`}>
                  {portfolio && portfolio.daily_change >= 0 
                    ? <TrendingUpIcon className="w-6 h-6 text-green-600 dark:text-green-400" />
                    : <TrendingDownIcon className="w-6 h-6 text-red-600 dark:text-red-400" />
                  }
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Daily Change</p>
                  <div className="flex items-baseline space-x-2">
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {portfolio ? formatCurrency(Math.abs(portfolio.daily_change)) : '$0'}
                    </p>
                    {portfolio && (
                      <Badge 
                        color={portfolio.daily_change >= 0 ? 'success' : 'error'}
                        size="sm"
                      >
                        {formatPercent(portfolio.daily_change_percent)}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  portfolio && portfolio.total_pnl >= 0 
                    ? 'bg-green-100 dark:bg-green-900' 
                    : 'bg-red-100 dark:bg-red-900'
                }`}>
                  <BarChart3Icon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total P&L</p>
                  <div className="flex items-baseline space-x-2">
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {portfolio ? formatCurrency(Math.abs(portfolio.total_pnl)) : '$0'}
                    </p>
                    {portfolio && (
                      <Badge 
                        color={portfolio.total_pnl >= 0 ? 'success' : 'error'}
                        size="sm"
                      >
                        {formatPercent(portfolio.total_pnl_percent)}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                  <DollarSignIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Cash Balance</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {portfolio ? formatCurrency(portfolio.cash_balance) : '$0'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Live Market Data */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Live Market Data
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(marketData).map(([symbol, data]: [string, any]) => (
              <div key={symbol} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex justify-between items-start mb-1">
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {symbol}
                  </span>
                  <Badge 
                    color={data.change >= 0 ? 'success' : 'error'}
                    size="sm"
                  >
                    {data.change_percent?.toFixed(2)}%
                  </Badge>
                </div>
                <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
                  ${data.price?.toFixed(2)}
                </p>
              </div>
            ))}
            {Object.keys(marketData).length === 0 && (
              <div className="col-span-full text-center text-gray-500 dark:text-gray-400">
                Waiting for market data...
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* AI Agent Insights */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            AI Agent Insights
          </h2>
          <div className="space-y-3">
            {agentThoughts.map((thought, index) => (
              <div 
                key={thought.id || index}
                className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-start space-x-3"
              >
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                </div>
                <div className="flex-grow">
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    {thought.content}
                  </p>
                  <div className="flex items-center space-x-3 mt-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(thought.timestamp).toLocaleTimeString()}
                    </span>
                    {thought.confidence && (
                      <Badge color="gray" size="sm">
                        {(thought.confidence * 100).toFixed(0)}% confidence
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {agentThoughts.length === 0 && (
              <div className="text-center text-gray-500 dark:text-gray-400 py-4">
                No agent insights available yet
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}