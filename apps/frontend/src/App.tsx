import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { EvaluationsPage } from './pages/EvaluationsPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { TracesPage } from './pages/TracesPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="datasets" element={<DatasetsPage />} />
            <Route path="playground" element={<PlaygroundPage />} />
            <Route path="evaluations" element={<EvaluationsPage />} />
            <Route path="experiments" element={<ExperimentsPage />} />
            <Route path="traces" element={<TracesPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
