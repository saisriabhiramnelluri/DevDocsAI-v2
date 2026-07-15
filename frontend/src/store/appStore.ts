// DevDocsAI — Global Store (Zustand)
import { create } from 'zustand';
import type { Repository } from '../types/repository';

interface AppStore {
  // Client Identity
  clientId: string;

  // Repository state
  repositories: Repository[];
  selectedRepoId: string | null;
  setRepositories: (repos: Repository[]) => void;
  addRepository: (repo: Repository) => void;
  updateRepository: (id: string, updates: Partial<Repository>) => void;
  removeRepository: (id: string) => void;
  setSelectedRepo: (id: string | null) => void;

  // UI state
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

const getClientId = () => {
  let id = localStorage.getItem('devdocs_client_id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('devdocs_client_id', id);
  }
  return id;
};

export const useAppStore = create<AppStore>((set) => ({
  clientId: getClientId(),
  repositories: [],
  selectedRepoId: null,
  sidebarOpen: true,

  setRepositories: (repos) => set({ repositories: repos }),

  addRepository: (repo) =>
    set((state) => ({
      repositories: [repo, ...state.repositories.filter((r) => r.id !== repo.id)],
    })),

  updateRepository: (id, updates) =>
    set((state) => ({
      repositories: state.repositories.map((r) =>
        r.id === id ? { ...r, ...updates } : r
      ),
    })),

  removeRepository: (id) =>
    set((state) => ({
      repositories: state.repositories.filter((r) => r.id !== id),
    })),

  setSelectedRepo: (id) => set({ selectedRepoId: id }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
