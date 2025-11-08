# 🤖 给 Claude 的任务: 升级 Executive Agent

## 📋 背景

Finance Bro 项目的 Executive Agent 目前功能较弱,需要升级为一个真正智能的 AI 驱动交易执行系统。

**当前代码位置**: `/Users/tanglu/Finance-Bro/backend/src/EventAgent/executive_agent.py`

## 🎯 你的任务

将现有的基础 Executive Agent 升级为具有以下能力的智能系统:

### 1️⃣ 添加 LLM 决策能力

当前问题:订单执行只有简单的风险检查,没有智能分析。

**要求**:
- 在执行前,使用 LLM 分析当前市场环境
- 根据市场状态、波动率、流动性选择最优执行策略
- 集成 EventAgent 检测的市场事件到决策中

**实现提示**:
```python
class MarketEnvironmentAnalyzer:
    """使用 LLM 分析市场环境,指导执行策略"""
    
    def __init__(self, llm_model: str = "gemini-2.0-flash-exp"):
        self.llm = ChatGoogleGenerativeAI(model=llm_model, temperature=0.1)
    
    async def analyze_market_for_execution(
        self,
        order: TradingOrder,
        market_data: Dict[str, Any],
        detected_events: List[Dict[str, Any]]
    ) -> ExecutionStrategy:
        """
        分析市场并返回推荐的执行策略
        
        Prompt 应包含:
        1. 订单详情(资产、数量、方向)
        2. 当前市场数据(价格、波动率、成交量)
        3. 最近检测的市场事件
        4. 流动性评估
        
        返回:
        - 推荐策略: MARKET/LIMIT/TWAP/VWAP/ADAPTIVE
        - 执行参数: 价格限制、时间窗口、拆分数量等
        - 风险评估
        - 详细推理
        """
        prompt = f"""
你是专业交易执行分析师。分析以下订单的最优执行策略:

订单信息:
- 资产: {order.symbol}
- 方向: {order.action.value}
- 数量: {order.quantity}

市场数据:
- 当前价格: {market_data.get('price')}
- 5分钟波动率: {market_data.get('volatility')}
- 平均成交量: {market_data.get('avg_volume')}
- 买卖价差: {market_data.get('spread')}

检测到的市场事件:
{json.dumps(detected_events, indent=2)}

请分析并推荐:
1. 最优执行策略(MARKET/LIMIT/TWAP/VWAP)
2. 具体执行参数
3. 风险因素
4. 详细推理

以 JSON 格式输出:
{{
    "recommended_strategy": "TWAP",
    "market_assessment": {{
        "state": "volatile",
        "liquidity": "medium",
        "execution_difficulty": 0.6
    }},
    "execution_params": {{
        "order_type": "LIMIT",
        "slice_count": 5,
        "duration_minutes": 30,
        "price_limit": 150.5
    }},
    "risk_factors": ["高波动率可能导致滑点"],
    "reasoning": "当前市场波动较大,建议使用 TWAP 策略分散执行,降低市场冲击..."
}}
"""
        # 调用 LLM
        response = await self.llm.ainvoke([SystemMessage(content=prompt)])
        # 解析并返回
        return json.loads(response.content)
```

### 2️⃣ 实现高级执行算法

**要求实现**:

#### A. TWAP 执行器 (时间加权平均价格)
```python
class TWAPExecutor:
    """
    将大订单拆分成多个小订单,在指定时间内均匀执行
    
    核心逻辑:
    1. 计算每份订单的大小: total_qty / slice_count
    2. 计算时间间隔: duration / slice_count
    3. 按时间间隔依次执行每份订单
    4. 实时监控执行效果,出现异常时调整策略
    """
    
    async def execute(
        self,
        order: TradingOrder,
        duration_minutes: int,
        slice_count: int
    ) -> List[ExecutionResult]:
        """
        TWAP 执行流程:
        1. 拆分订单
        2. 循环执行每一份
        3. 每次执行后分析市场变化
        4. 必要时调用 LLM 调整策略
        """
        pass
```

#### B. 自适应执行器
```python
class AdaptiveExecutor:
    """
    最智能的执行器,每一步都咨询 LLM
    
    执行流程:
    1. 执行一部分订单
    2. 分析执行效果(滑点、市场反应)
    3. 咨询 LLM: 继续/加速/减速/取消?
    4. 根据 LLM 建议调整
    5. 循环直到完成
    """
    
    async def execute_with_llm_guidance(
        self,
        order: TradingOrder
    ) -> ExecutionResult:
        """
        每执行一步,都用 LLM 评估:
        - 当前执行效果如何?
        - 市场有什么变化?
        - 应该继续、加速还是暂停?
        """
        pass
```

