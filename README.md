# 🧐 Finance-Bro

**Your finance bro for trading and investing.**
An open-source AI-powered system for personal and professional financial decision-making, combining portfolio management, time series analysis, research automation, and agent-based execution.

---

## 📺 Project Vision

Finance-Bro aims to become your **AI assistant for financial autonomy** — from generating alpha to executing trades, and reflecting on performance using reasoning-based models.

---

## 🛉️ Key Modules (Planned)

### 📊 Portfolio Management

* Track holdings, performance, and risk
* Visualizations for asset allocation and returns
* API integrations with brokers and data providers

### ⏱️ Time Series Analysis

* Advanced forecasting of price movements
* Volatility, seasonality, and trend detection
* Anomaly and regime shift analysis
* time series reasoning component: based on the time series data and news to generate the insights, fused Chain of Thought reasoning

### 🧠 Deep Research (Agent-based)

* Autonomous agent to scrape news, reports, filings
* LLM-powered summarization into a structured **Research Database**
* Retrieval-augmented generation (RAG) for insights

### 🖐 Formula Language for Modeling

* Custom DSL to express models like:

  ```
  price = MA(close, 20) + momentum(volume)
  ```
* Backtesting and diagnostics via formula interpreter
* 
### 🤖 Executive Agent (Trading Agent)

* Interact with **IBKR API** for:

  * Order placement
  * Portfolio rebalancing
  * Strategy execution

### 🔁 Reflective Reasoning Loop

* Evaluate trading outcomes using a **reasoning model**
* Regenerate or adjust strategies based on inferred “reward”
* Aim: Continuous improvement via capital market feedback

---

## 🏗️ System Design (WIP)

```
[User Interface]
      ↓
[Finance-Bro Core]
 ├─ Portfolio Tracker
 ├─ Time Series Engine
 ├─ Research Agent
 ├─ Formula Engine
 ├─ Execution Agent
 └─ Reflective Reasoning Module
      ↓
[IBKR / Market Data APIs]
```

* Modular design for research, modeling, execution, and self-feedback
* Built with Python, LLMs, and broker APIs
* Inspired by agentic design patterns (AutoGPT, LangGraph)

---

## 🚧 Status

The project is in early development (WIP).
Community contributions, ideas, and feedback are welcome!

---

## 🚀 Getting Started

Finance-Bro consists of a modern React frontend and a Python FastAPI backend with advanced time series prediction capabilities.

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.11+**
- Git

### Quick Start

#### Option 1: Using Makefile (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd Finance-Bro

# Start both frontend and backend
make dev
```

#### Option 2: Manual Setup

**Backend Setup:**
```bash
cd backend

# Install Python dependencies
pip3 install -r requirements.txt
# Or install enhanced TS agent dependencies
pip3 install yfinance pandas-ta scikit-learn nixtla statsforecast neuralforecast gluonts

# Set environment variables (optional)
export NIXTLA_API_KEY="your_nixtla_api_key"        # For TimeGPT access
export ALPHA_VANTAGE_API_KEY="your_av_key"         # Premium market data
export USE_IBKR="true"                             # IBKR real-time data

# Run the comprehensive API server
python3 comprehensive_api.py
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

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8001](http://localhost:8001)
- **API Documentation**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **ReDoc**: [http://localhost:8001/redoc](http://localhost:8001/redoc)

### 📊 Enhanced Time Series Agent

The upgraded TS Agent includes state-of-the-art forecasting models:

**Available Models:**
- **Foundation Models**: Nixtla TimeGPT-1, TimeGPT-Long-Horizon
- **Deep Learning**: GluonTS DeepAR, Transformer, SimpleFeedForward
- **Neural Networks**: NBEATS, NHITS, PatchTST, iTransformer, TimesNet
- **Statistical**: AutoARIMA, AutoETS, MSTL, SeasonalNaive
- **Machine Learning**: RandomForest, GradientBoosting, Linear models
- **Ensemble**: Adaptive weighted averaging with performance tracking

**TS Agent Endpoints:**
- `POST /ts/predict` - Single symbol prediction
- `POST /ts/predict/batch` - Batch predictions for multiple symbols
- `GET /ts/forecast/{symbol}` - Detailed forecasts with confidence intervals
- `POST /ts/portfolio/optimize` - Portfolio optimization using predictions
- `POST /ts/risk/assess` - Comprehensive risk assessment
- `GET /ts/trends/{symbol}` - Market trend analysis
- `GET /ts/volatility/{symbol}` - Volatility forecasting
- `GET /ts/models/available` - Available prediction models
- `GET /ts/data/{symbol}/history` - Historical data with technical indicators

**Test the TS Agent:**
```bash
cd backend

# Basic functionality test (no external dependencies)
python3 test_basic_ts_agent.py

# Comprehensive test (requires ML libraries)
python3 test_enhanced_ts_agent.py

# Run standalone TS Agent API
python3 run_ts_agent.py  # Available at http://localhost:8002
```

### 🔧 Development Commands

**Frontend:**
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run linting
```

**Backend:**
```bash
cd backend
python3 comprehensive_api.py     # Full API with TS Agent
python3 simple_app.py           # Basic API server
python3 run_ts_agent.py         # TS Agent only
```

### 🏗️ Building for Production

```bash
# Build frontend
cd frontend
npm run build

# Build backend (ensure dependencies are installed)
cd backend
pip3 install -r requirements.txt
```

### 🐳 Docker Support (Coming Soon)

```bash
# Full stack deployment
docker-compose up

# Individual services
docker-compose up frontend
docker-compose up backend
```

---

## 📜 License

[MIT License](LICENSE)




## 📋 API Examples

### Time Series Predictions

```bash
# Single symbol prediction
curl -X POST "http://localhost:8001/ts/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "horizon": 30,
    "models": ["statistical", "ml", "timegpt"],
    "include_technical": true,
    "include_market_features": true
  }'

# Batch predictions
curl -X POST "http://localhost:8001/ts/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "horizon": 30,
    "models": ["statistical", "neural"]
  }'

