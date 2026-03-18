import { StatCard } from "@/components/stat-card";

const stats = [
  { label: "Active jobs", value: "12,481", accent: "text-teal-700" },
  { label: "Open scrape runs", value: "4", accent: "text-sky-700" },
  { label: "Pending AI docs", value: "23", accent: "text-amber-700" },
  { label: "Applications this week", value: "18", accent: "text-emerald-700" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <section className="rounded-[28px] bg-slate-950 px-6 py-8 text-white">
        <div className="max-w-3xl">
          <div className="text-xs uppercase tracking-[0.35em] text-teal-300">Control Center</div>
          <h1 className="mt-4 text-4xl font-semibold leading-tight">
            Run the full job pipeline from scrape to tailored application.
          </h1>
          <p className="mt-4 text-base leading-7 text-slate-300">
            The platform is organized as independent services so scraping, search, AI generation,
            and application workflows scale without turning into a monolith.
          </p>
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </section>
    </div>
  );
}

