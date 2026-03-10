import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import type { TaskDetail } from '../api/types';
import { ArrowLeft, Clock, Server, CheckCircle2, XCircle, AlertCircle, FileText, Play } from 'lucide-react';

export function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();

  const { data: task, isLoading, isError } = useQuery<TaskDetail>({
    queryKey: ['task', taskId],
    queryFn: async () => {
      const { data } = await api.get(`/tasks/${taskId}`);
      return data;
    },
    refetchInterval: (query) => {
      // Stop polling if task is finished
      const data = query.state.data;
      if (data && ['completed', 'failed', 'cancelled', 'removed'].includes(data.status)) {
        return false;
      }
      return 3000;
    },
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (isError || !task) {
    return (
      <div className="max-w-4xl mx-auto p-8">
        <div className="card-minimal p-8 rounded-2xl text-center border-gray-200">
          <AlertCircle size={48} className="text-gray-900 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Task Not Found</h2>
          <p className="text-gray-500 mb-6">The task you're looking for doesn't exist or was removed.</p>
          <Link to="/dashboard" className="btn-primary">Back to Dashboard</Link>
        </div>
      </div>
    );
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'queued': return <Clock size={16} className="text-gray-400" />;
      case 'started': return <Server size={16} className="text-gray-500" />;
      case 'step': return <Play size={16} className="text-gray-400" />;
      case 'completed': return <CheckCircle2 size={16} className="text-gray-600" />;
      case 'failed': return <AlertCircle size={16} className="text-gray-700" />;
      case 'cancelled': return <XCircle size={16} className="text-gray-400" />;
      default: return <Server size={16} className="text-gray-300" />;
    }
  };


  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const durationStr = () => {
    if (!task.started_at) return null;
    let end = task.finished_at ? new Date(task.finished_at) : new Date();
    let start = new Date(task.started_at);
    let diffMs = end.getTime() - start.getTime();
    if (diffMs < 0) return '0s';
    
    let diffSecs = Math.floor(diffMs / 1000);
    let mins = Math.floor(diffSecs / 60);
    let secs = diffSecs % 60;
    
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-4 sm:p-6 lg:p-8 relative z-10">
      <Link to="/dashboard" className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 font-medium transition-colors mb-6 group">
        <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
        Back to Dashboard
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Task Details Side */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card-minimal p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center justify-between">
              Task Details
              <span className={`badge badge-${task.status}`}>{task.status}</span>
            </h2>
            
            <dl className="space-y-4 text-sm mt-4">
              <div>
                <dt className="text-gray-500 mb-1 font-medium">Task ID</dt>
                <dd className="font-mono text-gray-700 bg-gray-50 p-2 rounded-lg break-all border border-gray-100">{task.id}</dd>
              </div>
              
              <div>
                <dt className="text-gray-500 mb-1 font-medium">Created</dt>
                <dd className="text-gray-900 font-medium">{formatDate(task.created_at)}</dd>
              </div>

              {task.started_at && (
                <div>
                  <dt className="text-gray-500 mb-1 font-medium">Started</dt>
                  <dd className="text-gray-900 font-medium">{formatDate(task.started_at)}</dd>
                </div>
              )}

              {task.started_at && (
                <div>
                  <dt className="text-gray-500 mb-1 font-medium">Duration</dt>
                  <dd className="text-gray-900 font-mono font-medium">{durationStr()}</dd>
                </div>
              )}
              
              {task.pdf_filename && (
                <div>
                  <dt className="text-gray-500 mb-1 font-medium">Attached File</dt>
                  <dd className="text-gray-700 flex items-center gap-2 bg-gray-50 p-2 rounded-lg border border-gray-100">
                    <FileText size={16} className="text-primary" />
                    <span className="truncate">{task.pdf_filename}</span>
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* Prompt & Events Side */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card-minimal p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Instruction Prompt</h2>
            <div className="bg-gray-50 p-4 rounded-xl text-gray-700 whitespace-pre-wrap font-medium text-sm border border-gray-100 overflow-x-auto">
              {task.prompt_text}
            </div>
            
            {task.error_message && (
              <div className="mt-4 bg-gray-50 border border-gray-200 p-4 rounded-xl">
                <h3 className="text-gray-900 font-bold flex items-center gap-2 mb-2">
                  <AlertCircle size={18} /> Error Message
                </h3>
                <p className="text-gray-600 text-sm whitespace-pre-wrap font-mono">
                  {task.error_message}
                </p>
              </div>
            )}
          </div>

          <div className="card-minimal p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Event Timeline</h2>
            
            {task.events.length === 0 ? (
              <div className="text-muted-foreground text-center py-8">No events recorded yet.</div>
            ) : (
              <div className="relative border-l-2 border-gray-100 ml-3 space-y-6 pb-4">
                {task.events.map((event) => (
                  <div key={event.id} className="relative pl-6">
                    <div className="absolute -left-[14px] top-1 bg-white rounded-full p-1 border-2 border-gray-100">
                      {getEventIcon(event.event_type)}
                    </div>
                    <div className="mb-0.5 flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-gray-900 capitalize">{event.event_type}</span>
                      <span className="text-xs text-gray-500 font-medium">{formatDate(event.created_at)}</span>
                    </div>
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">{event.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
