# InfraAgent Architecture

## 🏗️ High-Level System Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                             USER INTERFACE                                  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       React Frontend (Port 5173)                      │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │
│  │  │Dashboard │  │  Alerts  │  │Approvals │  │Activities│           │  │
│  │  │          │  │          │  │          │  │          │           │  │
│  │  │ Health   │  │ Simulate │  │ Review & │  │ History  │           │  │
│  │  │ Monitor  │  │ Scenarios│  │ Approve  │  │ Rollback │           │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │  │
│  │                                                                       │  │
│  └───────────────────────────┬───────────────────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
                    WebSocket + REST API (Real-time Updates)
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                                ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              FastAPI Backend (Port 8000)                             │   │
│  │                     Orchestrator Layer                               │   │
│  │                                                                      │   │
│  │  • Workflow State Machine (8 states)                               │   │
│  │  • Event Sourcing Pattern                                          │   │
│  │  • WebSocket Manager                                               │   │
│  │  • REST API Endpoints (20+)                                        │   │
│  └─────────────────┬────────────────────────────────┬──────────────────┘   │
│                    │                                │                      │
│         ┌──────────┴──────────┐          ┌─────────┴──────────┐          │
│         │                     │          │                    │          │
│    ┌────▼─────┐      ┌───────▼──────┐   ▼                    │          │
│    │          │      │              │                         │          │
│  ┌─┴──────────┴──┐ ┌─┴──────────────┴─┐  ┌──────────────────┴───┐      │
│  │ Alert Agent   │ │ Config Agent     │  │ Action Agent          │      │
│  │               │ │                  │  │                       │      │
│  │ • Detects     │ │ • 🤖 AI-Powered │  │ • Executes approved  │      │
│  │   issues      │ │ • Analyzes alert│  │   actions             │      │
│  │ • Routes to   │ │ • Suggests fix  │  │ • Live tracking      │      │
│  │   agents      │ │ • Confidence:   │  │ • Rollback snapshots │      │
│  │               │ │   85-92%        │  │                       │      │
│  │               │ │ • Risk scoring  │  │                       │      │
│  └───────────────┘ └──────────────────┘  └───────────────────────┘      │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │              Additional Services                                    │   │
│  │                                                                     │   │
│  │  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │   │
│  │  │ Activity Service │  │  Health Service │  │ AI Post-Mortem  │  │   │
│  │  │                  │  │                 │  │   Generator     │  │   │
│  │  │ • History        │  │ • 14 services   │  │  🤖 Claude API  │  │   │
│  │  │ • Rollback mgmt  │  │ • 6 tiers       │  │ • Timeline      │  │   │
│  │  │ • 6 runbooks     │  │ • Metrics       │  │ • Root cause    │  │   │
│  │  └──────────────────┘  └─────────────────┘  └─────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
        ┌────────────────────┐    ┌────────────────────┐
        │  Mock Infrastructure│    │  Future: Real Infra│
        │                    │    │                    │
        │  • Alerts JSON     │    │  • SSH connections │
        │  • Services JSON   │    │  • Cloud APIs      │
        │  • Runbooks JSON   │    │  • Monitoring APIs │
        │  • Activities JSON │    │  • Prometheus, etc │
        └────────────────────┘    └────────────────────┘
