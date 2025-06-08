graph TD
  %% ─── Client Layer ───
  subgraph Client
    A[Web (Next .js + React)] 
    B[Mobile (Flutter)]
  end
  %% ─── Edge/API Layer ───
  subgraph Edge
    G[API Gateway<br/>FastAPI + GraphQL<br/>+ gRPC/HTTP2] 
    WS[Realtime Hub<br/>WS / GraphQL Sub]
    Auth[AuthN/Z<br/>OAuth2 + OIDC + RBAC]
  end
  %% ─── Core Services ───
  subgraph Core
    STRAT[Strategy Svc<br/>DSL → Graph]
    PORT[Portfolio Svc]
    LLM[LLM Svc<br/>Writer/Judge]
    BK[Backtest Cluster<br/>Ray + DuckDB]
    EXEC[Execution Svc<br/>IBKR FIX/REST]
    KB[(Signal & Insight Graph<br/>Postgres + Qdrant + Neo4j)]
  end
  %% ─── Data / Infra ───
  subgraph DataInfra
    DL[S3 Data Lake<br/>Parquet / Delta]
    STREAM[Kafka / Redpanda]
    CACHE[Redis / KeyDB]
    METRICS[Prometheus<br/>+ Grafana]
  end

  %% Flows
  A -->|GraphQL| G
  B -->|GraphQL| G
  G --> Auth
  G --> WS
  G --> STRAT
  G --> PORT
  G --> LLM
  STRAT --> BK
  BK --> KB
  LLM --> KB
  PORT --> EXEC
  EXEC --> KB
  EXEC --> STREAM
  STREAM --> PORT
  STREAM --> WS
  DL --> BK
  DL --> LLM
  KB --> STRAT
  KB --> LLM
  KB --> PORT
  CACHE <--> Core
  METRICS -->|scrape| Core