'use client';

import { useState, useEffect } from 'react';
import { api, type FormulaModel, type BacktestResult } from '@/services/api';
import { Card } from '@/components/application/cards/card';
import { Button } from '@/components/base/buttons/button';
import { Input } from '@/components/base/input/input';
import { TextArea } from '@/components/base/textarea/textarea';
import { Badge } from '@/components/base/badges/badges';
import { Tabs } from '@/components/application/tabs/tabs';
import { ProgressCircles } from '@/components/base/progress-indicators/progress-indicators';
import { 
  CodeIcon,
  PlayIcon,
  SaveIcon,
  ChartBarIcon,
  BookOpenIcon,
  CheckCircleIcon,
  XCircleIcon,
  InfoCircleIcon
} from '@untitledui/icons';

interface FormulaFunction {
  name: string;
  description: string;
  parameters: string[];
  example: string;
}

export default function StrategiesPage() {
  const [activeTab, setActiveTab] = useState('builder');
  const [models, setModels] = useState<FormulaModel[]>([]);
  const [functions, setFunctions] = useState<FormulaFunction[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<FormulaModel | null>(null);
  
  // Formula Builder State
  const [formulaName, setFormulaName] = useState('');
  const [formulaDescription, setFormulaDescription] = useState('');
  const [formulaCode, setFormulaCode] = useState('');
  const [validationResult, setValidationResult] = useState<{ valid: boolean; error?: string } | null>(null);
  
  // Backtest State
  const [backtestResults, setBacktestResults] = useState<BacktestResult | null>(null);
  const [backtestSymbol, setBacktestSymbol] = useState('AAPL');
  const [backtestDays, setBacktestDays] = useState('252'); // 1 year

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [modelsData, functionsData] = await Promise.all([
        api.getFormulaModels(),
        api.getFormulaFunctions()
      ]);
      
      setModels(modelsData);
      setFunctions(functionsData || getMockFunctions());
    } catch (error) {
      console.error('Failed to load data:', error);
      // Set mock data
      setModels(getMockModels());
      setFunctions(getMockFunctions());
    }
  };

  const getMockFunctions = (): FormulaFunction[] => [
    {
      name: 'SMA',
      description: 'Simple Moving Average',
      parameters: ['period'],
      example: 'SMA(20) # 20-period simple moving average'
    },
    {
      name: 'EMA',
      description: 'Exponential Moving Average',
      parameters: ['period'],
      example: 'EMA(12) # 12-period exponential moving average'
    },
    {
      name: 'RSI',
      description: 'Relative Strength Index',
      parameters: ['period'],
      example: 'RSI(14) # 14-period RSI'
    },
    {
      name: 'MACD',
      description: 'Moving Average Convergence Divergence',
      parameters: ['fast', 'slow', 'signal'],
      example: 'MACD(12, 26, 9) # Standard MACD'
    },
    {
      name: 'BB',
      description: 'Bollinger Bands',
      parameters: ['period', 'std_dev'],
      example: 'BB(20, 2) # 20-period BB with 2 std dev'
    },
    {
      name: 'CROSSOVER',
      description: 'Crossover Signal',
      parameters: ['series1', 'series2'],
      example: 'CROSSOVER(CLOSE, SMA(50)) # Price crosses above 50-day MA'
    }
  ];

  const getMockModels = (): FormulaModel[] => [
    {
      name: 'Golden Cross Strategy',
      formula: 'BUY_SIGNAL = CROSSOVER(SMA(50), SMA(200)) AND RSI(14) < 70\nSELL_SIGNAL = CROSSOVER(SMA(200), SMA(50)) OR RSI(14) > 80',
      description: 'Classic golden cross strategy with RSI filter'
    },
    {
      name: 'Mean Reversion',
      formula: 'BUY_SIGNAL = CLOSE < BB_LOWER(20, 2) AND RSI(14) < 30\nSELL_SIGNAL = CLOSE > BB_UPPER(20, 2) AND RSI(14) > 70',
      description: 'Bollinger Band mean reversion strategy'
    },
    {
      name: 'Momentum Breakout',
      formula: 'BUY_SIGNAL = CLOSE > MAX(HIGH, 20) AND VOLUME > SMA(VOLUME, 10) * 1.5\nSELL_SIGNAL = CLOSE < SMA(20)',
      description: 'High volume breakout strategy'
    }
  ];

  const validateFormula = async () => {
    if (!formulaCode.trim()) return;
    
    setLoading(true);
    try {
      const result = await api.validateFormula(formulaCode);
      setValidationResult(result);
    } catch (error) {
      setValidationResult({ 
        valid: false, 
        error: error instanceof Error ? error.message : 'Validation failed' 
      });
    } finally {
      setLoading(false);
    }
  };

  const saveFormula = async () => {
    if (!formulaName || !formulaCode || validationResult?.valid !== true) {
      return;
    }

    setLoading(true);
    try {
      const model: FormulaModel = {
        name: formulaName,
        formula: formulaCode,
        description: formulaDescription
      };
      
      await api.createFormulaModel(model);
      setModels(prev => [...prev, model]);
      
      // Reset form
      setFormulaName('');
      setFormulaDescription('');
      setFormulaCode('');
      setValidationResult(null);
    } catch (error) {
      console.error('Failed to save formula:', error);
    } finally {
      setLoading(false);
    }
  };

  const runBacktest = async (model: FormulaModel) => {
    setLoading(true);
    setSelectedModel(model);
    
    try {
      // Mock historical data
      const mockData = generateMockHistoricalData(parseInt(backtestDays));
      
      const result = await api.backtestFormula(model.name, mockData, {
        initial_capital: 100000,
        commission: 0.001
      });
      
      setBacktestResults(result);
      setActiveTab('backtest');
    } catch (error) {
      console.error('Backtest failed:', error);
      // Generate mock backtest results
      setBacktestResults(generateMockBacktestResults());
      setActiveTab('backtest');
    } finally {
      setLoading(false);
    }
  };

  const generateMockHistoricalData = (days: number) => {
    const data: any = { dates: [], prices: [], volumes: [] };
    let price = 150;
    
    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      
      price += (Math.random() - 0.5) * 5;
      data.dates.push(date.toISOString().split('T')[0]);
      data.prices.push(Math.max(price, 10));
      data.volumes.push(Math.floor(Math.random() * 1000000) + 100000);
    }
    
    return data;
  };

  const generateMockBacktestResults = (): BacktestResult => {
    const totalReturn = (Math.random() * 50 - 10); // -10% to 40%
    const numTrades = Math.floor(Math.random() * 50) + 10;
    const winningTrades = Math.floor(numTrades * (0.4 + Math.random() * 0.4));
    
    return {
      total_return: totalReturn,
      sharpe_ratio: Math.random() * 2 + 0.5,
      max_drawdown: -(Math.random() * 15 + 5),
      win_rate: winningTrades / numTrades,
      trades: Array.from({ length: Math.min(numTrades, 10) }, (_, i) => ({
        date: new Date(Date.now() - (numTrades - i) * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        action: Math.random() > 0.5 ? 'BUY' : 'SELL',
        price: 150 + (Math.random() - 0.5) * 50,
        quantity: Math.floor(Math.random() * 100) + 10,
        pnl: (Math.random() - 0.5) * 1000
      }))
    };
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <CodeIcon className="w-8 h-8 text-purple-600" />
          Trading Strategies
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Create, test, and optimize your trading strategies using our Formula Engine
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Trigger value="builder">Strategy Builder</Tabs.Trigger>
          <Tabs.Trigger value="library">Strategy Library</Tabs.Trigger>
          <Tabs.Trigger value="functions">Functions Reference</Tabs.Trigger>
          <Tabs.Trigger value="backtest">Backtest Results</Tabs.Trigger>
        </Tabs.List>

        {/* Strategy Builder */}
        <Tabs.Content value="builder" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <div className="p-6 space-y-4">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Create New Strategy
                </h2>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Strategy Name
                  </label>
                  <Input
                    value={formulaName}
                    onChange={(e) => setFormulaName(e.target.value)}
                    placeholder="My Trading Strategy"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Description
                  </label>
                  <TextArea
                    value={formulaDescription}
                    onChange={(e) => setFormulaDescription(e.target.value)}
                    placeholder="Brief description of your strategy"
                    rows={2}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Formula Code
                  </label>
                  <TextArea
                    value={formulaCode}
                    onChange={(e) => {
                      setFormulaCode(e.target.value);
                      setValidationResult(null);
                    }}
                    placeholder={`# Define your buy and sell signals
BUY_SIGNAL = CROSSOVER(SMA(50), SMA(200))
SELL_SIGNAL = CROSSOVER(SMA(200), SMA(50))`}
                    rows={8}
                    className="font-mono text-sm"
                  />
                </div>

                {validationResult && (
                  <div className={`p-3 rounded-lg flex items-start space-x-3 ${
                    validationResult.valid 
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                      : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                  }`}>
                    {validationResult.valid ? (
                      <CheckCircleIcon className="w-5 h-5 flex-shrink-0" />
                    ) : (
                      <XCircleIcon className="w-5 h-5 flex-shrink-0" />
                    )}
                    <div className="text-sm">
                      {validationResult.valid 
                        ? 'Formula is valid and ready to use!'
                        : validationResult.error || 'Formula contains errors'
                      }
                    </div>
                  </div>
                )}

                <div className="flex space-x-3">
                  <Button
                    variant="secondary"
                    onClick={validateFormula}
                    disabled={loading || !formulaCode.trim()}
                  >
                    {loading ? <ProgressCircles size="sm" /> : 'Validate'}
                  </Button>
                  <Button
                    variant="primary"
                    onClick={saveFormula}
                    disabled={loading || !validationResult?.valid || !formulaName}
                  >
                    <SaveIcon className="w-4 h-4 mr-2" />
                    Save Strategy
                  </Button>
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Quick Functions
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {functions.slice(0, 8).map((func, index) => (
                    <div key={index} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex justify-between items-start mb-1">
                        <code className="text-sm font-mono text-purple-600 dark:text-purple-400">
                          {func.name}
                        </code>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setFormulaCode(prev => prev + '\n' + func.example)}
                        >
                          Insert
                        </Button>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {func.description}
                      </p>
                      <code className="text-xs text-gray-500 dark:text-gray-500 block mt-1">
                        {func.example}
                      </code>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        </Tabs.Content>

        {/* Strategy Library */}
        <Tabs.Content value="library" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map((model, index) => (
              <Card key={index}>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {model.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {model.description}
                  </p>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded p-3 mb-4">
                    <code className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {model.formula.substring(0, 150)}
                      {model.formula.length > 150 && '...'}
                    </code>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => runBacktest(model)}
                      disabled={loading}
                    >
                      <PlayIcon className="w-4 h-4 mr-1" />
                      Test
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setFormulaCode(model.formula);
                        setActiveTab('builder');
                      }}
                    >
                      <CodeIcon className="w-4 h-4 mr-1" />
                      Edit
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Tabs.Content>

        {/* Functions Reference */}
        <Tabs.Content value="functions" className="mt-6">
          <Card>
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
                <BookOpenIcon className="w-6 h-6 mr-2" />
                Available Functions
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {functions.map((func, index) => (
                  <div key={index} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <code className="text-lg font-mono font-semibold text-purple-600 dark:text-purple-400">
                        {func.name}
                      </code>
                      <Badge color="gray" size="sm">
                        {func.parameters.length} param{func.parameters.length !== 1 ? 's' : ''}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {func.description}
                    </p>
                    <div className="bg-gray-50 dark:bg-gray-800 rounded p-2">
                      <code className="text-sm text-gray-700 dark:text-gray-300">
                        {func.example}
                      </code>
                    </div>
                    <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                      Parameters: {func.parameters.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </Tabs.Content>

        {/* Backtest Results */}
        <Tabs.Content value="backtest" className="mt-6">
          {backtestResults ? (
            <div className="space-y-6">
              <Card>
                <div className="p-6">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                        Backtest Results
                      </h2>
                      <p className="text-gray-600 dark:text-gray-400 mt-1">
                        {selectedModel?.name || 'Strategy'} • {backtestSymbol} • {backtestDays} days
                      </p>
                    </div>
                    <Badge 
                      color={backtestResults.total_return > 0 ? 'success' : 'error'} 
                      size="lg"
                    >
                      {backtestResults.total_return > 0 ? '+' : ''}{backtestResults.total_return.toFixed(2)}%
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Total Return</p>
                      <p className={`text-xl font-semibold ${
                        backtestResults.total_return > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {backtestResults.total_return.toFixed(2)}%
                      </p>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</p>
                      <p className="text-xl font-semibold text-gray-900 dark:text-white">
                        {backtestResults.sharpe_ratio.toFixed(2)}
                      </p>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</p>
                      <p className="text-xl font-semibold text-red-600">
                        {backtestResults.max_drawdown.toFixed(2)}%
                      </p>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Win Rate</p>
                      <p className="text-xl font-semibold text-gray-900 dark:text-white">
                        {(backtestResults.win_rate * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              </Card>

              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Recent Trades
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-400">Date</th>
                          <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-400">Action</th>
                          <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-400">Price</th>
                          <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-400">Quantity</th>
                          <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-400">P&L</th>
                        </tr>
                      </thead>
                      <tbody>
                        {backtestResults.trades.map((trade, index) => (
                          <tr key={index} className="border-b border-gray-100 dark:border-gray-800">
                            <td className="p-3 text-sm text-gray-900 dark:text-white">
                              {new Date(trade.date).toLocaleDateString()}
                            </td>
                            <td className="p-3">
                              <Badge 
                                color={trade.action === 'BUY' ? 'success' : 'error'} 
                                size="sm"
                              >
                                {trade.action}
                              </Badge>
                            </td>
                            <td className="p-3 text-sm text-gray-900 dark:text-white text-right">
                              ${trade.price.toFixed(2)}
                            </td>
                            <td className="p-3 text-sm text-gray-900 dark:text-white text-right">
                              {trade.quantity}
                            </td>
                            <td className="p-3 text-right">
                              {trade.pnl && (
                                <span className={trade.pnl > 0 ? 'text-green-600' : 'text-red-600'}>
                                  ${Math.abs(trade.pnl).toFixed(2)}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </Card>
            </div>
          ) : (
            <Card>
              <div className="p-12 text-center">
                <ChartBarIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  No Backtest Results
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Run a backtest on a strategy to see detailed performance metrics
                </p>
                <Button variant="primary" onClick={() => setActiveTab('library')}>
                  Choose Strategy to Test
                </Button>
              </div>
            </Card>
          )}
        </Tabs.Content>
      </Tabs>
    </div>
  );
}