import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiService } from "@/services/api";
import { 
  TrendingUp, 
  Play, 
  Pause, 
  Settings, 
  Activity,
  CheckCircle2,
  Clock,
  Zap,
  Target,
  DollarSign,
  BarChart3,
  ArrowUpRight,
  Bot,
  Brain,
  Eye,
  MessageSquare,
  Wallet
} from "lucide-react";

interface Trade {
  id: string;
  symbol: string;
  action: "BUY" | "SELL";
  quantity: number;
  price: number;
  timestamp: Date;
  status: "pending" | "executed" | "cancelled" | "partial";
  reasoning: string;
  confidence: number;
}

interface AgentStatus {
  isActive: boolean;
  mode: "aggressive" | "conservative" | "balanced";
  balance: number;
  buyingPower: number;
  dailyPnL: number;
  totalTrades: number;
  successRate: number;
  lastAction: Date;
}

interface MarketOrder {
  symbol: string;
  orderType: "market" | "limit" | "stop";
  action: "BUY" | "SELL";
  quantity: number;
  price?: number;
  stopPrice?: number;
  timeInForce: "DAY" | "GTC" | "IOC";
}

interface AgentThought {
  id: string;
  timestamp: Date;
  type: "analysis" | "decision" | "execution" | "monitoring";
  content: string;
  confidence: number;
  relatedSymbol?: string;
}

