// DevDocsAI — TypeScript Types: Repository
export type RepositoryStatus =
  | 'pending'
  | 'cloning'
  | 'parsing'
  | 'embedding'
  | 'graph'
  | 'summarizing'
  | 'ready'
  | 'failed';

export interface RepositoryMetadata {
  summary?: string;
  framework?: string;
  architecture_type?: string;
  total_files: number;
  total_functions: number;
  total_classes: number;
  total_lines: number;
  languages_detected?: string;
}

export interface Repository {
  id: string;
  repo_url: string;
  repo_name?: string;
  owner?: string;
  status: RepositoryStatus;
  progress: number;
  current_stage?: string;
  primary_language?: string;
  error_message?: string;
  created_at: string;
  processed_at?: string;
  metadata_?: RepositoryMetadata;
}

export interface RepositoryStatusResponse {
  repo_id: string;
  status: RepositoryStatus;
  progress: number;
  current_stage?: string;
  error_message?: string;
}

export interface AnalyzeResponse {
  repo_id: string;
  status: string;
  message: string;
}

export interface DependencyGraph {
  repo_id: string;
  mermaid: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  file?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation?: string;
}

export interface ArchitectureSummary {
  repo_id: string;
  summary: string;
  components: ArchitectureComponent[];
  framework?: string;
  architecture_type?: string;
}

export interface ArchitectureComponent {
  name: string;
  type: string;
  description?: string;
  dependencies: string[];
}
