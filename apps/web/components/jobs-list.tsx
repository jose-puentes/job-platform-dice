"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";

type ActionKind = "apply" | "resume" | "cover-letter";
type ActionState = {
  apply?: string;
  resume?: string;
  coverLetter?: string;
};

type JobItem = {
  id: string;
  title: string;
  company: string;
  source: string;
  location: string | null;
  short_description: string | null;
  work_mode: string;
  employment_type: string;
  is_active: boolean;
};

type ApplicationItem = {
  id: string;
  job_id: string;
  application_status: string;
};

export function JobsList({
  jobs,
  empty,
  applications,
}: {
  jobs: JobItem[];
  empty: boolean;
  applications: ApplicationItem[];
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const [actionStatus, setActionStatus] = useState<Record<string, ActionState>>({});
  const [busyActions, setBusyActions] = useState<Record<string, ActionState>>({});
  const [appliedJobs, setAppliedJobs] = useState<Record<string, boolean>>(
    Object.fromEntries(
      applications
        .filter((application) => application.application_status === "applied")
        .map((application) => [application.job_id, true])
    )
  );
  const [archivedJobs, setArchivedJobs] = useState<Record<string, boolean>>(
    Object.fromEntries(jobs.filter((job) => !job.is_active).map((job) => [job.id, true]))
  );
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  function updateActionStatus(jobId: string, action: ActionKind, message: string) {
    setActionStatus((current) => ({
      ...current,
      [jobId]: {
        ...current[jobId],
        [action === "cover-letter" ? "coverLetter" : action]: message,
      },
    }));
  }

  function setActionBusy(jobId: string, action: ActionKind, value: boolean) {
    setBusyActions((current) => ({
      ...current,
      [jobId]: {
        ...current[jobId],
        [action === "cover-letter" ? "coverLetter" : action]: value ? "busy" : undefined,
      },
    }));
  }

  async function runBatchApply() {
    const eligibleJobIds = selected.filter((jobId) => {
      const job = jobs.find((item) => item.id === jobId);
      return job?.is_active && !archivedJobs[jobId] && !appliedJobs[jobId];
    });

    if (eligibleJobIds.length === 0) {
      return;
    }

    await fetch(`/api/apply-runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_ids: eligibleJobIds, triggered_by: "web" }),
    });

    setSelected([]);
    startTransition(() => {
      router.push("/applications");
      router.refresh();
    });
  }

  async function runJobAction(jobId: string, action: ActionKind) {
    const job = jobs.find((item) => item.id === jobId);
    if (!job) {
      return;
    }
    if (action === "apply" && (!job.is_active || archivedJobs[jobId] || appliedJobs[jobId])) {
      return;
    }
    if (action !== "apply" && (!job.is_active || archivedJobs[jobId])) {
      return;
    }

    const labels = {
      apply: "Applying...",
      resume: "Building resume...",
      "cover-letter": "Building cover letter...",
    } as const;

    setActionBusy(jobId, action, true);
    updateActionStatus(jobId, action, labels[action]);

    const endpoint =
      action === "apply"
        ? `/jobs/${jobId}/apply`
        : action === "resume"
          ? `/jobs/${jobId}/documents/resume`
          : `/jobs/${jobId}/documents/cover-letter`;

    try {
      const response = await fetch(`/api${endpoint}`, { method: "POST" });
      if (!response.ok) {
        throw new Error("Action failed");
      }

      updateActionStatus(
        jobId,
        action,
        action === "apply"
          ? "Apply run started"
          : action === "resume"
            ? "Resume generation started"
            : "Cover letter generation started"
      );
      startTransition(() => {
        router.refresh();
      });
    } catch {
      updateActionStatus(jobId, action, "Action failed");
    } finally {
      setActionBusy(jobId, action, false);
    }
  }

  useEffect(() => {
    const eventSource = new EventSource("/api/job-actions/stream");

    eventSource.addEventListener("document_generation.created", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      const run = payload.payload?.run;
      if (!run?.job_id) {
        return;
      }
      updateActionStatus(
        run.job_id,
        run.document_type === "resume" ? "resume" : "cover-letter",
        run.document_type === "resume" ? "Resume queued" : "Cover letter queued"
      );
    });

    eventSource.addEventListener("document_generation.updated", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      const run = payload.payload?.run;
      if (!run?.job_id) {
        return;
      }

      const nextLabel =
        run.status === "completed"
          ? run.document_type === "resume"
            ? "Resume ready"
            : "Cover letter ready"
          : run.status === "failed"
            ? `${run.document_type === "resume" ? "Resume" : "Cover letter"} failed`
            : `${run.document_type === "resume" ? "Resume" : "Cover letter"} generating...`;

      updateActionStatus(
        run.job_id,
        run.document_type === "resume" ? "resume" : "cover-letter",
        nextLabel
      );
    });

    eventSource.addEventListener("apply_attempt.created", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      const attempt = payload.payload?.attempt;
      if (!attempt?.job_id) {
        return;
      }
      updateActionStatus(attempt.job_id, "apply", "Apply queued");
    });

    eventSource.addEventListener("apply_attempt.updated", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      const attempt = payload.payload?.attempt;
      const application = payload.payload?.application;
      if (!attempt?.job_id) {
        return;
      }

      let nextLabel = "Applying...";
      if (attempt.status === "completed") {
        nextLabel =
          application?.application_status === "manual_assist"
            ? "Manual assist required"
            : application?.application_status === "failed"
              ? "Job unavailable. Archived."
              : "Application completed";
        if (application?.application_status === "applied") {
          setAppliedJobs((current) => ({ ...current, [attempt.job_id]: true }));
        }
        if (application?.application_status === "failed") {
          setArchivedJobs((current) => ({ ...current, [attempt.job_id]: true }));
        }
      } else if (attempt.status === "failed") {
        nextLabel = "Apply failed";
      }

      updateActionStatus(attempt.job_id, "apply", nextLabel);
    });

    return () => {
      eventSource.close();
    };
  }, []);

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
        const status = actionStatus[job.id];
        const busy = busyActions[job.id] ?? {};
        const isApplied = Boolean(appliedJobs[job.id]);
        const isArchived = !job.is_active || Boolean(archivedJobs[job.id]);

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
                disabled={isApplied || isArchived}
                onChange={(event) => {
                  setSelected((current) =>
                    event.target.checked
                      ? [...current, job.id]
                      : current.filter((item) => item !== job.id)
                  );
                }}
              />
              <div className="flex-1">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <Link href={`/jobs/${job.id}`} className="text-xl font-semibold text-slate-900">
                      {job.title}
                    </Link>
                    <p className="mt-1 text-sm text-slate-600">
                      {job.company} - {job.location ?? "Location not specified"} - {job.source}
                    </p>
                    {job.short_description && (
                      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
                        {job.short_description}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs font-medium">
                    <span
                      className={`rounded-full px-3 py-1 ${
                        isArchived
                          ? "bg-amber-100 text-amber-800"
                          : "bg-emerald-50 text-emerald-700"
                      }`}
                    >
                      {isArchived ? "archived" : "active"}
                    </span>
                    {isApplied && (
                      <span className="rounded-full bg-slate-900 px-3 py-1 text-white">
                        applied
                      </span>
                    )}
                    <span className="rounded-full bg-teal-50 px-3 py-1 text-teal-700">
                      {job.work_mode}
                    </span>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">
                      {job.employment_type}
                    </span>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => runJobAction(job.id, "apply")}
                    disabled={busy.apply === "busy" || isApplied || isArchived}
                    className="rounded-xl bg-slate-950 px-3 py-2 text-sm font-medium text-white disabled:bg-slate-300"
                  >
                    {busy.apply === "busy"
                      ? "Starting..."
                      : isApplied
                        ? "Applied"
                        : isArchived
                          ? "Archived"
                          : "Apply"}
                  </button>
                  <button
                    type="button"
                    onClick={() => runJobAction(job.id, "resume")}
                    disabled={busy.resume === "busy" || isArchived}
                    className="rounded-xl bg-teal-700 px-3 py-2 text-sm font-medium text-white disabled:bg-teal-300"
                  >
                    {busy.resume === "busy" ? "Starting..." : "Build Resume"}
                  </button>
                  <button
                    type="button"
                    onClick={() => runJobAction(job.id, "cover-letter")}
                    disabled={busy.coverLetter === "busy" || isArchived}
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 disabled:bg-slate-100"
                  >
                    {busy.coverLetter === "busy" ? "Starting..." : "Build Cover Letter"}
                  </button>
                </div>
                {status && (
                  <div className="mt-3 flex flex-wrap gap-2 text-xs">
                    {status.apply && (
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">
                        Apply: {status.apply}
                      </span>
                    )}
                    {status.resume && (
                      <span className="rounded-full bg-teal-50 px-3 py-1 text-teal-700">
                        Resume: {status.resume}
                      </span>
                    )}
                    {status.coverLetter && (
                      <span className="rounded-full bg-amber-50 px-3 py-1 text-amber-700">
                        Cover letter: {status.coverLetter}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </article>
        );
      })}
    </section>
  );
}
