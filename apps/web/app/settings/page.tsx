export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <div className="text-sm uppercase tracking-[0.3em] text-slate-500">Admin</div>
      <h1 className="text-3xl font-semibold text-slate-900">Settings</h1>
      <div className="rounded-[24px] border border-slate-200 bg-white p-6 text-slate-600">
        Adapter configuration, prompt templates, and service health can be surfaced here.
      </div>
    </div>
  );
}
