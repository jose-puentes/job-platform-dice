export function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-5">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-3 text-3xl font-semibold ${accent}`}>{value}</div>
    </div>
  );
}

