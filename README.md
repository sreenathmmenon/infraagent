# InfraAgent - DevOps Copilot with Human-in-the-Loop

**Hackathon Project**: Human-in-the-Loop System with State Management and Rollback

InfraAgent is an intelligent DevOps copilot that automates infrastructure issue resolution while keeping humans in control. It detects alerts, suggests remediation actions, waits for operator approval, executes fixes, and provides time-bound rollback capabilities.

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

---

## 📦 Deployment

### Frontend (Vercel)

1. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Select your GitHub repository
   - Framework: **Vite**
   - Root Directory: \`frontend\`
   - Build Command: \`npm run build\`
   - Output Directory: \`dist\`
   - Add Environment Variable:
     - \`VITE_API_URL\`: Your backend URL (from Railway/Render)

### Backend (Railway / Render)

#### Option 1: Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Root Directory: \`backend\`
5. Deploy - Railway auto-detects the Procfile

#### Option 2: Render

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Settings:
   - **Name**: infraagent-backend
   - **Root Directory**: \`backend\`
   - **Build Command**: \`pip install -r requirements.txt\`
   - **Start Command**: \`uvicorn main:app --host 0.0.0.0 --port \$PORT\`
   - **Instance Type**: Free

---

## 🔑 Environment Variables

### Backend
- \`PORT\`: Server port (default: 8000)
- No AI API keys needed - uses mock data

### Frontend
- \`VITE_API_URL\`: Backend API URL (e.g., https://your-backend.railway.app)

---

## 📊 Judge Evaluation Mapping

### Theme: Human-in-the-Loop System with State Management and Rollback

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