```

---

## 🔄 Complete Workflow Diagram

```
                            ┌─────────────────────────┐
                            │    1. Alert Fires       │
                            │   (CPU spike, etc.)     │
                            └───────────┬─────────────┘
                                        │
                                        ▼
                            ┌─────────────────────────┐
                            │   2. Alert Agent        │
                            │   Detects & Routes      │
                            └───────────┬─────────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────────┐
                    │   3. Config Agent (🤖 AI-Powered)    │
                    │                                       │
                    │   • Analyzes alert context           │
                    │   • Reviews topology                 │
                    │   • Generates suggestion             │
                    │   • Confidence: 87%                  │
                    │   • Risk: Low/Medium/High            │
                    │   • Impact assessment                │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
        ┌──────────────────────────────────────────────────────┐
        │   4. WebSocket Broadcast: "Awaiting Approval"        │
        │      Real-time UI update                             │
        └───────────────┬──────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────────┐
        │   5. Human-in-the-Loop Decision           │
        │                                           │
        │   Operator sees:                          │
        │   ✓ AI Recommendation                     │
        │   ✓ Confidence Score                      │
        │   ✓ Risk Level                            │
        │   ✓ Estimated Impact                      │
        │   ✓ Rollback Plan                         │
        │                                           │
        │   [Approve] 👍  or  [Reject] 👎          │
        └─────┬─────────────────────────────┬───────┘
              │                             │
    ┌─────────▼──────┐              ┌──────▼────────┐
    │   APPROVED     │              │   REJECTED    │
    └─────┬──────────┘              └───────────────┘
          │                                 │
          ▼                                 ▼
┌──────────────────────┐            Workflow ends
│  6. Action Agent     │            with reason
│     Execution        │
│                      │
│  • Step 1: Backup   │
│  • Step 2: Execute  │
│  • Step 3: Verify   │
│                      │
│  Live progress ▶▶▶  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│   7. Completed + 5-Minute Rollback       │
│                                          │
│   Activity logged in history             │
│   Rollback timer: ⏱️ 4:58... 4:57...    │
│                                          │
│   [Rollback] button available            │
└────────────┬─────────────────────────────┘
             │
             ├──── Within 5 min ────┐
             │                      │
             │                      ▼
             │            ┌─────────────────────┐
             │            │  8. Rollback Exec   │
             │            │     (Optional)      │
             │            │                     │
             │            │  • Restore backup   │
             │            │  • Verify restored  │
             │            │  • Status: Rolled   │
             │            │    Back             │
             │            └─────────────────────┘
             │
             └──── After 5 min ────▶ Permanent (No rollback)
```

---

## 🤖 AI Integration Points Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI INTEGRATION POINTS                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ✅ IMPLEMENTED - Alert Remediation                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    Alert Data         Config Agent (AI)        Human Decision       │
│    ┌────────┐        ┌──────────────┐        ┌──────────────┐     │
│    │CPU:95% │───────▶│ Analyze      │───────▶│ [Approve]    │     │
│    │Mem:72% │        │ Suggest Fix  │        │ [Reject]     │     │
│    │Load:8.3│        │ Score: 87%   │        └──────────────┘     │
│    └────────┘        │ Risk: Low    │                              │
│                      └──────────────┘                              │
│                                                                      │
│    Input: Alert metrics, topology, history                          │
│    Output: Remediation suggestion, confidence, risk                 │
│    Model: Rule-based + AI hybrid                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ✅ IMPLEMENTED - Post-Mortem Generation                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    Completed         AI Post-Mortem            Human Review         │
│    Activity          Generator                                      │
│    ┌────────┐       ┌──────────────┐         ┌──────────────┐     │
│    │Alert   │──────▶│ Claude API   │────────▶│ Read Report  │     │
│    │Actions │       │              │         │ Act on Items │     │
│    │Results │       │ Generates:   │         └──────────────┘     │
│    │Timeline│       │ • Summary    │                              │
│    └────────┘       │ • Timeline   │                              │
│                     │ • Root Cause │                              │
│                     │ • Impact     │                              │
│                     │ • Lessons    │                              │
│                     └──────────────┘                              │
│                                                                      │
│    Input: Activity data (alert, actions, results, metrics)          │
│    Output: Comprehensive incident report                            │
│    Model: Claude 3.5 Sonnet (optional, has mock fallback)           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  🔮 FUTURE - Log Analysis                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    Log Stream       AI Analyzer              Proactive Alerts       │
│    ┌────────┐     ┌──────────────┐         ┌──────────────┐       │
│    │App logs│────▶│ Pattern      │────────▶│ Predict      │       │
│    │Sys logs│     │ Recognition  │         │ Issues       │       │
│    │Metrics │     │ Anomaly Det. │         │ Early        │       │
│    └────────┘     │ Clustering   │         └──────────────┘       │
│                   └──────────────┘                                 │
│                                                                      │
│    Model: Vector embeddings + semantic search                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  🔮 FUTURE - Runbook Generation                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    Historical        AI Generator            Human Validation       │
│    Data                                                             │
│    ┌────────┐      ┌──────────────┐        ┌──────────────┐       │
│    │Past    │─────▶│ Learn from   │───────▶│ Review       │       │
│    │Fixes   │      │ Success      │        │ Test         │       │
│    │Feedback│      │ Generate     │        │ Approve      │       │
│    └────────┘      │ Runbooks     │        └──────────────┘       │
│                    └──────────────┘                                │
│                                                                      │
│    Model: Fine-tuned LLM on operational data                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AI Integration Points

### 🤖 Current Implementation

#### 1. Alert Remediation (AI + Human-in-the-Loop)

```
┌───────────┐
│   Alert   │
│  Detected │
└─────┬─────┘
      │
      ▼
