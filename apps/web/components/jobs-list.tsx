"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { apiBaseUrl } from "@/lib/api";

type JobItem = {
  id: string;
  title: string;
  company: string;
  source: string;
  location: string | null;
  work_mode: string;
  employment_type: string;
};

export function JobsList({
  jobs,
  empty,
}: {
  jobs: JobItem[];
  empty: boolean;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  async function runBatchApply() {
    if (selected.length === 0) {
      return;
    }

    await fetch(`${apiBaseUrl}/apply-runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_ids: selected, triggered_by: "web" }),
    });

    setSelected([]);
    startTransition(() => {
      router.push("/applications");
      router.refresh();
    });
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3 rounded-[24px] border border-slate-200 bg-slate-50 p-4">
        <div className="text-sm text-slate-600">{selected.length} selected</div>
        <button
          onClick={runBatchApply}
          disabled={selected.length === 0 || isPending}
          className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Batch Apply
        </button>
      </div>
      {empty && (
        <div className="rounded-[24px] border border-slate-200 bg-white p-5 text-slate-600">
          No jobs are searchable yet. Trigger a scrape run to populate the catalog.
        </div>
      )}
      {jobs.map((job) => {
        const checked = selected.includes(job.id);
        return (
          <article
            key={job.id}
            className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300 hover:shadow-panel"
          >
            <div className="flex items-start gap-4">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-slate-300"
                checked={checked}
                onChange={(event) => {
                  setSelected((current) =>
                    event.target.checked
                      ? [...current, job.id]
                      : current.filter((item) => item !== job.id)
                  );
                }}
              />
              <Link href={`/jobs/${job.id}`} className="flex-1">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-semibold text-slate-900">{job.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {job.company} - {job.location ?? "Location not specified"} - {job.source}
                    </p>
                  </div>
                  <div className="flex gap-2 text-xs font-medium">
                    <span className="rounded-full bg-teal-50 px-3 py-1 text-teal-700">
                      {job.work_mode}
                    </span>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">
                      {job.employment_type}
                    </span>
                  </div>
                </div>
              </Link>
            </div>
          </article>
        );
      })}
    </section>
  );
}
