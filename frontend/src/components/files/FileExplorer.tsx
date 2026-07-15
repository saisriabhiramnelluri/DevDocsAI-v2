import { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, FileCode2, Folder, FolderOpen, Brackets, Box } from 'lucide-react';
import type { DependencyGraph } from '../../types/repository';

interface FileTreeNode {
  name: string;
  path: string;
  isDirectory: boolean;
  children: FileTreeNode[];
  functions?: string[];
  classes?: string[];
}

function buildTree(nodes: { id: string; name: string; type: string; file?: string; metadata?: Record<string, any> }[]): FileTreeNode {
  const root: FileTreeNode = { name: 'root', path: '', isDirectory: true, children: [] };

  for (const node of nodes) {
    const filePath = node.metadata?.file || node.file || node.name;
    if (!filePath || !filePath.includes('/')) continue;

    const parts = filePath.split('/').filter(Boolean);
    let current = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      const existing = current.children.find((c) => c.name === part);

      if (existing) {
        current = existing;
      } else {
        const newNode: FileTreeNode = {
          name: part,
          path: parts.slice(0, i + 1).join('/'),
          isDirectory: !isLast,
          children: [],
        };
        current.children.push(newNode);
        current = newNode;
      }
    }
  }

  return root;
}

function TreeNode({ node, depth = 0, graphNodes }: {
  node: FileTreeNode;
  depth?: number;
  graphNodes: any[];
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children.length > 0;

  // Find graph nodes that match this file
  const matchingGraphNodes = useMemo(() => {
    if (node.isDirectory) return [];
    return graphNodes.filter((n) => {
      const f = n.metadata?.file || n.file || n.name;
      return f && f.endsWith(node.path);
    });
  }, [node, graphNodes]);

  const functions = matchingGraphNodes.filter((n) => n.type === 'function');
  const classes = matchingGraphNodes.filter((n) => n.type === 'class');

  const Icon = node.isDirectory
    ? expanded ? FolderOpen : Folder
    : FileCode2;

  const iconColor = node.isDirectory
    ? 'text-brand-accent'
    : node.name.endsWith('.py') ? 'text-blue-400'
    : node.name.endsWith('.ts') || node.name.endsWith('.tsx') ? 'text-cyan-400'
    : node.name.endsWith('.js') ? 'text-yellow-400'
    : 'text-text-muted';

  return (
    <div>
      <button
        onClick={() => { if (hasChildren || !node.isDirectory) setExpanded((e) => !e); }}
        className={`flex items-center gap-1.5 w-full text-left px-2 py-1 rounded-lg hover:bg-surface transition-colors text-sm group ${depth === 0 ? 'font-semibold' : ''}`}
        style={{ paddingLeft: `${8 + depth * 16}px` }}
      >
        {node.isDirectory ? (
          <span className="text-text-muted w-3">
            {hasChildren ? (expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />) : null}
          </span>
        ) : (
          <span className="w-3" />
        )}
        <Icon size={14} className={iconColor} />
        <span className="truncate text-text-secondary group-hover:text-text-primary transition-colors font-mono">
          {node.name}
        </span>
        {!node.isDirectory && (functions.length > 0 || classes.length > 0) && (
          <span className="ml-auto text-[10px] text-text-muted opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
            {functions.length > 0 && <span className="text-brand-accent">{functions.length}fn</span>}
            {classes.length > 0 && <span className="text-brand-secondary">{classes.length}cls</span>}
          </span>
        )}
      </button>

      {/* Show functions / classes when file is expanded */}
      {!node.isDirectory && expanded && (functions.length > 0 || classes.length > 0) && (
        <div className="ml-1 border-l border-white/[0.06] my-1">
          {functions.map((fn: any) => (
            <div
              key={fn.id}
              className="flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono text-text-muted hover:text-brand-accent transition-colors cursor-default"
              style={{ paddingLeft: `${16 + (depth + 1) * 16}px` }}
            >
              <Brackets size={11} className="text-brand-accent flex-shrink-0" />
              <span className="truncate">{fn.name}</span>
            </div>
          ))}
          {classes.map((cls: any) => (
            <div
              key={cls.id}
              className="flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono text-text-muted hover:text-brand-secondary transition-colors cursor-default"
              style={{ paddingLeft: `${16 + (depth + 1) * 16}px` }}
            >
              <Box size={11} className="text-brand-secondary flex-shrink-0" />
              <span className="truncate">{cls.name}</span>
            </div>
          ))}
        </div>
      )}

      {/* Children */}
      {node.isDirectory && expanded && (
        <div>
          {node.children
            .sort((a, b) => {
              // directories first
              if (a.isDirectory && !b.isDirectory) return -1;
              if (!a.isDirectory && b.isDirectory) return 1;
              return a.name.localeCompare(b.name);
            })
            .map((child) => (
              <TreeNode key={child.path} node={child} depth={depth + 1} graphNodes={graphNodes} />
            ))}
        </div>
      )}
    </div>
  );
}

export function FileExplorer({ graph }: { graph: DependencyGraph }) {
  const [filter, setFilter] = useState('');

  const fileNodes = graph.nodes.filter((n: any) => {
    const f = n.metadata?.file || n.name;
    return f && (filter === '' || f.toLowerCase().includes(filter.toLowerCase()));
  });

  const tree = useMemo(() => buildTree(fileNodes), [fileNodes]);

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] md:h-[calc(100vh-140px)] w-full p-4 md:p-6 pb-12">
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-xs">
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter files…"
            className="w-full glass rounded-xl px-4 py-2 text-sm bg-transparent border border-white/[0.08] text-white placeholder-text-muted outline-none focus:border-brand-primary/50 font-mono"
          />
        </div>
        <div className="flex gap-4 text-xs text-text-muted">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-brand-accent inline-block" /> Functions
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-brand-secondary inline-block" /> Classes
          </span>
        </div>
      </div>

      <div className="flex-1 glass-strong rounded-2xl border-glow overflow-y-auto p-3">
        {tree.children.length === 0 ? (
          <div className="text-center text-text-muted py-12">
            <FileCode2 size={40} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No files match the filter</p>
          </div>
        ) : (
          tree.children
            .sort((a, b) => {
              if (a.isDirectory && !b.isDirectory) return -1;
              if (!a.isDirectory && b.isDirectory) return 1;
              return a.name.localeCompare(b.name);
            })
            .map((node) => (
              <TreeNode key={node.path} node={node} depth={0} graphNodes={graph.nodes} />
            ))
        )}
      </div>

      <p className="text-xs text-text-muted text-center mt-2 font-mono">
        {graph.nodes.length} nodes indexed · Hover a file to see function/class counts
      </p>
    </div>
  );
}
