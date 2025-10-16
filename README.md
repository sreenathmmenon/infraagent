# InfraAgent - DevOps Copilot with Human-in-the-Loop

InfraAgent is an intelligent DevOps copilot that automates infrastructure issue resolution while keeping humans in control. It detects alerts, suggests remediation actions, waits for operator approval, executes fixes, and provides time-bound rollback capabilities.

**Key Theme**: Human-in-the-Loop System with State Management and Rollback

---

## 🎯 Core Features

### 1. **Human-in-the-Loop Alert Management**
- Real-time infrastructure monitoring
- AI-powered remediation suggestions with risk assessment
- Operator approval workflow before any changes
- Confidence scores and impact analysis

### 2. **Automated Remediation with State Management**
- Event-sourced workflow: \`MONITORING → ALERT_DETECTED → AWAITING_APPROVAL → EXECUTING → COMPLETED\`
- Live execution progress tracking
- Detailed step-by-step execution visualization

### 3. **Time-Bound Rollback System**
- 5-minute rollback windows after each remediation
- One-click undo with countdown timer
- Step-by-step rollback visualization
- Automatic state restoration

### 4. **Runbooks Library**
- 6 production-grade runbooks:
  - CPU Spike Mitigation
  - RabbitMQ Queue Purge
  - Emergency Disk Space Recovery
  - Blue-Green Deployment
  - Database Performance Tuning
  - Security Patch Deployment
- Detailed steps, prerequisites, and risk assessments
- Success rates and execution counts

### 5. **Infrastructure Dashboard**
- Real-time health monitoring (Healthy/Degraded/Critical)
- Service breakdown by tier (Web, DB, Cache, Kubernetes, etc.)
- 14+ monitored services across 6 tiers

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- Git

### Local Development

\`\`\`bash
# Clone the repository
git clone <repository-url>
cd infraagent

# Backend setup
cd backend
pip install -r requirements.txt
python3 main.py
# Backend runs on http://localhost:8000

# Frontend setup (in new terminal)
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173
\`\`\`

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**Note**: No API keys or environment variables needed - works out of the box with mock data!

---

## 💡 Design Decisions

### Why Mock Data?

This project uses **mock infrastructure data** instead of real VM connections for several reasons:

1. **Portability**: Anyone can run and test the system immediately without infrastructure setup
2. **Cost**: No need for cloud VMs or services during development/evaluation
3. **Safety**: Demonstrates the system without risk of affecting real infrastructure
4. **Focus**: Showcases the core workflow (Human-in-the-Loop, State Management, Rollback) without infrastructure complexity

**Production-Ready Architecture**: The multi-agent system is designed to connect to real infrastructure via:
- SSH for server commands
- Cloud provider APIs (AWS, GCP, Azure)
- Monitoring systems (Prometheus, Datadog, etc.)
- Simply swap mock data with real API calls in the agent layer

---

## 📊 Feature Implementation

### Core Requirements: Human-in-the-Loop, State Management, Rollback

| Criterion | Implementation | Evidence |
|-----------|---------------|----------|
| **Human-in-the-Loop** | ✅ Every action requires operator approval | Alert approval workflow, approve/reject buttons |
| **State Management** | ✅ Event-sourced workflow with 8 states | State machine: MONITORING → ALERT_DETECTED → AWAITING_APPROVAL → APPROVED → EXECUTING → COMPLETED |
| **Rollback Capability** | ✅ Time-bound 5-minute rollback windows | Countdown timer, one-click undo, step-by-step rollback |
| **Real-time Updates** | ✅ WebSocket communication | Live progress tracking, instant UI updates |
| **Production Quality** | ✅ 12+ alert types, 6 runbooks, 14 services | Infrastructure dashboard, comprehensive monitoring |
| **User Experience** | ✅ Intuitive UI, toast notifications, animations | Smooth transitions, visual feedback, responsive design |
| **Scalability** | ✅ Modular architecture, multi-agent system | AlertAgent, ConfigAgent, ActionAgent, TopologyAgent |

---

## 🛠️ Technology Stack

- **Frontend**: React 18, Vite, Tailwind CSS
- **Backend**: FastAPI, Python 3.10+, Uvicorn
- **Communication**: WebSocket (real-time), REST API
- **State**: Event-Sourcing pattern
- **Deployment**: Vercel (frontend), Railway/Render (backend)

---

🚀 **InfraAgent** - Your DevOps Copilot with Human Control
