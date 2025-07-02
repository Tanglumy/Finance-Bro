import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Brain, Send, Loader2, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";
import { apiService, AnalysisRequest, AnalysisResponse } from "@/services/api";

export function AnalysisComponent() {
  const [message, setMessage] = useState("");
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [investmentHorizon, setInvestmentHorizon] = useState("medium");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!message.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const request: AnalysisRequest = {
        message: message.trim(),
        risk_tolerance: riskTolerance,
        investment_horizon: investmentHorizon,
        portfolio_data: {}
      };

      const response = await apiService.analyzeMarketEvents(request);
      setAnalysis(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-emerald-400">
            <Brain className="h-5 w-5" />
            <span>AI Market Analysis</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-slate-300 mb-2 block">Analysis Request</label>
            <Textarea
              placeholder="Ask about market conditions, specific stocks, or request portfolio analysis..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="bg-slate-700 border-slate-600 text-white min-h-[100px]"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-300 mb-2 block">Risk Tolerance</label>
              <Select value={riskTolerance} onValueChange={setRiskTolerance}>
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="conservative">Conservative</SelectItem>
                  <SelectItem value="moderate">Moderate</SelectItem>
                  <SelectItem value="aggressive">Aggressive</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm text-slate-300 mb-2 block">Investment Horizon</label>
              <Select value={investmentHorizon} onValueChange={setInvestmentHorizon}>
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="short">Short Term (&lt; 1 year)</SelectItem>
                  <SelectItem value="medium">Medium Term (1-5 years)</SelectItem>
                  <SelectItem value="long">Long Term (&gt; 5 years)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={loading || !message.trim()}
            className="w-full bg-emerald-600 hover:bg-emerald-700"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Send className="h-4 w-4 mr-2" />
            )}
            Analyze Market
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Card className="bg-red-900/20 border-red-700">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-red-400">
              <AlertTriangle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {analysis && (
        <div className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-emerald-400">Analysis Results</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                <div className="prose prose-invert max-w-none">
                  <p className="text-slate-300 whitespace-pre-wrap">{analysis.analysis}</p>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {analysis.market_events.length > 0 && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-blue-400">
                  <TrendingUp className="h-5 w-5" />
                  <span>Market Events</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analysis.market_events.map((event, index) => (
                    <div key={index} className="p-3 rounded-lg bg-slate-700/50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-white">{event.title || `Event ${index + 1}`}</h4>
                          <p className="text-sm text-slate-300 mt-1">{event.description || JSON.stringify(event)}</p>
                        </div>
                        {event.impact && (
                          <Badge className={`ml-2 ${
                            event.impact === 'positive' ? 'bg-green-600' : 
                            event.impact === 'negative' ? 'bg-red-600' : 'bg-yellow-600'
                          }`}>
                            {event.impact}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {analysis.trading_signals.length > 0 && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-purple-400">
                  <CheckCircle className="h-5 w-5" />
                  <span>Trading Signals</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analysis.trading_signals.map((signal, index) => (
                    <div key={index} className="p-3 rounded-lg bg-slate-700/50">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold text-white">{signal.symbol || `Signal ${index + 1}`}</h4>
                          <p className="text-sm text-slate-300">{signal.action || signal.description || JSON.stringify(signal)}</p>
                        </div>
                        {signal.confidence && (
                          <Badge variant="outline" className="border-slate-600">
                            {Math.round(signal.confidence * 100)}%
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {analysis.portfolio_recommendations.length > 0 && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-orange-400">
                  <TrendingUp className="h-5 w-5" />
                  <span>Portfolio Recommendations</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analysis.portfolio_recommendations.map((rec, index) => (
                    <div key={index} className="p-3 rounded-lg bg-slate-700/50">
                      <h4 className="font-semibold text-white">{rec.title || `Recommendation ${index + 1}`}</h4>
                      <p className="text-sm text-slate-300 mt-1">{rec.description || JSON.stringify(rec)}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}