export function ExecutiveAgentComponent() {
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [agentThoughts, setAgentThoughts] = useState<AgentThought[]>([]);
  const [pendingOrder, setPendingOrder] = useState<MarketOrder>({
    symbol: "",
    orderType: "market",
    action: "BUY",
    quantity: 0,
    timeInForce: "DAY"
  });
  const [loading, setLoading] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  useEffect(() => {
    loadAgentData();
    if (isSimulating) {
      const interval = setInterval(simulateAgentActivity, 5000);
      return () => clearInterval(interval);
    }
  }, [isSimulating]);

  const loadAgentData = async () => {
    setLoading(true);
    setConnectionStatus('checking');
    
    try {
      await apiService.getHealthStatus();
      setConnectionStatus('connected');
      
      const mockAgentStatus: AgentStatus = {
        isActive: true,
        mode: "balanced",
        balance: 87432.50,
        buyingPower: 23678.90,
        dailyPnL: 1847.32,
        totalTrades: 127,
        successRate: 73.2,
        lastAction: new Date(Date.now() - 1000 * 60 * 15)
      };

      const mockTrades: Trade[] = [
        {
          id: "1",
          symbol: "AAPL",
          action: "BUY",
          quantity: 50,
          price: 185.42,
          timestamp: new Date(Date.now() - 1000 * 60 * 30),
          status: "executed",
          reasoning: "Strong earnings momentum, technical breakout above resistance",
          confidence: 0.87
        },
        {
          id: "2",
          symbol: "TSLA",
          action: "SELL",
          quantity: 25,
          price: 248.91,
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
          status: "executed",
          reasoning: "Profit taking after 15% gain, potential resistance at current level",
          confidence: 0.78
        },
        {
          id: "3",
          symbol: "NVDA",
          action: "BUY",
          quantity: 30,
          price: 487.83,
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4),
          status: "pending",
          reasoning: "AI sector momentum, strong institutional buying",
          confidence: 0.92
        }
      ];

      const mockThoughts: AgentThought[] = [
        {
          id: "1",
          timestamp: new Date(),
          type: "analysis",
          content: "Analyzing market volatility patterns... VIX showing signs of complacency. Preparing for potential regime shift.",
          confidence: 0.75,
          relatedSymbol: "VIX"
        },
        {
          id: "2",
          timestamp: new Date(Date.now() - 1000 * 60 * 2),
          type: "decision",
          content: "AAPL showing strong relative strength vs SPY. Momentum indicators aligned for continuation. Initiating position.",
          confidence: 0.87,
          relatedSymbol: "AAPL"
        },
        {
          id: "3",
          timestamp: new Date(Date.now() - 1000 * 60 * 5),
          type: "monitoring",
          content: "Portfolio heat map showing technology sector overweight. Monitoring for rebalancing opportunities.",
          confidence: 0.68
        },
        {
          id: "4",
          timestamp: new Date(Date.now() - 1000 * 60 * 8),
          type: "execution",
          content: "TSLA position closed at target. Risk/reward no longer favorable. Booking 15.7% gain.",
          confidence: 0.83,
          relatedSymbol: "TSLA"
        }
      ];

      setAgentStatus(mockAgentStatus);
      setRecentTrades(mockTrades);
      setAgentThoughts(mockThoughts);
    } catch (error) {
      console.error('Failed to connect to backend:', error);
      setConnectionStatus('disconnected');
    } finally {
      setLoading(false);
    }
  };

  const simulateAgentActivity = () => {
    const newThought: AgentThought = {
      id: Date.now().toString(),
      timestamp: new Date(),
      type: ["analysis", "decision", "monitoring", "execution"][Math.floor(Math.random() * 4)] as any,
      content: [
        "Scanning market for oversold conditions...",
        "Detecting unusual options flow in tech sector",
        "Risk metrics within acceptable parameters",
        "Adjusting position sizes based on volatility",
        "Monitoring Fed speakers for policy signals",
        "Technical indicators showing bullish divergence"
      ][Math.floor(Math.random() * 6)],
      confidence: Math.random() * 0.4 + 0.6,
      relatedSymbol: ["AAPL", "NVDA", "TSLA", "MSFT", "SPY"][Math.floor(Math.random() * 5)]
    };

    setAgentThoughts(prev => [newThought, ...prev.slice(0, 9)]);
  };

  const toggleAgent = () => {
    if (agentStatus) {
      setAgentStatus(prev => prev ? { ...prev, isActive: !prev.isActive } : null);
      setIsSimulating(!agentStatus.isActive);
    }
  };

  const changeAgentMode = (mode: "aggressive" | "conservative" | "balanced") => {
    if (agentStatus) {
      setAgentStatus(prev => prev ? { ...prev, mode } : null);
    }
  };

  const submitOrder = () => {
    if (!pendingOrder.symbol || !pendingOrder.quantity) return;
    
    const newTrade: Trade = {
      id: Date.now().toString(),
      symbol: pendingOrder.symbol,
      action: pendingOrder.action,
      quantity: pendingOrder.quantity,
      price: pendingOrder.price || 0,
      timestamp: new Date(),
      status: "pending",
      reasoning: "Manual trade execution via executive interface",
      confidence: 0.85
    };

    setRecentTrades(prev => [newTrade, ...prev]);
    setPendingOrder({
      symbol: "",
      orderType: "market",
      action: "BUY",
      quantity: 0,
      timeInForce: "DAY"
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "executed": return "text-green-400 bg-green-400/20";
      case "pending": return "text-yellow-400 bg-yellow-400/20";
      case "cancelled": return "text-red-400 bg-red-400/20";
      case "partial": return "text-blue-400 bg-blue-400/20";
      default: return "text-gray-400 bg-gray-400/20";
    }
  };

  const getThoughtIcon = (type: string) => {
    switch (type) {
      case "analysis": return <BarChart3 className="h-4 w-4 text-blue-400" />;
      case "decision": return <Brain className="h-4 w-4 text-purple-400" />;
      case "execution": return <Zap className="h-4 w-4 text-green-400" />;
      case "monitoring": return <Eye className="h-4 w-4 text-yellow-400" />;
      default: return <MessageSquare className="h-4 w-4 text-gray-400" />;
    }
  };

  const getModeColor = (mode: string) => {
    switch (mode) {
      case "aggressive": return "bg-red-600";
      case "conservative": return "bg-blue-600";
      case "balanced": return "bg-green-600";
      default: return "bg-gray-600";
    }
  };

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-orange-400">
              <Bot className="h-5 w-5" />
              <span>Executive Trading Agent</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge className={`${connectionStatus === 'connected' ? 'bg-blue-600' : connectionStatus === 'checking' ? 'bg-yellow-600' : 'bg-red-600'} text-white`}>
                {connectionStatus === 'connected' ? 'CONNECTED' : connectionStatus === 'checking' ? 'CONNECTING' : 'DISCONNECTED'}
              </Badge>
              <Badge className={`${agentStatus?.isActive ? 'bg-green-600' : 'bg-red-600'} text-white`}>
                {agentStatus?.isActive ? 'ACTIVE' : 'INACTIVE'}
              </Badge>
              <Badge className={`${getModeColor(agentStatus?.mode || 'balanced')} text-white`}>
                {agentStatus?.mode?.toUpperCase()}
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-400 mx-auto"></div>
          <p className="text-slate-400 mt-4">Initializing trading agent...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Account Balance</p>
                    <p className="text-2xl font-bold text-white">
                      ${agentStatus?.balance.toLocaleString()}
                    </p>
                  </div>
                  <Wallet className="h-8 w-8 text-emerald-400" />
                </div>
                <div className="flex items-center mt-2">
                  <DollarSign className="h-4 w-4 text-green-400 mr-1" />
                  <span className="text-sm text-green-400">
                    Buying Power: ${agentStatus?.buyingPower.toLocaleString()}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Daily P&L</p>
                    <p className="text-2xl font-bold text-green-400">
                      +${agentStatus?.dailyPnL.toLocaleString()}
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-400" />
                </div>
                <div className="flex items-center mt-2">
                  <ArrowUpRight className="h-4 w-4 text-green-400 mr-1" />
                  <span className="text-sm text-green-400">Today's gain</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Success Rate</p>
                    <p className="text-2xl font-bold text-purple-400">
                      {agentStatus?.successRate}%
                    </p>
                  </div>
                  <Target className="h-8 w-8 text-purple-400" />
                </div>
                <div className="flex items-center mt-2">
                  <CheckCircle2 className="h-4 w-4 text-green-400 mr-1" />
                  <span className="text-sm text-slate-300">
                    {agentStatus?.totalTrades} total trades
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Last Action</p>
                    <p className="text-lg font-bold text-white">
                      {agentStatus?.lastAction.toLocaleTimeString()}
                    </p>
                  </div>
                  <Activity className="h-8 w-8 text-orange-400" />
                </div>
                <div className="flex items-center mt-2">
                  <Clock className="h-4 w-4 text-slate-400 mr-1" />
                  <span className="text-sm text-slate-400">
                    {Math.floor((Date.now() - (agentStatus?.lastAction.getTime() || 0)) / 60000)}m ago
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Agent Control Panel</span>
                    <div className="flex space-x-2">
                      <Button
                        onClick={toggleAgent}
                        className={`${agentStatus?.isActive ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}`}
                      >
                        {agentStatus?.isActive ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                        {agentStatus?.isActive ? 'Pause' : 'Start'} Agent
                      </Button>
                      <Button variant="outline" className="border-slate-600">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-slate-300 mb-2 block">Trading Mode</label>
                      <div className="flex space-x-2">
                        {["conservative", "balanced", "aggressive"].map((mode) => (
                          <Button
                            key={mode}
                            variant={agentStatus?.mode === mode ? "default" : "outline"}
                            onClick={() => changeAgentMode(mode as "aggressive" | "conservative" | "balanced")}
                            className={`${agentStatus?.mode === mode ? getModeColor(mode) : 'border-slate-600'}`}
                          >
                            {mode.charAt(0).toUpperCase() + mode.slice(1)}
                          </Button>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <Input
                        placeholder="Symbol"
                        value={pendingOrder.symbol}
                        onChange={(e) => setPendingOrder(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                      <Select value={pendingOrder.action} onValueChange={(value) => setPendingOrder(prev => ({ ...prev, action: value as "BUY" | "SELL" }))}>
                        <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-700 border-slate-600">
                          <SelectItem value="BUY">BUY</SelectItem>
                          <SelectItem value="SELL">SELL</SelectItem>
                        </SelectContent>
                      </Select>
                      <Input
                        type="number"
                        placeholder="Quantity"
                        value={pendingOrder.quantity || ""}
                        onChange={(e) => setPendingOrder(prev => ({ ...prev, quantity: parseInt(e.target.value) || 0 }))}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                      <Button onClick={submitOrder} className="bg-orange-600 hover:bg-orange-700">
                        <Zap className="h-4 w-4 mr-2" />
                        Execute
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="h-5 w-5 text-blue-400" />
                    <span>Recent Trades</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-64">
                    <div className="space-y-3">
                      {recentTrades.map((trade) => (
                        <div key={trade.id} className="p-4 rounded-lg bg-slate-700/50">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-3">
                              <Badge className={trade.action === "BUY" ? "bg-green-600" : "bg-red-600"}>
                                {trade.action}
                              </Badge>
                              <span className="font-bold text-white">{trade.symbol}</span>
                              <span className="text-slate-300">{trade.quantity} shares</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Badge className={getStatusColor(trade.status)}>
                                {trade.status}
                              </Badge>
                              <Badge variant="outline" className="border-slate-600 text-slate-300">
                                {Math.round(trade.confidence * 100)}%
                              </Badge>
                            </div>
                          </div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-slate-300">${trade.price.toFixed(2)}</span>
                            <span className="text-xs text-slate-500">
                              {trade.timestamp.toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm text-slate-400">{trade.reasoning}</p>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Brain className="h-5 w-5 text-purple-400" />
                  <span>Agent Thoughts</span>
                  {isSimulating && (
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <span className="text-xs text-green-400">LIVE</span>
                    </div>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {agentThoughts.map((thought) => (
                      <div key={thought.id} className="p-3 rounded-lg bg-slate-700/50">
                        <div className="flex items-start space-x-3">
                          <div className="mt-1">
                            {getThoughtIcon(thought.type)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <Badge variant="outline" className="border-slate-600 text-xs">
                                {thought.type}
                              </Badge>
                              <div className="flex items-center space-x-2">
                                {thought.relatedSymbol && (
                                  <Badge className="bg-blue-600 text-white text-xs">
                                    {thought.relatedSymbol}
                                  </Badge>
                                )}
                                <span className="text-xs text-slate-500">
                                  {Math.round(thought.confidence * 100)}%
                                </span>
                              </div>
                            </div>
                            <p className="text-sm text-slate-300 mb-1">{thought.content}</p>
                            <span className="text-xs text-slate-500">
                              {thought.timestamp.toLocaleTimeString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}