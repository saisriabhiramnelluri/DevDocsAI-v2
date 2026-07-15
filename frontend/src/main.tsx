import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import './index.css';
import App from './App.tsx';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster 
        position="bottom-right"
        toastOptions={{
          className: 'glass border border-white/[0.08]',
          style: {
            background: 'rgba(10, 15, 30, 0.9)',
            color: '#E2E8F0',
            backdropFilter: 'blur(12px)',
          },
        }}
      />
    </QueryClientProvider>
  </StrictMode>,
);