### 3️⃣ 集成市场事件响应

**要求**:
- 监听 EventAgent 检测到的市场事件
- 当事件影响当前执行时,动态调整策略
- 使用 LLM 评估事件影响

```python
class EventDrivenExecutionManager:
    """
    响应市场事件,调整执行策略
    """
    
    async def on_market_event(
        self,
        event: Dict[str, Any],
        active_orders: List[TradingOrder]
    ):
        """
        当检测到市场事件时:
        1. 使用 LLM 分析事件对当前执行的影响
        2. 决定是否需要调整策略
        3. 如需调整,生成新的执行计划
        
        例如:
        - 突发负面新闻 -> 暂停买入,加速卖出
        - 波动率飙升 -> 从市价单切换到限价单
        - 流动性枯竭 -> 减少订单规模
        """
        for order in active_orders:
            if self._is_order_affected(order, event):
                # 咨询 LLM
                impact = await self._analyze_event_impact(event, order)
                
                if impact["requires_action"]:
                    await self._adjust_execution(order, impact)
```

### 4️⃣ 动态风险管理

**要求**:
- 不再使用固定风险参数
- 根据市场状态动态调整风险限制
- 危机时收紧,正常时放宽

```python
class AdaptiveRiskManager:
    """
    基于市场状态动态调整风险参数
    """
    
    async def get_risk_params_for_market_state(
        self,
        market_state: str,  # "normal", "volatile", "crisis"
        recent_events: List[Dict[str, Any]]
    ) -> RiskParameters:
        """
        使用 LLM 分析市场状态,返回适应的风险参数
        
        示例:
        - 正常市场: 最大持仓 10%, 止损 5%
        - 高波动: 最大持仓 5%, 止损 3%
        - 危机模式: 最大持仓 2%, 止损 2%
        """
        prompt = f"""
市场状态: {market_state}
最近事件: {recent_events}

基础风险参数:
- 最大持仓: 10%
- 日最大亏损: 2%
- 止损: 5%

请根据当前市场状态调整这些参数。
危机时应更保守,正常时可适度放宽。

输出调整后的参数(JSON格式)。
"""
        # 调用 LLM,返回调整后的参数
```

### 5️⃣ 集成到 LangGraph 工作流

**要求**:
- 修改 `src/EventAgent/graph.py`
- 在信号生成后添加执行节点
- 实现完整的 "事件检测 -> 信号生成 -> 智能执行 -> 监控调整" 流程

```python
def create_enhanced_event_agent_graph():
    """
    增强的 EventAgent 工作流,包含智能执行
    """
    graph = StateGraph(EventAgentState)
    
    # 现有节点
    graph.add_node("detect_events", detect_market_events)
    graph.add_node("analyze_portfolio", analyze_portfolio_state)
    graph.add_node("generate_signals", generate_trading_signals)
    
    # 新增执行节点
    graph.add_node("plan_execution", plan_execution_strategy)  # 规划执行策略
    graph.add_node("execute_orders", execute_orders_intelligently)  # 智能执行
    graph.add_node("monitor_execution", monitor_and_adjust)  # 监控与调整
    
    # 工作流连接
    graph.add_edge("generate_signals", "plan_execution")
    graph.add_edge("plan_execution", "execute_orders")
    graph.add_edge("execute_orders", "monitor_execution")
    
    # 监控节点的条件分支
    graph.add_conditional_edges(
        "monitor_execution",
        check_execution_status,
        {
            "continue_monitoring": "monitor_execution",
            "completed": END,
            "needs_replanning": "plan_execution"
        }
    )
```

### 6️⃣ 添加执行质量分析

**要求**:
- 每次执行后分析质量
- 计算滑点、市场冲击等指标
- 使用 LLM 提供改进建议

