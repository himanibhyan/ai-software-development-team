import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { ThemeToggle } from './ThemeToggle';

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b flex items-center justify-end px-6 bg-card">
          <ThemeToggle />
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
