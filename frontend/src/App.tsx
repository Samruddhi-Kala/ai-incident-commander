import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { IncidentListPage } from './pages/IncidentListPage';
import { IncidentDetailPage } from './pages/IncidentDetailPage';
import { InvestigationDetailPage } from './pages/InvestigationDetailPage';
import { RemediationListPage } from './pages/RemediationListPage';
import { RemediationDetailPage } from './pages/RemediationDetailPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<OverviewPage />} />
          <Route path="incidents" element={<IncidentListPage />} />
          <Route path="incidents/:incidentId" element={<IncidentDetailPage />} />
          <Route path="incidents/:incidentId/investigation" element={<InvestigationDetailPage />} />
          <Route path="remediations" element={<RemediationListPage />} />
          <Route path="remediations/:remediationId" element={<RemediationDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
