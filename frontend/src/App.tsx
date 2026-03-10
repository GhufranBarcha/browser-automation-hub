import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { TaskDetailPage } from './pages/TaskDetailPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background text-foreground font-sans antialiased flex flex-col selection:bg-primary/20">
          {/* Main App Container */}
          <main className="flex-1 flex flex-col">
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
