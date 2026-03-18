import Link from "next/link";
import { BriefcaseBusiness, Files, Gauge, Send, Settings2 } from "lucide-react";
import { ReactNode } from "react";

const navItems = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { href: "/documents", label: "Documents", icon: Files },
  { href: "/applications", label: "Applications", icon: Send },
  { href: "/settings", label: "Settings", icon: Settings2 },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto flex min-h-screen max-w-[1600px] gap-6 px-4 py-4 md:px-6">
      <aside className="hidden w-72 shrink-0 rounded-[28px] border border-white/60 bg-white/80 p-5 shadow-panel backdrop-blur md:block">
        <div className="mb-8">
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
            Job Bot
          </div>
          <h1 className="mt-3 text-2xl font-semibold text-slate-900">Operator Console</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Searchable jobs, async scrape runs, AI-generated docs, and tracked applications.
          </p>
        </div>
        <nav className="space-y-2">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 rounded-[28px] border border-white/60 bg-white/75 p-4 shadow-panel backdrop-blur md:p-6">
        {children}
      </main>
    </div>
  );
}

