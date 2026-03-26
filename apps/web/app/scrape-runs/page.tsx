import { apiFetch } from "@/lib/api";
import { createScrapeRun } from "./actions";
import { ScrapeRunsDashboard } from "./scrape-runs-dashboard";

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
      <p className="max-w-3xl text-sm text-slate-600">
        Each scrape run creates one task per query per results page. Example: 1 query with 5 pages
        creates 5 tasks. If you enter 2 comma-separated queries with 5 pages, the run creates 10
        tasks.
      </p>
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
          <label className="flex min-w-[168px] flex-col gap-1 rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-600">
            <span className="font-medium text-slate-900">Pages to Scan</span>
            <input
              name="max_pages"
              type="number"
              min="1"
              max="25"
              defaultValue="1"
              className="w-full bg-transparent text-base text-slate-900 outline-none"
            />
            <span className="text-xs text-slate-500">1 page = 1 task per query</span>
          </label>
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
      {!error && <ScrapeRunsDashboard initialRuns={data?.items ?? []} />}
    </div>
  );
}
