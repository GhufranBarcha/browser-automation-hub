import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { api } from '../api/client';
import { Loader2 } from 'lucide-react';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const loginMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/auth/login', { email, password });
      return data;
    },
    onSuccess: () => {
      navigate('/dashboard');
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    loginMutation.mutate();
  };

  return (
    <div className="flex min-h-screen flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
          Sign In
        </h2>
        <p className="mt-2 text-center text-sm text-gray-500">
          Enter your credentials to access the automation dashboard.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[480px]">
        <div className="bg-white px-4 py-8 shadow-sm sm:rounded-xl sm:px-10 border border-gray-200">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-gray-50 p-3 text-sm text-gray-900 border border-gray-200 text-center font-medium">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium leading-6 text-gray-900" htmlFor="email">Email</label>
                <div className="mt-2">
                  <input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input-field"
                    placeholder="admin@example.com"
                    disabled={loginMutation.isPending}
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium leading-6 text-gray-900" htmlFor="password">Password</label>
                <div className="mt-2">
                  <input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field"
                    placeholder="••••••••"
                    disabled={loginMutation.isPending}
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? (
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              ) : (
                'Sign In'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
