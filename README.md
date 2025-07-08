# 🚀 Finance-Bro

**Your AI-powered finance companion for intelligent trading and investing.**

An advanced open-source platform combining portfolio management, time series forecasting, custom formula modeling, research automation, and agent-based execution for both personal and professional financial decision-making.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## 🎯 Vision

Finance-Bro aims to democratize quantitative finance by providing an **AI assistant for financial autonomy** — from generating alpha through custom strategies to executing trades and continuously learning from market feedback using reasoning-based models.

---

## ✨ Core Features

### 📊 **Portfolio Management**
- **Real-time tracking** of holdings, performance, and risk metrics
- **Interactive visualizations** for asset allocation and returns
- **Multiple broker integrations** (IBKR, Yahoo Finance, Alpha Vantage)
- **P&L calculation** with detailed performance analytics

### 📈 **Advanced Time Series Engine**
- **8+ ML models**: Foundation (TimeGPT), Deep Learning (DeepAR), Neural Networks (NBEATS), Statistical (ARIMA)
- **Ensemble methods** with adaptive weighted averaging
- **Technical indicators**: 15+ indicators (RSI, MACD, Bollinger Bands, ATR, etc.)
- **Market regime detection** and volatility forecasting
- **Risk scenario analysis** (bull/bear/sideways projections)

### 🔧 **Formula Language & Modeling**
- **Custom DSL** for expressing financial models and strategies
- **50+ built-in functions** for technical analysis and mathematical operations
- **Real-time formula evaluation** against market data
- **Backtesting engine** with comprehensive performance metrics
- **Strategy optimization** and parameter tuning

### 🧠 **Research & Analysis Agents**
- **Autonomous news scraping** and financial report analysis
- **LLM-powered summarization** into structured research database
- **Sentiment analysis** and market intelligence
- **RAG-based insights** generation

### 🤖 **Executive Trading Agent**
- **Automated signal generation** based on custom formulas
- **Portfolio rebalancing** and position sizing
- **Risk management** with stop-loss and take-profit rules
- **Paper trading** simulation environment

### 🔄 **Reflective Learning Loop**
- **Performance evaluation** using reasoning models
- **Strategy adaptation** based on market feedback
- **Continuous improvement** through reward-based learning

---

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   React Frontend    │    │   FastAPI Backend   │
│   (TypeScript)      │◄──►│   (Python 3.11+)   │
└─────────────────────┘    └─────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
            ┌───────▼────┐    ┌────────▼────┐    ┌───────▼────┐
            │ Formula    │    │ Time Series │    │ Research   │
            │ Engine     │    │ Agent       │    │ Agent      │
            │ (DSL)      │    │ (ML/AI)     │    │ (LLM)      │
            └────────────┘    └─────────────┘    └────────────┘
                    │                  │                  │
            ┌───────▼──────────────────▼──────────────────▼────┐
            │              External Data Sources              │
            │     (IBKR, Yahoo Finance, Alpha Vantage)       │
            └─────────────────────────────────────────────────┘
```

**Key Components:**
- **Modular design** with independent agents
- **Event-driven architecture** with WebSocket real-time updates
- **Containerized deployment** with Docker support
- **RESTful API** with comprehensive documentation
- **Built with** FastAPI, React, LangGraph, and modern ML libraries

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd Finance-Bro

# Copy environment template
cp .env.example .env

# Start with Docker Compose
docker-compose up

# Or development mode
docker-compose -f docker-compose.dev.yml up
```

### Option 2: Local Development

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- Git

**Backend Setup:**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export NIXTLA_API_KEY="your_nixtla_api_key"
export ALPHA_VANTAGE_API_KEY="your_av_key"

