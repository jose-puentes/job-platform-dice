import { apiFetch } from "@/lib/api";
import { createScrapeRun } from "./actions";

type ScrapeRun = {
  id: string;
  source: string;
  query: string | null;
  location: string | null;
  status: string;
  total_tasks: number;
  completed_tasks: number;
  total_found: number;
  total_inserted: number;
  total_updated: number;
  total_duplicates: number;
  total_failed: number;
};

type ScrapeRunListResponse = {
  items: ScrapeRun[];
};

export default async function ScrapeRunsPage() {
  let data: ScrapeRunListResponse | null = null;
  let error = false;

  try {
    data = await apiFetch<ScrapeRunListResponse>("/scrape-runs");
  } catch {
    error = true;
  }

  return (
    <div className="space-y-4">
      <div className="text-sm uppercase tracking-[0.3em] text-slate-500">Operations</div>
      <h1 className="text-3xl font-semibold text-slate-900">Scrape Runs</h1>
      <form
        action={createScrapeRun}
        className="grid gap-3 rounded-[24px] border border-slate-200 bg-white p-6 md:grid-cols-4"
      >
        <input
          name="source"
          placeholder="Source"
          defaultValue="dice"
          className="rounded-2xl border border-slate-200 px-4 py-3"
        />
        <input
          name="query"
          placeholder="python developer, data engineer"
          className="rounded-2xl border border-slate-200 px-4 py-3"
        />
        <input
          name="location"
          placeholder="Location"
          defaultValue="Remote"
          className="rounded-2xl border border-slate-200 px-4 py-3"
        />
        <div className="flex gap-3">
          <input
            name="max_pages"
            type="number"
            min="1"
            max="25"
            defaultValue="1"
            className="w-24 rounded-2xl border border-slate-200 px-4 py-3"
          />
          <button className="flex-1 rounded-2xl bg-slate-950 px-4 py-3 font-medium text-white">
            Start Run
          </button>
        </div>
      </form>
      {error && (
        <div className="rounded-[24px] border border-amber-200 bg-amber-50 p-6 text-amber-800">
          Unable to load scrape runs from the gateway right now.
        </div>
      )}
      {!error && data?.items.length === 0 && (
        <div className="rounded-[24px] border border-slate-200 bg-white p-6 text-slate-600">
          No scrape runs yet. Create one through the API gateway to start the ingestion pipeline.
        </div>
      )}
      <div className="space-y-4">
        {data?.items.map((run) => (
          <article key={run.id} className="rounded-[24px] border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">{run.source}</h2>
                <p className="mt-1 text-sm text-slate-600">
                  {run.query ?? "No query"} - {run.location ?? "No location"}
                </p>
              </div>
              <div className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">
                {run.status}
              </div>
            </div>
            <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-3 xl:grid-cols-6">
              <div className="rounded-2xl bg-slate-50 p-3">
                Tasks: {run.completed_tasks}/{run.total_tasks}
              </div>
              <div className="rounded-2xl bg-slate-50 p-3">Found: {run.total_found}</div>
              <div className="rounded-2xl bg-slate-50 p-3">Inserted: {run.total_inserted}</div>
              <div className="rounded-2xl bg-slate-50 p-3">Updated: {run.total_updated}</div>
              <div className="rounded-2xl bg-slate-50 p-3">
                Duplicates: {run.total_duplicates}
              </div>
              <div className="rounded-2xl bg-slate-50 p-3">Failed: {run.total_failed}</div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
