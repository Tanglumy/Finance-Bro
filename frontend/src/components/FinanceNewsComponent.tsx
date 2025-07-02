import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Newspaper, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  ExternalLink,
  Filter,
  BarChart3,
  Heart,
  Eye
} from "lucide-react";

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: Date;
  url: string;
  sentiment: "positive" | "negative" | "neutral";
  relevanceScore: number;
  category: string;
  symbols: string[];
  isBookmarked: boolean;
  readCount: number;
}

interface MarketTrend {
  symbol: string;
  change: number;
  changePercent: number;
  sentiment: "bullish" | "bearish" | "neutral";
  newsCount: number;
}

export function FinanceNewsComponent() {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [trends, setTrends] = useState<MarketTrend[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [bookmarkedOnly, setBookmarkedOnly] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMockData();
  }, []);

  const loadMockData = () => {
    setLoading(true);
    
    setTimeout(() => {
      const mockNews: NewsArticle[] = [
        {
          id: "1",
          title: "Apple Reports Record Q4 Earnings, Beats Analyst Expectations",
          summary: "Apple Inc. reported quarterly earnings that exceeded Wall Street expectations, driven by strong iPhone sales and services revenue growth.",
          source: "Bloomberg",
          publishedAt: new Date(Date.now() - 1000 * 60 * 30),
          url: "#",
          sentiment: "positive",
          relevanceScore: 0.95,
          category: "earnings",
          symbols: ["AAPL"],
          isBookmarked: false,
          readCount: 1247
        },
        {
          id: "2",
          title: "Federal Reserve Signals Potential Rate Cuts in 2024",
          summary: "Fed Chair Powell indicated a more dovish stance, suggesting the central bank may begin cutting interest rates if inflation continues to decline.",
          source: "Reuters",
          publishedAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
          url: "#",
          sentiment: "positive",
          relevanceScore: 0.92,
          category: "monetary-policy",
          symbols: ["SPY", "QQQ"],
          isBookmarked: true,
          readCount: 2103
        },
        {
          id: "3",
          title: "Tesla Faces Production Challenges Amid Supply Chain Disruptions",
          summary: "Tesla reported lower-than-expected delivery numbers for the quarter, citing ongoing supply chain issues and component shortages.",
          source: "CNBC",
          publishedAt: new Date(Date.now() - 1000 * 60 * 60 * 4),
          url: "#",
          sentiment: "negative",
          relevanceScore: 0.88,
          category: "automotive",
          symbols: ["TSLA"],
          isBookmarked: false,
          readCount: 892
        },
        {
          id: "4",
          title: "Nvidia's AI Chip Demand Continues to Surge in Q4",
          summary: "Nvidia reported exceptional demand for its AI processors, with data center revenue growing 200% year-over-year.",
          source: "TechCrunch",
          publishedAt: new Date(Date.now() - 1000 * 60 * 60 * 6),
          url: "#",
          sentiment: "positive",
          relevanceScore: 0.94,
          category: "technology",
          symbols: ["NVDA"],
          isBookmarked: true,
          readCount: 1556
        },
        {
          id: "5",
          title: "Banking Sector Outlook: Rising Interest Rates Benefit Margins",
          summary: "Major banks expected to benefit from higher interest rates, with improved net interest margins driving profitability.",
          source: "Financial Times",
          publishedAt: new Date(Date.now() - 1000 * 60 * 60 * 8),
          url: "#",
          sentiment: "positive",
          relevanceScore: 0.87,
          category: "banking",
          symbols: ["JPM", "BAC", "WFC"],
          isBookmarked: false,
          readCount: 743
        }
      ];

      const mockTrends: MarketTrend[] = [
        { symbol: "AAPL", change: 2.45, changePercent: 1.32, sentiment: "bullish", newsCount: 23 },
        { symbol: "TSLA", change: -8.92, changePercent: -3.21, sentiment: "bearish", newsCount: 18 },
        { symbol: "NVDA", change: 15.67, changePercent: 2.89, sentiment: "bullish", newsCount: 31 },
        { symbol: "MSFT", change: 1.23, changePercent: 0.45, sentiment: "neutral", newsCount: 12 },
        { symbol: "GOOGL", change: -2.34, changePercent: -1.67, sentiment: "bearish", newsCount: 15 }
      ];

      setNews(mockNews);
      setTrends(mockTrends);
      setLoading(false);
    }, 1000);
  };

  const filteredNews = news.filter(article => {
    const matchesSearch = article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         article.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         article.symbols.some(symbol => symbol.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesCategory = selectedCategory === "all" || article.category === selectedCategory;
    const matchesBookmark = !bookmarkedOnly || article.isBookmarked;
    
    return matchesSearch && matchesCategory && matchesBookmark;
  });

  const toggleBookmark = (articleId: string) => {
    setNews(prev => prev.map(article => 
      article.id === articleId 
        ? { ...article, isBookmarked: !article.isBookmarked }
        : article
    ));
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive": return <TrendingUp className="h-4 w-4 text-green-400" />;
      case "negative": return <TrendingDown className="h-4 w-4 text-red-400" />;
      default: return <BarChart3 className="h-4 w-4 text-yellow-400" />;
    }
  };


  const getTrendIcon = (sentiment: string) => {
    switch (sentiment) {
      case "bullish": return <TrendingUp className="h-4 w-4 text-green-400" />;
      case "bearish": return <TrendingDown className="h-4 w-4 text-red-400" />;
      default: return <BarChart3 className="h-4 w-4 text-yellow-400" />;
    }
  };

  const categories = [
    { value: "all", label: "All Categories" },
    { value: "earnings", label: "Earnings" },
    { value: "monetary-policy", label: "Monetary Policy" },
    { value: "technology", label: "Technology" },
    { value: "automotive", label: "Automotive" },
    { value: "banking", label: "Banking" }
  ];

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-blue-400">
            <Newspaper className="h-5 w-5" />
            <span>AI-Powered Finance News Recommendations</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1">
              <Input
                placeholder="Search news, symbols, or topics..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white placeholder-slate-400"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={bookmarkedOnly ? "default" : "outline"}
                onClick={() => setBookmarkedOnly(!bookmarkedOnly)}
                className="border-slate-600"
              >
                <Heart className={`h-4 w-4 ${bookmarkedOnly ? 'text-white' : 'text-slate-400'}`} />
                Bookmarked
              </Button>
              <Button
                onClick={loadMockData}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Filter className="h-4 w-4" />
                Refresh
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            {categories.map(category => (
              <Badge
                key={category.value}
                variant={selectedCategory === category.value ? "default" : "outline"}
                className={`cursor-pointer transition-colors ${
                  selectedCategory === category.value 
                    ? "bg-blue-600 text-white" 
                    : "border-slate-600 text-slate-300 hover:bg-slate-700"
                }`}
                onClick={() => setSelectedCategory(category.value)}
              >
                {category.label}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Recommended News</span>
                <Badge variant="outline" className="border-slate-600 text-slate-300">
                  {filteredNews.length} articles
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {loading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
                      <p className="text-slate-400 mt-2">Loading latest news...</p>
                    </div>
                  ) : filteredNews.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">
                      <Newspaper className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>No articles match your current filters</p>
                    </div>
                  ) : (
                    filteredNews.map((article) => (
                      <div key={article.id} className="p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700/70 transition-colors">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {getSentimentIcon(article.sentiment)}
                            <span className="text-sm font-medium text-slate-300">{article.source}</span>
                            <Badge variant="outline" className="border-slate-600 text-xs">
                              {Math.round(article.relevanceScore * 100)}% match
                            </Badge>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleBookmark(article.id)}
                              className="text-slate-400 hover:text-white"
                            >
                              <Heart className={`h-4 w-4 ${article.isBookmarked ? 'fill-red-400 text-red-400' : ''}`} />
                            </Button>
                            <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        
                        <h3 className="font-semibold text-white mb-2 line-clamp-2">{article.title}</h3>
                        <p className="text-sm text-slate-300 mb-3 line-clamp-3">{article.summary}</p>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <div className="flex flex-wrap gap-1">
                              {article.symbols.map(symbol => (
                                <Badge key={symbol} className="bg-blue-600 text-white text-xs">
                                  {symbol}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center space-x-3 text-xs text-slate-400">
                            <div className="flex items-center space-x-1">
                              <Eye className="h-3 w-3" />
                              <span>{article.readCount}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <Clock className="h-3 w-3" />
                              <span>{article.publishedAt.toLocaleTimeString()}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
                <span>Trending Symbols</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {trends.map((trend) => (
                  <div key={trend.symbol} className="flex items-center justify-between p-3 rounded-lg bg-slate-700/50">
                    <div className="flex items-center space-x-3">
                      {getTrendIcon(trend.sentiment)}
                      <div>
                        <div className="font-medium text-white">{trend.symbol}</div>
                        <div className="text-xs text-slate-400">{trend.newsCount} articles</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${trend.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {trend.change >= 0 ? '+' : ''}{trend.change.toFixed(2)}
                      </div>
                      <div className={`text-xs ${trend.changePercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {trend.changePercent >= 0 ? '+' : ''}{trend.changePercent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-purple-400" />
                <span>Market Sentiment</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">Positive</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 h-2 bg-slate-700 rounded">
                      <div className="h-full bg-green-400 rounded" style={{ width: '68%' }}></div>
                    </div>
                    <span className="text-sm text-green-400">68%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">Neutral</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 h-2 bg-slate-700 rounded">
                      <div className="h-full bg-yellow-400 rounded" style={{ width: '20%' }}></div>
                    </div>
                    <span className="text-sm text-yellow-400">20%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">Negative</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 h-2 bg-slate-700 rounded">
                      <div className="h-full bg-red-400 rounded" style={{ width: '12%' }}></div>
                    </div>
                    <span className="text-sm text-red-400">12%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}