export interface AnalysisRequest {
  message: string;
  portfolio_data?: Record<string, any>;
  risk_tolerance?: string;
  investment_horizon?: string;
}

export interface AnalysisResponse {
  analysis: string;
  market_events: Array<Record<string, any>>;
  trading_signals: Array<Record<string, any>>;
  portfolio_recommendations: Array<Record<string, any>>;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
}

export interface AgentConfiguration {
  [key: string]: any;
}

class ApiService {
  private baseUrl = '/api';

  async analyzeMarketEvents(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getHealthStatus(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getConfiguration(): Promise<AgentConfiguration> {
    const response = await fetch(`${this.baseUrl}/config`);
    
    if (!response.ok) {
      throw new Error(`Config fetch failed: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiService = new ApiService();