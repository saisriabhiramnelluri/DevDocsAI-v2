import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { KeyboardShortcutsOverlay } from './hooks/useKeyboardShortcuts';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { RepoPage } from './pages/RepoPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { GeneratorsHubPage } from './pages/generators/GeneratorsHubPage';
import { CommentGeneratorPage } from './pages/generators/CommentGeneratorPage';
import { TestGeneratorPage } from './pages/generators/TestGeneratorPage';
import { UMLGeneratorPage } from './pages/generators/UMLGeneratorPage';
import { ConvertGeneratorPage } from './pages/generators/ConvertGeneratorPage';
import { OptimizerPage } from './pages/generators/OptimizerPage';
import { SwaggerGeneratorPage } from './pages/generators/SwaggerGeneratorPage';
import { ReleaseNotesPage } from './pages/generators/ReleaseNotesPage';
import { TreeGeneratorPage } from './pages/generators/TreeGeneratorPage';
import { useAppStore } from './store/appStore';
import './App.css';

function AppLayout() {
  const { sidebarOpen } = useAppStore();
  const location = useLocation();
  const isHome = location.pathname === '/';
  const isGeneratorPage = location.pathname.startsWith('/generators');

  return (
    <div className="min-h-screen bg-background text-text-primary overflow-x-hidden selection:bg-brand-primary/30">
      {/* Background Decorations */}
      <div className="glow-orb glow-orb-1" />
      <div className="glow-orb glow-orb-2" />
      <div className="fixed inset-0 bg-dot-grid opacity-30 pointer-events-none" />

      <Navbar />
      {/* Sidebar only on inner non-generator pages */}
      {!isHome && !isGeneratorPage && <Sidebar />}

      {/* Global keyboard shortcuts overlay (? key) */}
      <KeyboardShortcutsOverlay />

      <main
        className={`relative z-10 transition-all duration-300 ${
          !isHome && !isGeneratorPage && sidebarOpen ? 'md:pl-[280px]' : ''
        }`}
      >
        <ErrorBoundary>
          <Routes>
            {/* Core pages */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/repo/:repoId" element={<RepoPage />} />

            {/* Generator pages */}
            <Route path="/generators" element={<GeneratorsHubPage />} />
            <Route path="/generators/comment" element={<CommentGeneratorPage />} />
            <Route path="/generators/test" element={<TestGeneratorPage />} />
            <Route path="/generators/uml" element={<UMLGeneratorPage />} />
            <Route path="/generators/convert" element={<ConvertGeneratorPage />} />
            <Route path="/generators/optimize" element={<OptimizerPage />} />
            <Route path="/generators/swagger" element={<SwaggerGeneratorPage />} />
            <Route path="/generators/release-notes" element={<ReleaseNotesPage />} />
            <Route path="/generators/tree" element={<TreeGeneratorPage />} />

            {/* 404 */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}

export default App;


