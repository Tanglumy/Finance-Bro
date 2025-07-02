import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Trophy, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Award,
  BarChart3,
  PieChart,
  Activity,
  Zap,
  Star,
  CheckCircle2,
  RefreshCw,
  DollarSign,
  ArrowUpRight
} from "lucide-react";

interface Portfolio {
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  dayChange: number;
  dayChangePercent: number;
  positions: Position[];
}

interface Position {
  symbol: string;
  shares: number;
  currentPrice: number;
  avgCost: number;
  marketValue: number;
  unrealizedPL: number;
  unrealizedPLPercent: number;
  weight: number;
}

interface RewardMetric {
  id: string;
  title: string;
  value: number;
  target: number;
  unit: string;
  trend: "up" | "down" | "stable";
  score: number;
  description: string;
  suggestions: string[];
}

interface TradingReward {
  id: string;
  title: string;
  description: string;
  points: number;
  type: "achievement" | "milestone" | "performance";
  unlockedAt: Date;
  icon: string;
}

interface ReflexTuning {
  strategy: string;
  performance: number;
  lastAdjustment: Date;
  nextReview: Date;
  confidence: number;
  adjustments: string[];
}

export function RewardsAgentComponent() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [rewardMetrics, setRewardMetrics] = useState<RewardMetric[]>([]);
  const [tradingRewards, setTradingRewards] = useState<TradingReward[]>([]);
  const [reflexTuning, setReflexTuning] = useState<ReflexTuning[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const loadPortfolioData = () => {
    setLoading(true);
    
    setTimeout(() => {
      const mockPortfolio: Portfolio = {
        totalValue: 125437.89,
        totalReturn: 18923.45,
        totalReturnPercent: 17.8,
        dayChange: 2847.32,
        dayChangePercent: 2.32,
        positions: [
          {
            symbol: "AAPL",
            shares: 150,
            currentPrice: 185.42,
            avgCost: 168.30,
            marketValue: 27813.00,
            unrealizedPL: 2568.00,
            unrealizedPLPercent: 10.2,
            weight: 22.2
          },
          {
            symbol: "NVDA",
            shares: 75,
            currentPrice: 487.83,
            avgCost: 421.50,
            marketValue: 36587.25,
            unrealizedPL: 4974.75,
            unrealizedPLPercent: 15.7,
            weight: 29.1
          },
          {
            symbol: "TSLA",
            shares: 45,
            currentPrice: 248.91,
            avgCost: 267.80,
            marketValue: 11200.95,
            unrealizedPL: -849.05,
            unrealizedPLPercent: -7.0,
            weight: 8.9
          },
          {
            symbol: "MSFT",
            shares: 85,
            currentPrice: 378.25,
            avgCost: 342.10,
            marketValue: 32151.25,
            unrealizedPL: 3072.75,
            unrealizedPLPercent: 10.6,
            weight: 25.6
          }
        ]
      };

      const mockRewardMetrics: RewardMetric[] = [
        {
          id: "sharpe",
          title: "Sharpe Ratio",
          value: 1.87,
          target: 2.0,
          unit: "",
          trend: "up",
          score: 85,
          description: "RiOPENAI_API_KEY_REDACTED return performance",
          suggestions: ["Consider reducing exposure to high-volatility assets", "Diversify across sectors"]
        },
        {
          id: "diversification",
          title: "Diversification Score",
          value: 7.2,
          target: 8.0,
          unit: "/10",
          trend: "stable",
          score: 72,
          description: "Portfolio diversification level",
          suggestions: ["Add international exposure", "Include bonds or REITs"]
        },
        {
          id: "alpha",
          title: "Alpha Generation",
          value: 4.8,
          target: 3.0,
          unit: "%",
          trend: "up",
          score: 95,
          description: "Excess return vs benchmark",
          suggestions: ["Maintain current strategy", "Consider profit-taking on high performers"]
        },
        {
          id: "volatility",
          title: "Portfolio Volatility",
          value: 18.3,
          target: 15.0,
          unit: "%",
          trend: "down",
          score: 68,
          description: "Portfolio risk level",
          suggestions: ["Add defensive positions", "Reduce position sizes"]
        }
      ];

      const mockTradingRewards: TradingReward[] = [
        {
          id: "1",
          title: "Alpha Generator",
          description: "Achieved 15%+ returns vs benchmark",
          points: 500,
          type: "achievement",
          unlockedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2),
          icon: "🎯"
        },
        {
          id: "2",
          title: "Risk Manager",
          description: "Maintained Sharpe ratio above 1.5 for 3 months",
          points: 300,
          type: "milestone",
          unlockedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5),
          icon: "🛡️"
        },
        {
          id: "3",
          title: "Market Timing",
          description: "Successfully timed 3 major market moves",
          points: 750,
          type: "performance",
          unlockedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 1),
          icon: "⚡"
        },
        {
          id: "4",
          title: "Diversification Master",
          description: "Maintained well-balanced portfolio across sectors",
          points: 200,
          type: "achievement",
          unlockedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7),
          icon: "🎨"
        }
      ];

      const mockReflexTuning: ReflexTuning[] = [
        {
          strategy: "Momentum Following",
          performance: 0.87,
          lastAdjustment: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3),
          nextReview: new Date(Date.now() + 1000 * 60 * 60 * 24 * 4),
          confidence: 0.92,
          adjustments: [
            "Increased position sizing by 15%",
            "Tightened stop-loss levels",
            "Added sector rotation filter"
          ]
        },
        {
          strategy: "Mean Reversion",
          performance: 0.73,
          lastAdjustment: new Date(Date.now() - 1000 * 60 * 60 * 24 * 1),
          nextReview: new Date(Date.now() + 1000 * 60 * 60 * 24 * 6),
          confidence: 0.78,
          adjustments: [
            "Reduced holding period",
            "Added volatility filters",
            "Implemented dynamic position sizing"
          ]
        }
      ];

      setPortfolio(mockPortfolio);
      setRewardMetrics(mockRewardMetrics);
      setTradingRewards(mockTradingRewards);
      setReflexTuning(mockReflexTuning);
      setLoading(false);
    }, 1000);
  };

  const getMetricColor = (score: number) => {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-yellow-400";
    return "text-red-400";
  };

  const getMetricBgColor = (score: number) => {
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up": return <TrendingUp className="h-4 w-4 text-green-400" />;
      case "down": return <TrendingDown className="h-4 w-4 text-red-400" />;
      default: return <Activity className="h-4 w-4 text-yellow-400" />;
    }
  };

  const getRewardTypeColor = (type: string) => {
    switch (type) {
      case "achievement": return "bg-purple-600";
      case "milestone": return "bg-blue-600";
      case "performance": return "bg-green-600";
      default: return "bg-gray-600";
    }
  };

  const totalRewardPoints = tradingRewards.reduce((sum, reward) => sum + reward.points, 0);

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-purple-400">
              <Trophy className="h-5 w-5" />
              <span>Portfolio Rewards & Reflex Tuning</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge className="bg-purple-600 text-white">
                <Star className="h-3 w-3 mr-1" />
                {totalRewardPoints} Points
              </Badge>
              <Button 
                onClick={loadPortfolioData} 
                disabled={loading}
                variant="outline"
                size="sm"
                className="border-slate-600"
              >
                {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto"></div>
          <p className="text-slate-400 mt-4">Loading portfolio data...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Portfolio Value</p>
                    <p className="text-2xl font-bold text-white">
                      ${portfolio?.totalValue.toLocaleString()}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-emerald-400" />
                </div>
                <div className="flex items-center mt-2">
                  <ArrowUpRight className="h-4 w-4 text-green-400 mr-1" />
                  <span className="text-sm text-green-400">
                    +${portfolio?.dayChange.toLocaleString()} ({portfolio?.dayChangePercent}%)
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Total Return</p>
                    <p className="text-2xl font-bold text-green-400">
                      +{portfolio?.totalReturnPercent}%
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-400" />
                </div>
                <div className="flex items-center mt-2">
                  <span className="text-sm text-slate-300">
                    +${portfolio?.totalReturn.toLocaleString()}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Best Position</p>
                    <p className="text-2xl font-bold text-white">NVDA</p>
                  </div>
                  <Award className="h-8 w-8 text-purple-400" />
                </div>
                <div className="flex items-center mt-2">
                  <ArrowUpRight className="h-4 w-4 text-green-400 mr-1" />
                  <span className="text-sm text-green-400">+15.7%</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Reward Score</p>
                    <p className="text-2xl font-bold text-purple-400">8.2/10</p>
                  </div>
                  <Target className="h-8 w-8 text-purple-400" />
                </div>
                <div className="flex items-center mt-2">
                  <CheckCircle2 className="h-4 w-4 text-green-400 mr-1" />
                  <span className="text-sm text-green-400">Above target</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-emerald-400" />
                  <span>Performance Metrics</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {rewardMetrics.map((metric) => (
                    <div key={metric.id} className="p-4 rounded-lg bg-slate-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          {getTrendIcon(metric.trend)}
                          <span className="font-medium text-white">{metric.title}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`font-bold ${getMetricColor(metric.score)}`}>
                            {metric.value}{metric.unit}
                          </span>
                          <Badge className={`${getMetricBgColor(metric.score)} text-white text-xs`}>
                            {metric.score}
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="w-full bg-slate-600 rounded-full h-2 mb-2">
                        <div 
                          className={`h-2 rounded-full ${getMetricBgColor(metric.score)}`}
                          style={{ width: `${metric.score}%` }}
                        ></div>
                      </div>
                      
                      <p className="text-xs text-slate-400 mb-2">{metric.description}</p>
                      
                      <div className="space-y-1">
                        {metric.suggestions.map((suggestion, idx) => (
                          <div key={idx} className="flex items-center space-x-2">
                            <Zap className="h-3 w-3 text-yellow-400" />
                            <span className="text-xs text-slate-300">{suggestion}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Trophy className="h-5 w-5 text-purple-400" />
                    <span>Recent Achievements</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-64">
                    <div className="space-y-3">
                      {tradingRewards.map((reward) => (
                        <div key={reward.id} className="flex items-center space-x-3 p-3 rounded-lg bg-slate-700/50">
                          <div className="text-2xl">{reward.icon}</div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium text-white">{reward.title}</h4>
                              <Badge className={`${getRewardTypeColor(reward.type)} text-white text-xs`}>
                                +{reward.points}
                              </Badge>
                            </div>
                            <p className="text-sm text-slate-300">{reward.description}</p>
                            <p className="text-xs text-slate-500">
                              {reward.unlockedAt.toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="h-5 w-5 text-orange-400" />
                    <span>Reflex Tuning</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {reflexTuning.map((tuning, index) => (
                      <div key={index} className="p-4 rounded-lg bg-slate-700/50">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-white">{tuning.strategy}</h4>
                          <div className="flex items-center space-x-2">
                            <Badge className="bg-orange-600 text-white">
                              {Math.round(tuning.performance * 100)}%
                            </Badge>
                            <Badge variant="outline" className="border-slate-600 text-slate-300">
                              {Math.round(tuning.confidence * 100)}% conf
                            </Badge>
                          </div>
                        </div>
                        
                        <div className="text-xs text-slate-400 mb-2">
                          Last adjusted: {tuning.lastAdjustment.toLocaleDateString()}
                        </div>
                        
                        <div className="space-y-1">
                          {tuning.adjustments.slice(0, 2).map((adjustment, idx) => (
                            <div key={idx} className="flex items-center space-x-2">
                              <CheckCircle2 className="h-3 w-3 text-green-400" />
                              <span className="text-xs text-slate-300">{adjustment}</span>
                            </div>
                          ))}
                        </div>
                        
                        <div className="flex items-center justify-between mt-3">
                          <span className="text-xs text-slate-400">
                            Next review: {tuning.nextReview.toLocaleDateString()}
                          </span>
                          <Button variant="ghost" size="sm" className="text-orange-400 hover:text-orange-300">
                            <RefreshCw className="h-3 w-3 mr-1" />
                            Tune
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <PieChart className="h-5 w-5 text-blue-400" />
                <span>Portfolio Positions</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {portfolio?.positions.map((position) => (
                  <div key={position.symbol} className="p-4 rounded-lg bg-slate-700/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-lg text-white">{position.symbol}</span>
                      <Badge variant="outline" className="border-slate-600 text-slate-300">
                        {position.weight}%
                      </Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-400">Shares:</span>
                        <span className="text-sm text-white">{position.shares}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-400">Value:</span>
                        <span className="text-sm text-white">${position.marketValue.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-400">P/L:</span>
                        <span className={`text-sm ${position.unrealizedPL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {position.unrealizedPL >= 0 ? '+' : ''}${position.unrealizedPL.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-400">Return:</span>
                        <span className={`text-sm font-medium ${position.unrealizedPLPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {position.unrealizedPLPercent >= 0 ? '+' : ''}{position.unrealizedPLPercent}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}