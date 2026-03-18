import { apiFetch } from "@/lib/api";

type ApplicationItem = {
  id: string;
  job_id: string;
  application_status: string;
  apply_strategy: string;
  external_reference: string | null;
};

type ApplicationsResponse = {
  items: ApplicationItem[];
};

export default async function ApplicationsPage() {
  let data: ApplicationsResponse | null = null;

  try {
    data = await apiFetch<ApplicationsResponse>("/applications");
  } catch {
    data = { items: [] };
  }

  return (
    <div className="space-y-4">
      <div className="text-sm uppercase tracking-[0.3em] text-slate-500">Apply History</div>
      <h1 className="text-3xl font-semibold text-slate-900">Applications</h1>
      <div className="space-y-4">
        {data.items.length === 0 && (
          <div className="rounded-[24px] border border-slate-200 bg-white p-6 text-slate-600">
            No applications recorded yet.
          </div>
        )}
        {data.items.map((application) => (
          <article key={application.id} className="rounded-[24px] border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{application.apply_strategy}</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Job {application.job_id} · {application.external_reference ?? "No external reference"}
                </p>
              </div>
              <div className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
                {application.application_status}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
