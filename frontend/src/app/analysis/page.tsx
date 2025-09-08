'use client';

import { useState } from 'react';
import { api, type AnalysisRequest, type AnalysisResponse } from '@/services/api';
import { Card } from '@/components/application/cards/card';
import { Button } from '@/components/base/buttons/button';
import { Badge } from '@/components/base/badges/badges';
import { TextArea } from '@/components/base/textarea/textarea';
import { Select } from '@/components/base/select/select';
import { ProgressCircles } from '@/components/base/progress-indicators/progress-indicators';
import { 
  TrendingUpIcon, 
  TrendingDownIcon, 
  AlertCircleIcon,
  CheckCircleIcon,
  ChartLineIcon,
  BrainIcon 
} from '@untitledui/icons';

export default function MarketAnalysisPage() {
  const [query, setQuery] = useState('');
  const [riskTolerance, setRiskTolerance] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate');
  const [investmentHorizon, setInvestmentHorizon] = useState<'short' | 'medium' | 'long'>('medium');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!query.trim()) {
      setError('Please enter an analysis query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: AnalysisRequest = {
        message: query,
        risk_tolerance: riskTolerance,
        investment_horizon: investmentHorizon,
      };

      const response = await api.analyzeMarket(request);
      setAnalysis(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze market');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (action: string) => {
    switch (action) {
      case 'BUY':
        return 'success';
      case 'SELL':
        return 'error';
      case 'HOLD':
        return 'warning';
      default:
        return 'gray';
    }
  };

  const getImpactIcon = (impact: string) => {
    if (impact === 'positive' || impact === 'high') {
      return <TrendingUpIcon className="w-5 h-5 text-green-500" />;
    } else if (impact === 'negative' || impact === 'low') {
      return <TrendingDownIcon className="w-5 h-5 text-red-500" />;
    } else {
      return <AlertCircleIcon className="w-5 h-5 text-yellow-500" />;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <ChartLineIcon className="w-8 h-8 text-blue-600" />
          Market Analysis
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Get AI-powered market insights and trading recommendations
        </p>
      </div>

      {/* Analysis Input */}
      <Card>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              What would you like to analyze?
            </label>
            <TextArea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="E.g., 'Analyze tech sector opportunities' or 'What's the outlook for renewable energy stocks?'"
              rows={4}
              className="w-full"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Risk Tolerance
              </label>
              <Select
                value={riskTolerance}
                onValueChange={(value) => setRiskTolerance(value as any)}
              >
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Investment Horizon
              </label>
              <Select
                value={investmentHorizon}
                onValueChange={(value) => setInvestmentHorizon(value as any)}
              >
                <option value="short">Short-term (&lt; 1 year)</option>
                <option value="medium">Medium-term (1-5 years)</option>
                <option value="long">Long-term (&gt; 5 years)</option>
              </Select>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg">
              {error}
            </div>
          )}

          <Button
            variant="primary"
            size="lg"
            onClick={handleAnalyze}
            disabled={loading || !query.trim()}
            className="w-full md:w-auto"
          >
            {loading ? (
              <>
                <ProgressCircles size="sm" className="mr-2" />
                Analyzing...
              </>
            ) : (
              <>
                <BrainIcon className="w-5 h-5 mr-2" />
                Analyze Market
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <>
          {/* Main Analysis */}
          <Card>
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Analysis Summary
              </h2>
              <div className="prose prose-gray dark:prose-invert max-w-none">
                <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
                  {analysis.analysis}
                </div>
              </div>
            </div>
          </Card>

          {/* Market Events */}
          {analysis.market_events.length > 0 && (
            <Card>
              <div className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Market Events
                </h2>
                <div className="space-y-3">
                  {analysis.market_events.map((event, index) => (
                    <div 
                      key={index}
                      className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-start space-x-3"
                    >
                      <div className="flex-shrink-0">
                        {getImpactIcon(event.impact)}
                      </div>
                      <div className="flex-grow">
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {event.title}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {event.description}
                        </p>
                        <div className="flex items-center space-x-3 mt-2">
                          <Badge 
                            color={event.impact === 'positive' || event.impact === 'high' ? 'success' : 
                                   event.impact === 'negative' || event.impact === 'low' ? 'error' : 'warning'}
                            size="sm"
                          >
                            {event.impact}
                          </Badge>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(event.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {/* Trading Signals */}
          {analysis.trading_signals.length > 0 && (
            <Card>
              <div className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Trading Signals
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {analysis.trading_signals.map((signal, index) => (
                    <div 
                      key={index}
                      className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {signal.symbol}
                        </h3>
                        <Badge color={getSignalColor(signal.action)} size="sm">
                          {signal.action}
                        </Badge>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600 dark:text-gray-400">Current Price</span>
                          <span className="font-medium text-gray-900 dark:text-white">
                            ${signal.current_price.toFixed(2)}
                          </span>
                        </div>
                        
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600 dark:text-gray-400">Confidence</span>
                          <span className="font-medium text-gray-900 dark:text-white">
                            {(signal.confidence * 100).toFixed(0)}%
                          </span>
                        </div>

                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {signal.reasoning}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {/* Portfolio Recommendations */}
          {analysis.portfolio_recommendations.length > 0 && (
            <Card>
              <div className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Portfolio Recommendations
                </h2>
                <div className="space-y-3">
                  {analysis.portfolio_recommendations.map((rec, index) => (
                    <div 
                      key={index}
                      className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800"
                    >
                      <div className="flex items-start space-x-3">
                        <CheckCircleIcon className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-white">
                            {rec.title}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {rec.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}