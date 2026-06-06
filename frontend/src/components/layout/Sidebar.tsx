import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  History,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/history', label: 'Project History', icon: History },
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r bg-card flex flex-col h-screen">
      <div className="flex items-center gap-2 px-6 py-5 border-b">
        <Sparkles className="h-6 w-6 text-primary" />
        <span className="font-semibold text-lg">AI Dev Team</span>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
