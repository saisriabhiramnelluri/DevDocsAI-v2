// DevDocsAI — Repository API Service
import apiClient from './api';
import type {
  AnalyzeResponse,
  ArchitectureSummary,
  DependencyGraph,
  Repository,
  RepositoryStatusResponse,
} from '../types/repository';

export const repositoryService = {
  async analyze(repoUrl: string): Promise<AnalyzeResponse> {
    const { data } = await apiClient.post<AnalyzeResponse>('/repositories/analyze', {
      repo_url: repoUrl,
    });
    return data;
  },

  async getById(repoId: string): Promise<Repository> {
    const { data } = await apiClient.get<Repository>(`/repositories/${repoId}`);
    return data;
  },

  async getStatus(repoId: string): Promise<RepositoryStatusResponse> {
    const { data } = await apiClient.get<RepositoryStatusResponse>(
      `/repositories/${repoId}/status`
    );
    return data;
  },

  async list(): Promise<{ repositories: Repository[]; total: number }> {
    const { data } = await apiClient.get('/repositories/');
    return data;
  },

  async delete(repoId: string): Promise<void> {
    await apiClient.delete(`/repositories/${repoId}`);
  },

  async getArchitectureSummary(repoId: string): Promise<ArchitectureSummary> {
    const { data } = await apiClient.get<ArchitectureSummary>(
      `/architecture/${repoId}/summary`
    );
    return data;
  },

  async getDependencyGraph(repoId: string): Promise<DependencyGraph> {
    const { data } = await apiClient.get<DependencyGraph>(
      `/architecture/${repoId}/graph`
    );
    return data;
  },

  async getDependencies(repoId: string) {
    const { data } = await apiClient.get(`/architecture/${repoId}/dependencies`);
    return data;
  },

  async getReadme(repoId: string) {
    const { data } = await apiClient.get(`/docs/${repoId}/readme`);
    return data;
  },

  async getApiDocs(repoId: string) {
    const { data } = await apiClient.get(`/docs/${repoId}/api`);
    return data;
  },

  async getOnboarding(repoId: string) {
    const { data } = await apiClient.get(`/docs/${repoId}/onboarding`);
    return data;
  },
};
