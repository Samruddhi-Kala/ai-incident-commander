# AI Incident Commander — React Frontend Dashboard

A modern, production-inspired operations console for automated incident investigation and human-governed remediation.

## 🚀 Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Run local development server
npm run dev

# 3. Run frontend unit tests
npm run test

# 4. Compile and build production bundle
npm run build
```

## 🛠️ Stack
- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS (dark operations theme)
- **Routing**: React Router v6
- **API Client**: Axios with centralized error handling
- **Testing**: Vitest + React Testing Library

## 🧭 Routes
- `/` — Command Center Overview
- `/incidents` — Incident Telemetry Console
- `/incidents/:incidentId` — Incident Detail
- `/incidents/:incidentId/investigation` — Investigation Deep Dive & Lifecycle Timeline
- `/remediations` — Remediation Governance Console
- `/remediations/:remediationId` — Remediation Proposal Detail & Execution Controller
