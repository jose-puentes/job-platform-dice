import Link from "next/link";

import { apiFetch } from "@/lib/api";
import { JobsList } from "@/components/jobs-list";

type JobItem = {
  id: string;
  title: string;
  company: string;
  source: string;
  location: string | null;
  work_mode: string;
  employment_type: string;
};

type JobsResponse = {
  items: JobItem[];
  total: number;
  page: number;
  page_size: number;
};

export default async function JobsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const q = typeof params.q === "string" ? params.q : "";
  const source = typeof params.source === "string" ? params.source : "";
  const company = typeof params.company === "string" ? params.company : "";
  const location = typeof params.location === "string" ? params.location : "";
  const workMode = typeof params.work_mode === "string" ? params.work_mode : "";
  const employmentType = typeof params.employment_type === "string" ? params.employment_type : "";
  const page = typeof params.page === "string" ? params.page : "1";
  let data: JobsResponse | null = null;
  let error = false;

  try {
    const query = new URLSearchParams();
    if (q) query.set("q", q);
    if (source) query.set("source", source);
    if (company) query.set("company", company);
    if (location) query.set("location", location);
    if (workMode) query.set("work_mode", workMode);
    if (employmentType) query.set("employment_type", employmentType);
    if (page) query.set("page", page);
    data = await apiFetch<JobsResponse>(`/jobs?${query.toString()}`);
  } catch {
    error = true;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="text-sm font-medium uppercase tracking-[0.3em] text-slate-500">
            Job Search
          </div>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">Normalized Job Catalog</h1>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
          Search, filter, paginate, and batch apply will connect here through `api-gateway`.
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[320px,1fr]">
        <aside className="rounded-[24px] border border-slate-200 bg-slate-50 p-5">
          <h2 className="text-lg font-semibold text-slate-900">Filters</h2>
          <form className="mt-4 space-y-3 text-sm text-slate-600" method="GET">
            <input
              name="q"
              defaultValue={q}
              placeholder="Keyword"
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            />
            <input
              name="source"
              defaultValue={source}
              placeholder="Source"
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            />
            <input
              name="company"
              defaultValue={company}
              placeholder="Company"
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            />
            <input
              name="location"
              defaultValue={location}
              placeholder="Location"
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            />
            <select
              name="work_mode"
              defaultValue={workMode}
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            >
              <option value="">Any work mode</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">Onsite</option>
            </select>
            <select
              name="employment_type"
              defaultValue={employmentType}
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            >
              <option value="">Any employment type</option>
              <option value="full_time">Full time</option>
              <option value="part_time">Part time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
              <option value="temporary">Temporary</option>
            </select>
            <button className="w-full rounded-2xl bg-slate-950 px-4 py-3 font-medium text-white">
              Apply Filters
            </button>
          </form>
        </aside>
        <div className="space-y-4">
          {error && (
            <div className="rounded-[24px] border border-amber-200 bg-amber-50 p-5 text-amber-800">
              Unable to load jobs from the gateway right now.
            </div>
          )}
          {!error && (
            <JobsList jobs={data?.items ?? []} empty={(data?.items.length ?? 0) === 0} />
          )}
          {!error && data && (
            <div className="flex items-center justify-between rounded-[24px] border border-slate-200 bg-white px-5 py-4 text-sm text-slate-600">
              <div>
                Page {data.page} · {data.total} total jobs
              </div>
              <div className="flex gap-3">
                <Link
                  href={`/jobs?${new URLSearchParams({
                    ...(q ? { q } : {}),
                    ...(source ? { source } : {}),
                    ...(company ? { company } : {}),
                    ...(location ? { location } : {}),
                    ...(workMode ? { work_mode: workMode } : {}),
                    ...(employmentType ? { employment_type: employmentType } : {}),
                    page: String(Math.max(1, data.page - 1)),
                  }).toString()}`}
                  className="rounded-xl border border-slate-200 px-3 py-2"
                >
                  Previous
                </Link>
                <Link
                  href={`/jobs?${new URLSearchParams({
                    ...(q ? { q } : {}),
                    ...(source ? { source } : {}),
                    ...(company ? { company } : {}),
                    ...(location ? { location } : {}),
                    ...(workMode ? { work_mode: workMode } : {}),
                    ...(employmentType ? { employment_type: employmentType } : {}),
                    page: String(data.page + 1),
                  }).toString()}`}
                  className="rounded-xl border border-slate-200 px-3 py-2"
                >
                  Next
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
