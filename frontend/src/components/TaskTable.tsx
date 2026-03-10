import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Task } from '../api/types';
import { Play, XCircle, Trash2, Clock, AlertCircle, FileText } from 'lucide-react';

interface Props {
  tasks: Task[];
  title: string;
  emptyMessage: string;
}

export function TaskTable({ tasks, title, emptyMessage }: Props) {
  const queryClient = useQueryClient();

  const cancelMutation = useMutation({
    mutationFn: (id: string) => api.post(`/tasks/${id}/cancel`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const removeMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/tasks/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const retryMutation = useMutation({
    mutationFn: (id: string) => api.post(`/tasks/${id}/retry`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
  };

  if (tasks.length === 0) {
    return (
      <div className="card-minimal mb-6 overflow-hidden">
        <div className="bg-white px-6 py-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="p-12 text-center text-gray-500 flex flex-col items-center justify-center gap-3 bg-gray-50/50">
          <Clock size={32} className="opacity-20" />
          <p>{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card-minimal mb-6 overflow-hidden">
      <div className="bg-white px-6 py-4 border-b border-gray-100 flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          {title}
          <span className="badge bg-gray-100 text-gray-600 border-gray-200">{tasks.length}</span>
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-500 bg-gray-50/80 uppercase border-b border-gray-100">
            <tr>
              <th className="px-6 py-3 font-medium">Status & ID</th>
              <th className="px-6 py-3 font-medium">Prompt</th>
              <th className="px-6 py-3 font-medium">Created At</th>
              <th className="px-6 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {tasks.map((task) => (
              <tr key={task.id} className="hover:bg-gray-50/80 transition-colors group border-b border-gray-50 last:border-0">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-col gap-1">
                    <span className={`badge badge-${task.status} w-fit`}>
                      {task.status}
                    </span>
                    <Link to={`/tasks/${task.id}`} className="font-mono text-xs text-primary hover:underline" title={task.id}>
                      {task.id.split('-')[0]}...
                    </Link>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-col gap-1 max-w-md">
                    <span className="text-gray-900 truncate font-medium">{task.prompt_text}</span>
                    {task.pdf_filename && (
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <FileText size={12} />
                        {task.pdf_filename}
                      </span>
                    )}
                    {task.error_message && (
                      <span className="text-xs text-gray-700 flex items-start gap-1 mt-1 bg-gray-50 border border-gray-200 p-1.5 rounded-lg truncate">
                        <AlertCircle size={14} className="shrink-0 mt-0.5" />
                        {task.error_message}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                  {formatDate(task.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <div className="flex justify-end gap-2 transition-opacity">
                    {(task.status === 'queued' || task.status === 'running') && (
                      <button
                        onClick={() => cancelMutation.mutate(task.id)}
                        disabled={cancelMutation.isPending || task.cancel_requested}
                        className="btn-secondary px-3 py-1.5 gap-1.5"
                        title="Cancel Task"
                      >
                        <XCircle size={14} className={task.cancel_requested ? "animate-pulse text-gray-500" : ""} />
                        <span>{task.cancel_requested ? 'Cancelling...' : 'Cancel'}</span>
                      </button>
                    )}
                    {(task.status === 'queued' || task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled') && (
                      <button
                        onClick={() => removeMutation.mutate(task.id)}
                        disabled={removeMutation.isPending}
                        className="btn-destructive px-3 py-1.5 gap-1.5"
                        title="Delete Task"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                    {(task.status === 'failed' || task.status === 'cancelled') && (
                      <button
                        onClick={() => retryMutation.mutate(task.id)}
                        disabled={retryMutation.isPending}
                        className="btn-primary px-3 py-1.5 gap-1.5"
                        title="Retry Task"
                      >
                        <Play size={14} />
                        <span>Retry</span>
                      </button>
                    )}
                    <Link
                      to={`/tasks/${task.id}`}
                      className="btn-secondary px-3 py-1.5"
                    >
                      Details
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