```python
class ExecutionQualityAnalyzer:
    """
    分析执行质量,提供改进建议
    """
    
    async def analyze_execution(
        self,
        order: TradingOrder,
        result: ExecutionResult,
        market_vwap: float
    ) -> Dict[str, Any]:
        """
        计算指标:
        1. 滑点 = (执行价格 - 决策价格) / 决策价格
        2. vs VWAP = (执行价格 - VWAP) / VWAP
        3. 执行时长
        4. 完成率
        
        然后用 LLM 分析:
        - 这次执行质量如何?
        - 哪里做得好?
        - 哪里可以改进?
        - 下次应该怎么做?
        """
        metrics = {
            "slippage": (result.average_price - order.price) / order.price,
            "vs_vwap": (result.average_price - market_vwap) / market_vwap,
            "fill_rate": result.filled_quantity / order.quantity
        }
        
        # LLM 分析
        analysis = await self._llm_analyze_quality(order, result, metrics)
        
        return {
            "metrics": metrics,
            "quality_score": analysis["score"],
            "strengths": analysis["strengths"],
            "improvements": analysis["improvements"]
        }
```

## 📁 文件结构建议

创建以下新文件:

```
backend/src/EventAgent/execution/
├── __init__.py
├── market_analyzer.py          # 市场环境分析器
├── strategy_selector.py        # 策略选择器
├── risk_manager.py             # 动态风险管理
├── quality_analyzer.py         # 执行质量分析
└── executors/
    ├── __init__.py
    ├── base_executor.py        # 基础执行器类
    ├── twap_executor.py        # TWAP 执行器
    ├── vwap_executor.py        # VWAP 执行器
    └── adaptive_executor.py    # 自适应执行器
```

同时修改:
- `executive_agent.py` - 重构为使用新的智能组件
- `graph.py` - 添加执行相关节点
- `state.py` - 添加执行状态字段
- `prompts.py` - 添加执行相关 prompts

## ✅ 验收标准

完成后应该能够:

1. ✅ 执行订单前,自动分析市场环境并选择最优策略
2. ✅ 支持 TWAP、VWAP、自适应等多种执行策略
3. ✅ 实时响应市场事件,动态调整执行
4. ✅ 根据市场状态自动调整风险参数
5. ✅ 执行后自动分析质量并提供改进建议
6. ✅ 与 EventAgent 工作流无缝集成

## 🚀 开始工作

请按以下顺序实施:

### Phase 1: 核心智能组件
1. 创建 `MarketEnvironmentAnalyzer` - LLM 市场分析
2. 创建 `ExecutionStrategySelector` - 策略选择逻辑
3. 测试这两个组件

### Phase 2: 执行算法
4. 实现 `TWAPExecutor`
5. 实现 `AdaptiveExecutor`
6. 测试执行器

### Phase 3: 事件响应与风险
7. 实现 `EventDrivenExecutionManager`
8. 实现 `AdaptiveRiskManager`
9. 测试事件响应

### Phase 4: 集成
10. 修改 `executive_agent.py` 使用新组件
11. 更新 `graph.py` 添加执行节点
12. 端到端测试

### Phase 5: 质量分析
13. 实现 `ExecutionQualityAnalyzer`
14. 添加执行日志和报告

## 💡 实现提示

### LLM 调用最佳实践
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
import json

# 初始化 LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.1  # 低温度,更确定性的输出
)

# 调用 LLM
async def call_llm_for_decision(prompt: str) -> Dict[str, Any]:
    response = await llm.ainvoke([SystemMessage(content=prompt)])
    return json.loads(response.content)
```

### Prompt 编写技巧
1. **明确角色**: "你是一位专业的交易执行分析师..."
2. **提供上下文**: 包含所有相关信息
3. **明确输出格式**: 要求 JSON 格式,指定字段
4. **举例说明**: 提供期望输出的示例
5. **清晰指令**: 明确说明要做什么分析

### 错误处理
```python
try:
    result = await execute_order(order)
except Exception as e:
    # 记录错误
    logger.error(f"执行失败: {e}")
    
    # 使用 LLM 分析失败原因和建议
    analysis = await analyze_execution_failure(order, e)
    
    # 返回失败结果
    return ExecutionResult(
        success=False,
        message=analysis["failure_reason"],
        suggestion=analysis["retry_suggestion"]
    )
```

## 📚 参考现有代码

可以参考项目中已有的 LLM 使用模式:
- `graph.py` 中的 `detect_market_events()` - LLM 调用示例
- `prompts.py` - Prompt 编写风格
- `state.py` - 状态管理

## 🎯 关键设计原则

1. **AI-First**: 重要决策都让 LLM 参与
2. **Event-Driven**: 深度整合市场事件
3. **Adaptive**: 根据市场动态调整
4. **Safe**: 多重风险检查
5. **Observable**: 所有决策可追溯

---

## 开始实施吧!

请从 Phase 1 开始,逐步实现以上功能。如有任何疑问,随时询问。

祝编码愉快! 🚀

