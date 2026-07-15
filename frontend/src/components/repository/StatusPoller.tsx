import { useEffect, useRef } from 'react';
import { useAppStore } from '../../store/appStore';
import { repositoryService } from '../../services/repositoryService';

export function useStatusPoller(repoId: string | undefined) {
  const { repositories, updateRepository } = useAppStore((state: any) => state);
  const pollingRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!repoId) return;

    const repo = repositories.find((r: any) => r.id === repoId);
    
    // Stop polling if we are ready or failed
    if (repo && (repo.status === 'ready' || repo.status === 'failed')) {
      if (pollingRef.current) clearInterval(pollingRef.current);
      return;
    }

    const poll = async () => {
      try {
        const status = await repositoryService.getStatus(repoId);
        updateRepository(repoId, status);
        
        if (status.status === 'ready' || status.status === 'failed') {
          // If it just became ready, we might want to fetch the full repo to get metadata
          if (status.status === 'ready') {
            const fullRepo = await repositoryService.getById(repoId);
            updateRepository(repoId, fullRepo);
          }
          if (pollingRef.current) clearInterval(pollingRef.current);
        }
      } catch (error) {
        console.error('Failed to poll status', error);
      }
    };

    // Initial poll
    poll();

    // Set up interval
    pollingRef.current = window.setInterval(poll, 3000);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [repoId, repositories, updateRepository]);
}
