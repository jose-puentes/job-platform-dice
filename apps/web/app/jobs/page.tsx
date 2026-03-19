import Link from "next/link";

import { JobsList } from "@/components/jobs-list";
import { apiFetch } from "@/lib/api";

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

type JobFiltersResponse = {
  sources: string[];
  companies: string[];
  locations: string[];
  work_modes: string[];
  employment_types: string[];
};

function buildQuery(params: Record<string, string>) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });

  return query;
}

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
  const postedWithinDays =
    typeof params.posted_within_days === "string" ? params.posted_within_days : "";
  const salaryMin = typeof params.salary_min === "string" ? params.salary_min : "";
  const salaryMax = typeof params.salary_max === "string" ? params.salary_max : "";
  const sort = typeof params.sort === "string" ? params.sort : "posted_at_desc";
  const page = typeof params.page === "string" ? params.page : "1";
  const filtersFallback: JobFiltersResponse = {
    sources: [],
    companies: [],
    locations: [],
    work_modes: ["remote", "hybrid", "onsite", "unknown"],
    employment_types: ["full_time", "part_time", "contract", "internship", "temporary", "unknown"],
  };

  let data: JobsResponse | null = null;
  let filters = filtersFallback;
  let error = false;

  try {
    const query = buildQuery({
      q,
      source,
      company,
      location,
      work_mode: workMode,
      employment_type: employmentType,
      posted_within_days: postedWithinDays,
      salary_min: salaryMin,
      salary_max: salaryMax,
      sort,
      page,
    });
    [data, filters] = await Promise.all([
      apiFetch<JobsResponse>(`/jobs?${query.toString()}`),
      apiFetch<JobFiltersResponse>("/jobs/filters").catch(() => filtersFallback),
    ]);
  } catch {
    error = true;
  }

  const baseQuery = {
    ...(q ? { q } : {}),
    ...(source ? { source } : {}),
    ...(company ? { company } : {}),
    ...(location ? { location } : {}),
    ...(workMode ? { work_mode: workMode } : {}),
    ...(employmentType ? { employment_type: employmentType } : {}),
    ...(postedWithinDays ? { posted_within_days: postedWithinDays } : {}),
    ...(salaryMin ? { salary_min: salaryMin } : {}),
    ...(salaryMax ? { salary_max: salaryMax } : {}),
    ...(sort ? { sort } : {}),
  };

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
          Search, filter, paginate, and batch apply now flow through the gateway-backed catalog.
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
            <select
              name="source"
              defaultValue={source}
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            >
              <option value="">All sources</option>
              {filters.sources.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <input
              name="company"
              defaultValue={company}
              placeholder="Company"
              list="job-company-options"
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            />
            <datalist id="job-company-options">
              {filters.companies.map((item) => (
                <option key={item} value={item} />
              ))}
            </datalist>
            <input
              name="location"
              defaultValue={location}
              placeholder="Location"
              list="job-location-options"
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            />
            <datalist id="job-location-options">
              {filters.locations.map((item) => (
                <option key={item} value={item} />
              ))}
            </datalist>
            <select
              name="work_mode"
              defaultValue={workMode}
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            >
              <option value="">Any work mode</option>
              {filters.work_modes.map((item) => (
                <option key={item} value={item}>
                  {item.replaceAll("_", " ")}
                </option>
              ))}
            </select>
            <select
              name="employment_type"
              defaultValue={employmentType}
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            >
              <option value="">Any employment type</option>
              {filters.employment_types.map((item) => (
                <option key={item} value={item}>
                  {item.replaceAll("_", " ")}
                </option>
              ))}
            </select>
            <select
              name="posted_within_days"
              defaultValue={postedWithinDays}
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            >
              <option value="">Any posted date</option>
              <option value="1">Last 24 hours</option>
              <option value="7">Last 7 days</option>
              <option value="14">Last 14 days</option>
              <option value="30">Last 30 days</option>
            </select>
            <div className="grid grid-cols-2 gap-3">
              <input
                name="salary_min"
                type="number"
                min="0"
                step="1000"
                defaultValue={salaryMin}
                placeholder="Min salary"
                className="w-full rounded-2xl border border-slate-200 bg-white p-3"
              />
              <input
                name="salary_max"
                type="number"
                min="0"
                step="1000"
                defaultValue={salaryMax}
                placeholder="Max salary"
                className="w-full rounded-2xl border border-slate-200 bg-white p-3"
              />
            </div>
            <select
              name="sort"
              defaultValue={sort}
              className="w-full rounded-2xl border border-slate-200 bg-white p-3"
            >
              <option value="posted_at_desc">Newest first</option>
              <option value="posted_at_asc">Oldest first</option>
              <option value="salary_desc">Highest salary</option>
              <option value="salary_asc">Lowest salary</option>
              <option value="company_asc">Company A-Z</option>
              <option value="title_asc">Title A-Z</option>
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
              <div>Page {data.page} - {data.total} total jobs</div>
              <div className="flex gap-3">
                <Link
                  href={`/jobs?${buildQuery({
                    ...baseQuery,
                    page: String(Math.max(1, data.page - 1)),
                  }).toString()}`}
                  className="rounded-xl border border-slate-200 px-3 py-2"
                >
                  Previous
                </Link>
                <Link
                  href={`/jobs?${buildQuery({
                    ...baseQuery,
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
