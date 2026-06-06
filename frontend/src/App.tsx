import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import DashboardPage from '@/pages/DashboardPage';
import MonitorPage from '@/pages/MonitorPage';
import ResultsPage from '@/pages/ResultsPage';
import HistoryPage from '@/pages/HistoryPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/projects/:projectId/monitor" element={<MonitorPage />} />
        <Route path="/projects/:projectId" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
