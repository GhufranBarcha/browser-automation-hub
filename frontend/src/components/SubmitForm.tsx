import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { FileText, Loader2, X } from 'lucide-react';

export function SubmitForm() {
  const [prompt, setPrompt] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const submitMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append('prompt', prompt);
      if (file) {
        formData.append('file', file);
      }
      
      const { data } = await api.post('/tasks', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return data;
    },
    onSuccess: () => {
      setPrompt('');
      setFile(null);
      // Invalidate queries to refresh task list and queue
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['queueSummary'] });
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    submitMutation.mutate();
  };

  return (
    <div className="card-minimal p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
        Create Automation Task
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="block text-sm font-medium leading-6 text-gray-900">Instruction Prompt</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="input-field min-h-[120px] resize-y"
            placeholder="Type your multi-step instructions here..."
            required
            disabled={submitMutation.isPending}
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mt-4">
          <div className="flex-1 w-full relative">
            <input
              type="file"
              id="file-upload"
              accept=".pdf"
              className="hidden"
              onChange={handleFileChange}
              disabled={submitMutation.isPending}
            />
              <label
                htmlFor="file-upload"
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border border-dashed border-gray-300 bg-gray-50 cursor-pointer hover:bg-gray-100 hover:border-gray-400 transition-colors w-full sm:w-auto overflow-hidden ${file ? 'border-primary/50 bg-primary/5' : ''}`}
              >
                <FileText size={20} className={file ? "text-primary" : "text-gray-400"} />
                <span className={`text-sm truncate max-w-[200px] ${file ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
                  {file ? file.name : "Attach Supplemental PDF"}
                </span>
              </label>
            {file && (
              <button
                type="button"
                onClick={(e) => { e.preventDefault(); setFile(null); }}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-white/10 text-muted-foreground hover:text-white transition-colors"
                title="Remove file"
              >
                <X size={16} />
              </button>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary shrink-0 w-full sm:w-auto shadow-sm"
            disabled={!prompt.trim() || submitMutation.isPending}
          >
            {submitMutation.isPending ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Queuing...</>
            ) : (
              'Add to Queue'
            )}
          </button>
        </div>
        
        {submitMutation.isError && (
          <p className="text-gray-600 font-medium text-sm mt-2">
            Error: {(submitMutation.error as any).response?.data?.detail || submitMutation.error.message}
          </p>
        )}
      </form>
    </div>
  );
}
