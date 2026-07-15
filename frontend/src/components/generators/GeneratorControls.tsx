// DevDocsAI — Reusable Code Editor textarea
// A styled textarea mimicking a code editor (no Monaco dep needed for prototype)
interface CodeEditorProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  language?: string;
  rows?: number;
  readOnly?: boolean;
}

export function CodeEditor({
  value,
  onChange,
  placeholder = 'Paste your code here…',
  rows = 22,
  readOnly = false,
}: CodeEditorProps) {
  return (
    <div className="relative rounded-2xl border border-white/[0.08] overflow-hidden bg-[#0a0c14]">
      {/* Line numbers gutter */}
      <div className="absolute left-0 top-0 bottom-0 w-10 bg-white/[0.02] border-r border-white/[0.05] flex flex-col items-end pt-3 pr-2 select-none pointer-events-none overflow-hidden">
        {Array.from({ length: Math.max(rows, value.split('\n').length) }, (_, i) => (
          <span key={i} className="text-[10px] font-mono text-text-muted/40 leading-[1.65rem]">
            {i + 1}
          </span>
        ))}
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        readOnly={readOnly}
        rows={rows}
        spellCheck={false}
        className="w-full pl-12 pr-4 py-3 bg-transparent text-sm font-mono text-text-secondary
                   leading-[1.65rem] resize-none outline-none placeholder:text-text-muted/30
                   scrollbar-hide"
      />
    </div>
  );
}

// Select dropdown matching the design system
interface SelectProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}

export function GenSelect({ label, value, onChange, options }: SelectProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium text-text-muted uppercase tracking-wider">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="glass rounded-xl px-3 py-2.5 text-sm text-text-primary border border-white/[0.08]
                   bg-surface outline-none focus:border-brand-primary/50 transition-colors cursor-pointer"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value} className="bg-surface">
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