┌─────────────────────────────────────┐
│      Config Agent (AI-Powered)      │
│                                     │
│  • Analyzes alert context          │
│  • Reviews infrastructure topology  │
│  • Suggests remediation action     │
│  • Calculates confidence score     │
│  • Assesses risk level             │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│    Human-in-the-Loop Approval       │
│                                     │
│  Operator reviews:                  │
│  ✓ AI suggestion                    │
│  ✓ Confidence: 87%                  │
│  ✓ Risk: Low                        │
│  ✓ Estimated impact                 │
│                                     │
│  [Approve] or [Reject]              │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│       Action Agent (Execution)      │
│                                     │
│  • Executes approved action         │
│  • Live progress tracking           │
│  • Creates rollback snapshot        │
└─────────────────────────────────────┘
```

**AI Role**: Intelligent suggestion generation with confidence scoring
**Human Role**: Final approval/rejection decision
**Status**: ✅ Implemented with rule-based + AI hybrid

---

#### 2. Post-Mortem Generation (AI-Powered)

```
┌─────────────────────────────────────┐
│    Completed Activity               │
│                                     │
│  • Alert data                       │
│  • Actions taken                    │
│  • Execution results                │
│  • Timestamps                       │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│   AI Post-Mortem Generator          │
│   (Claude API - Optional)           │
│                                     │
│  Generates:                         │
│  • Executive summary                │
│  • Timeline of events               │
│  • Root cause analysis              │
│  • Impact assessment                │
│  • Lessons learned                  │
│  • Preventive measures              │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│    Human Review                     │
│                                     │
│  • Read comprehensive report        │
│  • Understand what happened         │
│  • Plan improvements                │
└─────────────────────────────────────┘
```

**AI Role**: Automated incident report generation
**Human Role**: Review and act on recommendations
**Status**: ✅ Implemented (works without API key using mock fallback)

---

### 🔮 Future AI Integrations

#### 3. Log Analyzer (AI-Powered) - Future Enhancement

```
┌─────────────────────────────────────┐
│     Log Stream Ingestion            │
│                                     │
│  • Application logs                 │
│  • System logs                      │
│  • Error traces                     │
│  • Metrics data                     │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│    AI Log Analyzer (PLANNED)        │
│                                     │
│  • Pattern recognition              │
│  • Anomaly detection                │
│  • Error clustering                 │
│  • Trend analysis                   │
│  • Predictive alerts                │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│   Proactive Alert Generation        │
│                                     │
│  • Predict issues before they occur │
│  • Suggest preventive actions       │
│  • Link to similar past incidents   │
└─────────────────────────────────────┘
```

**AI Role**: Proactive issue detection from log patterns
**Human Role**: Act on predictive insights
**Status**: 🔮 Planned for future release

---

#### 4. Intelligent Runbook Generation (AI-Powered) - Future Enhancement

```
┌─────────────────────────────────────┐
│   Historical Activity Data          │
│                                     │
│  • Past incidents                   │
│  • Successful remediations          │
│  • Operator feedback                │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  AI Runbook Generator (PLANNED)     │
│                                     │
│  • Learn from successful fixes      │
│  • Generate new runbooks            │
│  • Optimize existing procedures     │
│  • Adapt to infrastructure changes  │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│   Human Review & Approval           │
│                                     │
│  • Validate generated runbooks      │
│  • Test in staging                  │
│  • Approve for production use       │
└─────────────────────────────────────┘
```

**AI Role**: Learn and create new operational procedures
**Human Role**: Validate and approve new runbooks
**Status**: 🔮 Planned for future release

---

#### 5. Predictive Capacity Planning (AI-Powered) - Future Enhancement

```
┌─────────────────────────────────────┐
│    Infrastructure Metrics           │
│                                     │
│  • CPU/Memory trends                │
│  • Disk usage patterns              │
│  • Network traffic growth           │
│  • Request rate changes             │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  AI Capacity Predictor (PLANNED)    │
│                                     │
│  • Time-series forecasting          │
│  • Growth trend analysis            │
│  • Resource exhaustion prediction   │
│  • Scaling recommendations          │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│   Proactive Scaling Suggestions     │
│                                     │
│  • "DB will hit 90% disk in 7 days" │
│  • "Scale web tier for Black Friday"│
│  • "Reduce cache size by 30%"       │
└─────────────────────────────────────┘
```

**AI Role**: Predict resource needs before incidents occur
**Human Role**: Plan and execute capacity changes
**Status**: 🔮 Planned for future release

---

## Current State Management Flow

```
┌──────────────┐
│  MONITORING  │  Initial state
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ALERT_DETECTED│  Alert fires
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│AWAITING_APPROVAL │  🤖 AI suggests, waiting for human
└──────┬───────────┘
       │
       ├─[Approve]──────────────┐
       │                        ▼
       │                  ┌──────────┐
       │                  │ APPROVED │
       │                  └────┬─────┘
       │                       │
       │                       ▼
       │                  ┌───────────┐
       │                  │ EXECUTING │  Live tracking
       │                  └────┬──────┘
       │                       │
       │                       ▼
       │                  ┌───────────┐
       │                  │ COMPLETED │
       │                  └────┬──────┘
       │                       │
       │                       ├─[Within 5 min]──▶ ROLLBACK
       │                       │
       │                       └─[After 5 min]───▶ Permanent
       │
       └─[Reject]──────────────▶ REJECTED
```

---

## Technology Stack

### Current
- **Frontend**: React 18, Vite, Tailwind CSS
- **Backend**: FastAPI, Python 3.10+
- **AI Model**: Claude 3.5 Sonnet (optional, has mock fallback)
- **Communication**: WebSocket (real-time) + REST API
- **State**: Event-Sourcing pattern

### Future AI Integrations
- **Log Analysis**: Vector embeddings + semantic search
- **Predictive Models**: Time-series forecasting (Prophet, LSTM)
- **Runbook Generation**: Fine-tuned LLM on operational data
- **Anomaly Detection**: Unsupervised learning models

---

## Key Design Principles

1. **AI Augments, Human Decides**
   - AI provides suggestions and insights
   - Humans make final decisions
   - Complete audit trail of all actions

2. **Safety First**
   - Time-bound rollback windows
   - Risk assessment for every action
   - Operator approval required

3. **Production-Ready Architecture**
   - Modular agent system
   - Event-sourced state management
   - Scalable to real infrastructure

4. **Graceful Degradation**
   - Works without AI API keys (mock data)
   - Rule-based fallbacks
   - No single point of failure

---

🚀 **InfraAgent** - Your AI-Powered DevOps Copilot with Human Control
