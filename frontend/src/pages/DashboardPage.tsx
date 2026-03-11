import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { Task, QueueSummary } from '../api/types';
import { SubmitForm } from '../components/SubmitForm';
import { TaskTable } from '../components/TaskTable';
import { LogOut } from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Redirect to login if unauthenticated
  useEffect(() => {
    api.get('/auth/me').catch((err) => {
      if (err.response?.status === 401) {
        navigate('/login');
      }
    });
  }, [navigate]);

  const { data: summary } = useQuery<QueueSummary>({
    queryKey: ['queueSummary'],
    queryFn: async () => {
      const { data } = await api.get('/queue/summary');
      return data;
    },
    refetchInterval: 3000,
  });

  const { data: tasks = [] } = useQuery<Task[]>({
    queryKey: ['tasks'],
    queryFn: async () => {
      const { data } = await api.get('/tasks');
      return data;
    },
    refetchInterval: 3000,
  });

  const handleLogout = async () => {
    await api.post('/auth/logout');
    queryClient.clear();
    navigate('/login');
  };

  const queuedTasks = tasks.filter(t => t.status === 'queued');
  const runningTasks = tasks.filter(t => t.status === 'running');
  const completedTasks = tasks.filter(t => ['completed', 'failed', 'cancelled'].includes(t.status));

  return (
    <div className="max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8 relative z-10">
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 flex items-center gap-3">
            Automation Dashboard
          </h1>
          <p className="text-gray-500 mt-1 text-sm">Manage and monitor browser automation tasks</p>
        </div>
        
        <div className="flex items-center gap-6">
          {summary && (
            <div className="flex items-center gap-4 text-sm bg-white border border-gray-200 px-4 py-2 rounded-full shadow-sm">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-gray-300"></span>
                <span className="text-gray-600"><strong className="text-gray-900 font-semibold">{summary.queued}</strong> Queued</span>
              </div>
              <div className="w-px h-4 bg-gray-200"></div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-gray-500"></span>
                <span className="text-gray-600"><strong className="text-gray-900 font-semibold">{summary.active_slots}/{summary.max_slots}</strong> Slots Used</span>
              </div>
            </div>
          )}
          
          <button onClick={handleLogout} className="text-gray-400 hover:text-gray-600 transition-colors" title="Logout">
            <LogOut size={20} />
          </button>
        </div>
      </header>

      <SubmitForm />

      <div className="space-y-8">
        <TaskTable 
          tasks={runningTasks} 
          title="Active Runs" 
          emptyMessage="No tasks are currently running." 
        />
        <TaskTable 
          tasks={queuedTasks} 
          title="Queue" 
          emptyMessage="Queue is empty. Submit a new task above." 
        />
        <TaskTable 
          tasks={completedTasks.slice(0, 50)} 
          title="Recent History" 
          emptyMessage="No completed or failed tasks yet." 
        />
      </div>
    </div>
  );
}