# Portfolio optimization
curl -X POST "http://localhost:8001/ts/portfolio/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA"],
    "optimization_method": "max_sharpe",
    "horizon": 30
  }'
```

### Market Analysis

```bash
# Get market quotes
curl "http://localhost:8001/market/quotes?symbols=AAPL,MSFT,GOOGL"

# Technical indicators
curl "http://localhost:8001/market/technical/AAPL?indicators=RSI,MACD,SMA"

# Market sentiment
curl "http://localhost:8001/market/sentiment"
```

## 🎯 Features

### ✅ **Completed Features**

- **📊 Portfolio Management**: Real-time tracking, P&L calculation, position management
- **📈 Time Series Analysis**: State-of-the-art forecasting with 8+ model types
- **📰 News & Research**: Financial news aggregation and sentiment analysis  
- **🤖 Trading Agent**: Automated trading signals and execution simulation
- **💼 Risk Management**: Comprehensive risk assessment and alerts
- **🏆 Rewards System**: Performance tracking and achievement system
- **📱 Modern UI**: React + TypeScript with shadcn/ui components
- **🔄 Real-time Data**: WebSocket connections for live market updates
- **🔗 API Integration**: IBKR, Yahoo Finance, Alpha Vantage support

### 🔄 **Enhanced Time Series Engine**

- **Foundation Models**: Nixtla TimeGPT with fine-tuning capabilities
- **Deep Learning**: GluonTS DeepAR, Transformer models
- **Neural Networks**: NBEATS, NHITS, PatchTST, iTransformer, TimesNet
- **Statistical Models**: AutoARIMA, AutoETS, MSTL with seasonal patterns
- **ML Algorithms**: RandomForest, GradientBoosting with feature engineering
- **Ensemble Methods**: Adaptive weighted averaging with performance tracking
- **Technical Analysis**: 15+ indicators (RSI, MACD, Bollinger Bands, etc.)
- **Market Features**: Volatility, momentum, regime detection
- **Risk Scenarios**: Bull/bear/sideways market projections

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Optional: Enhanced forecasting with TimeGPT
NIXTLA_API_KEY=your_nixtla_api_key

# Optional: Premium market data
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Optional: Real-time IBKR integration
USE_IBKR=true
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# Optional: News data
NEWS_API_KEY=your_news_api_key
```

### Frontend Configuration

The frontend automatically connects to the backend API. Configuration is handled in `frontend/src/services/api.ts`.

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │
│   (React/TS)    │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
            ┌───────▼───┐ ┌────▼────┐ ┌───▼────┐
            │Event Agent│ │TS Agent │ │Research│
            │(Trading)  │ │(ML/AI)  │ │ Agent  │
            └───────────┘ └─────────┘ └────────┘
                    │          │          │
            ┌───────▼──────────▼──────────▼────┐
            │     External Data Sources        │
            │  (IBKR, Yahoo, Alpha Vantage)   │
            └─────────────────────────────────┘
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `npm test` (frontend) and `python -m pytest` (backend)
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📈 Roadmap

- [ ] **Docker Containerization**: Complete Docker setup for easy deployment
- [ ] **Advanced ML Models**: Transformer-based models for better predictions
- [ ] **Real-time Trading**: Live trading integration with multiple brokers
- [ ] **Mobile App**: React Native mobile application
- [ ] **Advanced Analytics**: More sophisticated risk and performance metrics
- [ ] **Paper Trading**: Full simulation environment
- [ ] **Multi-asset Support**: Crypto, forex, commodities, options
- [ ] **Social Features**: Community signals and shared strategies