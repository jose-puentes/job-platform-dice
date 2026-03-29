import { apiFetch } from "@/lib/api";
import { JobActionsPanel } from "./job-actions-panel";

type JobDetail = {
  id: string;
  title: string;
  company: string;
  source: string;
  location: string | null;
  work_mode: string;
  employment_type: string;
  description: string;
  application_url: string | null;
  job_url: string;
  is_active: boolean;
};

type DocumentItem = {
  id: string;
  document_type: string;
  generation_status: string;
};

type GenerationRunItem = {
  id: string;
  document_type: string;
  status: string;
  error_message: string | null;
};

type ApplicationItem = {
  id: string;
  application_status: string;
};

export default async function JobDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  const [job, documents, application] = await Promise.all([
    apiFetch<JobDetail>(`/jobs/${jobId}`),
    apiFetch<{ items: DocumentItem[]; generation_runs: GenerationRunItem[] }>(
      `/jobs/${jobId}/documents`
    ).catch(() => ({ items: [], generation_runs: [] })),
    apiFetch<ApplicationItem>(`/jobs/${jobId}/application`).catch(() => null),
  ]);

  return (
    <div className="space-y-6">
      <div className="rounded-[28px] bg-slate-950 px-6 py-8 text-white">
        <div className="text-sm uppercase tracking-[0.3em] text-teal-300">Job Detail</div>
        <h1 className="mt-3 text-3xl font-semibold">{job.title}</h1>
        <p className="mt-3 max-w-3xl text-slate-300">
          {job.company} - {job.location ?? "Location not specified"} - {job.source} -{" "}
          {job.work_mode} - {job.employment_type}
        </p>
        <div className="mt-4 flex flex-wrap gap-2 text-sm">
          <span className="rounded-full bg-white/10 px-3 py-1 text-slate-100">
            {job.is_active ? "Active" : "Archived"}
          </span>
          {application?.application_status === "applied" && (
            <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-emerald-100">
              Applied
            </span>
          )}
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr,360px]">
        <article className="rounded-[24px] border border-slate-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-slate-900">Description</h2>
          <p className="mt-4 whitespace-pre-wrap leading-7 text-slate-600">{job.description}</p>
        </article>
        <aside className="rounded-[24px] border border-slate-200 bg-slate-50 p-6">
          <h2 className="text-xl font-semibold text-slate-900">Actions</h2>
          <JobActionsPanel
            jobId={jobId}
            documents={documents}
            applicationLink={job.application_url ?? job.job_url}
            initialApplication={application}
            isJobActive={job.is_active}
          />
        </aside>
      </div>
    </div>
  );
}