# Start API server
python comprehensive_api.py
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 🌐 Access Points

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8001](http://localhost:8001)
- **API Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **ReDoc**: [http://localhost:8001/redoc](http://localhost:8001/redoc)

---

## 💡 Formula Language Examples

### Basic Technical Analysis
```python
# Simple moving average crossover
"MA(close, 20) > MA(close, 50)"

# RSI oversold/overbought
"RSI(close, 14) < 30 ? BUY : RSI(close, 14) > 70 ? SELL : HOLD"

# Bollinger Bands squeeze
"(BB(close, 20, 2).upper - BB(close, 20, 2).lower) < STD(close, 20) * 0.1"
```

### Advanced Strategies
```python
# Momentum with volume confirmation
"ROC(close, 10) > 0.05 AND volume > MA(volume, 20) * 1.5"

# Mean reversion strategy
"ABS(close - MA(close, 20)) / MA(close, 20) > 0.02 AND RSI(close, 14) < 30"

# Trend following with ADX filter
"EMA(close, 12) > EMA(close, 26) AND ADX(high, low, close, 14) > 25"

# Volatility breakout
"ATR(high, low, close, 14) > MA(ATR(high, low, close, 14), 10) * 1.2"
```

### Custom Variables
```python
# Parameterized formulas
"MA(close, fast_period) > MA(close, slow_period)"
# Variables: {"fast_period": 10, "slow_period": 20}

# RiOPENAI_API_KEY_REDACTED position sizing
"RSI(close, 14) < oversold_level ? position_size : 0"
# Variables: {"oversold_level": 25, "position_size": 0.1}
```

---

## 📋 API Reference

### Formula Engine Endpoints

```bash
# Get available functions
GET /formula/functions

# Validate formula
POST /formula/validate
{
  "formula": "MA(close, 20) > MA(close, 50)"
}

# Create trading model
POST /formula/models
{
  "name": "ma_crossover",
  "formula": "MA(close, 20) > MA(close, 50)",
  "description": "Moving average crossover strategy"
}

# Backtest strategy
POST /formula/backtest
{
  "model_name": "ma_crossover",
  "data": {...},
  "initial_capital": 100000,
  "commission": 0.001
}
```

### Time Series Endpoints

```bash
# Single prediction
POST /ts/predict
{
  "symbol": "AAPL",
  "horizon": 30,
  "models": ["statistical", "neural", "timegpt"]
}

# Portfolio optimization
POST /ts/portfolio/optimize
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "optimization_method": "max_sharpe"
}
```

### Market Data Endpoints

```bash
# Real-time quotes
GET /market/quotes?symbols=AAPL,MSFT

# Technical indicators
GET /market/technical/AAPL?indicators=RSI,MACD

# Market sentiment
GET /market/sentiment
```

---

## 🧪 Testing & Development

### Running Tests

```bash
cd backend

# Run all tests
make test_comprehensive

# Run with coverage
make test_coverage

# Run specific test suites
make test_formula      # Formula engine tests
make test_api         # API tests
make test_integration # Integration tests

# Run tests in parallel
make test_parallel

# Generate HTML coverage report
make test_coverage
```

### Development Commands

```bash
# Backend
cd backend
python run_tests.py --verbose
python comprehensive_api.py

# Frontend
cd frontend
npm run dev
npm run build
npm run lint

# Docker
docker-compose up --build
docker-compose run --rm backend python run_tests.py
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in the project root:

```bash
# API Keys (Optional)
NIXTLA_API_KEY=your_nixtla_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
NEWS_API_KEY=your_news_api_key

# IBKR Integration (Optional)
USE_IBKR=true
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# Database (Future)
DATABASE_URL=postgresql://user:pass@localhost/finance_bro

# Cache
REDIS_URL=redis://localhost:6379
```

### Docker Configuration

```bash
# Production deployment
docker-compose up

# Development with hot reload
docker-compose -f docker-compose.dev.yml up

# Scale services
docker-compose up --scale backend=3

# View logs
docker-compose logs -f backend
```

---

## 📊 Features Status

### ✅ **Implemented Features**

- **🐳 Docker Containerization**: Full production-ready setup
- **📊 Portfolio Management**: Real-time tracking and analytics
- **📈 Time Series Engine**: 8+ ML models with ensemble methods
- **🔧 Formula Language**: Complete DSL with 50+ functions
- **📰 Research Agent**: News aggregation and sentiment analysis
- **🤖 Trading Agent**: Signal generation and strategy execution
- **💼 Risk Management**: Comprehensive risk assessment
- **🏆 Performance Tracking**: Detailed metrics and reporting
- **📱 Modern UI**: React + TypeScript frontend
- **🔄 Real-time Updates**: WebSocket connections
- **🧪 Testing Framework**: Comprehensive test suite with CI/CD
- **🔗 API Integration**: Multiple data providers
- **📚 API Documentation**: Interactive Swagger/ReDoc

### 🚧 **In Development**

- **📱 Mobile App**: React Native application
- **🌐 Multi-asset Support**: Crypto, forex, commodities
- **👥 Social Features**: Community signals and strategies
- **🎯 Advanced Analytics**: Enhanced performance metrics
- **🔄 Live Trading**: Real-time broker integration
- **📊 Advanced Visualizations**: Interactive charts and dashboards

---

## 🤝 Contributing

We welcome contributions from the community! Here's how to get started:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Install** development dependencies: `make install-dev`
4. **Make** your changes
5. **Run** tests: `make test_comprehensive`
6. **Lint** code: `make lint`
7. **Commit** changes: `git commit -m 'Add amazing feature'`
8. **Push** to branch: `git push origin feature/amazing-feature`
9. **Open** a Pull Request

### Code Standards

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, follow React best practices
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update README and API docs
- **Performance**: Profile critical paths

### Areas for Contribution

- **🔌 Data Connectors**: New broker/exchange integrations
- **📊 Indicators**: Additional technical analysis functions
- **🤖 ML Models**: New forecasting algorithms
- **🎨 UI Components**: Enhanced visualizations
- **📚 Documentation**: Tutorials and examples
- **🧪 Testing**: Edge cases and integration tests

---

## 📈 Roadmap

### Q1 2024
- [ ] **Enhanced Formula Language**: More advanced functions and operators
- [ ] **Live Trading Integration**: Real-time broker connectivity
- [ ] **Mobile Application**: React Native app for iOS/Android
- [ ] **Advanced Risk Management**: Portfolio-level risk controls

### Q2 2024
- [ ] **Multi-asset Support**: Crypto, forex, commodities, options
- [ ] **Social Trading**: Community signals and strategy sharing
- [ ] **Advanced Analytics**: Sophisticated performance attribution
- [ ] **Paper Trading Competition**: Gamified trading environment

### Q3 2024
- [ ] **Institutional Features**: Multi-user support and permissions
- [ ] **Advanced ML Models**: Transformer-based price prediction
- [ ] **API Marketplace**: Third-party strategy integrations
- [ ] **Regulatory Compliance**: FINRA/SEC compliance tools

### Long-term Vision
- [ ] **AI-First Trading**: Autonomous trading agents
- [ ] **Global Markets**: International exchange support
- [ ] **Decentralized Finance**: DeFi protocol integrations
- [ ] **Educational Platform**: Trading courses and simulations

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Nixtla** for TimeGPT foundation models
- **LangGraph** for agent orchestration framework
- **FastAPI** for high-performance web framework
- **React** and **TypeScript** for modern frontend
- **Docker** for containerization
- **Open Source Community** for inspiration and libraries

---

## 📞 Support

- **Documentation**: [API Docs](http://localhost:8001/docs)
- **Issues**: [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anthropics/claude-code/discussions)
- **Email**: finance-bro@example.com

---

**Built with ❤️ by the Finance-Bro team**

*Making quantitative finance accessible to everyone*