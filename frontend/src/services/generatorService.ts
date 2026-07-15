// DevDocsAI — Generator API Service
import apiClient from './api';

const API = apiClient;

// ── Comment Generator ─────────────────────────────────────────────────────────
export interface CommentResult {
  commented_code: string;
  language: string;
  style: string;
  comments_added: number;
  original_lines: number;
  output_lines: number;
}

export const generatorService = {
  async generateComments(
    code: string,
    language: string,
    style = 'auto',
  ): Promise<CommentResult> {
    const { data } = await API.post<CommentResult>('/generators/comment', {
      code,
      language,
      style,
    });
    return data;
  },

  // ── Test Generator ──────────────────────────────────────────────────────────
  async generateTests(
    code: string,
    language: string,
    framework = 'auto',
    coverage = 'high',
  ): Promise<{
    test_code: string;
    language: string;
    framework: string;
    coverage_level: string;
    estimated_test_count: number;
  }> {
    const { data } = await API.post('/generators/test', {
      code,
      language,
      framework,
      coverage,
    });
    return data;
  },

  // ── UML Generator ───────────────────────────────────────────────────────────
  async generateUMLFromCode(
    code: string,
    language: string,
    diagram_type = 'class',
  ): Promise<{ mermaid: string; source: string; diagram_type?: string }> {
    const { data } = await API.post('/generators/uml/from-code', {
      code,
      language,
      diagram_type,
    });
    return data;
  },

  async generateUMLFromRepo(
    repo_id: string,
    class_filter?: string[],
    max_classes = 20,
  ): Promise<{ mermaid: string; source: string; classes_count?: number }> {
    const { data } = await API.post('/generators/uml/from-repo', {
      repo_id,
      class_filter,
      max_classes,
    });
    return data;
  },

  // ── Code Converter ──────────────────────────────────────────────────────────
  async convertCode(
    code: string,
    source_language: string,
    target_language: string,
    preserve_comments = true,
  ): Promise<{
    converted_code: string;
    source_language: string;
    target_language: string;
    original_lines: number;
    output_lines: number;
    warnings: string[];
  }> {
    const { data } = await API.post('/generators/convert', {
      code,
      source_language,
      target_language,
      preserve_comments,
    });
    return data;
  },

  // ── Optimizer ───────────────────────────────────────────────────────────────
  async optimizeCode(
    code: string,
    language: string,
    focus = 'all',
  ): Promise<{
    original_code: string;
    optimized_code: string;
    improvements: { severity: string; line_range: string; category: string; description: string }[];
    summary: string;
    language: string;
    focus: string;
    stats: { total_improvements: number; high_severity: number; medium_severity: number; low_severity: number };
  }> {
    const { data } = await API.post('/generators/optimize', {
      code,
      language,
      focus,
    });
    return data;
  },

  // ── Tree Generator ──────────────────────────────────────────────────────────
  async treeFromRepo(
    repo_id: string,
    depth = 4,
    include_descriptions = true,
  ): Promise<{
    tree_text: string;
    markdown: string;
    file_count: number;
    directory_descriptions: Record<string, string>;
  }> {
    const { data } = await API.get(
      `/generators/tree/${repo_id}?depth=${depth}&include_descriptions=${include_descriptions}`,
    );
    return data;
  },

  async treeFromStructure(
    structure: string,
    project_name = 'Project',
  ): Promise<{ tree_text: string; markdown: string; file_count: number }> {
    const { data } = await API.post('/generators/tree', { structure, project_name });
    return data;
  },

  // ── Swagger / OpenAPI Generator ─────────────────────────────────────────────
  async generateSwaggerDocs(
    spec: string,
    language_samples = ['python', 'javascript', 'curl'],
  ): Promise<{
    documentation: string;
    title: string;
    version: string;
    endpoint_count: number;
    format: string;
    language_samples: string[];
  }> {
    const { data } = await API.post('/generators/swagger', {
      spec,
      output_format: 'markdown',
      language_samples,
    });
    return data;
  },

  // ── Release Notes Generator ──────────────────────────────────────────────────
  async generateReleaseNotes(
    commits: string[],
    version = 'Next Release',
    from_ref?: string,
    to_ref?: string,
  ): Promise<{
    release_notes: string;
    version: string;
    commit_count: number;
    categories: string[];
    from_ref?: string;
    to_ref?: string;
  }> {
    const { data } = await API.post('/generators/release-notes', {
      commits,
      version,
      from_ref,
      to_ref,
    });
    return data;
  },
};

