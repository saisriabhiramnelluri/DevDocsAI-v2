// DevDocsAI — Search API Service
import apiClient from './api';

export interface SearchResult {
  chunk_id: string;
  content: string;
  file: string;
  type: string;
  name?: string;
  score: number;
  line_start?: number;
  line_end?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
}

export const searchService = {
  async query(
    repoId: string,
    query: string,
    topK = 10,
    levelFilter?: string
  ): Promise<SearchResponse> {
    const { data } = await apiClient.post<SearchResponse>('/search/query', {
      repo_id: repoId,
      query,
      top_k: topK,
      level_filter: levelFilter,
    });
    return data;
  },
};
