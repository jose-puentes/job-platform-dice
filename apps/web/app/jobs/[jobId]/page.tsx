import { apiFetch } from "@/lib/api";
import { applyToJob, generateCoverLetter, generateResume } from "./actions";

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

export default async function JobDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  const [job, documents] = await Promise.all([
    apiFetch<JobDetail>(`/jobs/${jobId}`),
    apiFetch<{ items: DocumentItem[]; generation_runs: GenerationRunItem[] }>(
      `/jobs/${jobId}/documents`
    ).catch(() => ({ items: [], generation_runs: [] })),
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
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr,360px]">
        <article className="rounded-[24px] border border-slate-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-slate-900">Description</h2>
          <p className="mt-4 whitespace-pre-wrap leading-7 text-slate-600">{job.description}</p>
        </article>
        <aside className="rounded-[24px] border border-slate-200 bg-slate-50 p-6">
          <h2 className="text-xl font-semibold text-slate-900">Actions</h2>
          <div className="mt-4 space-y-3">
            <form action={applyToJob.bind(null, jobId)}>
              <button className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-medium text-white">
                Apply
              </button>
            </form>
            <form action={generateResume.bind(null, jobId)}>
              <button className="w-full rounded-2xl bg-teal-700 px-4 py-3 text-sm font-medium text-white">
                Build Resume
              </button>
            </form>
            <form action={generateCoverLetter.bind(null, jobId)}>
              <button className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900">
                Build Cover Letter
              </button>
            </form>
          </div>
          <div className="mt-4 space-y-2 text-sm text-slate-600">
            {documents.items.length === 0 && documents.generation_runs.length === 0 && (
              <div>No generated documents yet.</div>
            )}
            {documents.generation_runs.map((run) => (
              <div key={run.id} className="rounded-2xl border border-slate-200 bg-white px-3 py-2">
                <div>
                  {run.document_type} generation - {run.status}
                </div>
                {run.error_message && <div className="mt-1 text-rose-600">{run.error_message}</div>}
              </div>
            ))}
            {documents.items.map((document) => (
              <div
                key={document.id}
                className="rounded-2xl border border-slate-200 bg-white px-3 py-3"
              >
                <div className="font-medium text-slate-900">
                  {document.document_type.replaceAll("_", " ")} - {document.generation_status}
                </div>
                <div className="mt-2 flex gap-3 text-sm">
                  <a
                    href={`/api/documents/${document.id}/preview`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-teal-700 underline"
                  >
                    Preview
                  </a>
                  <a
                    href={`/api/documents/${document.id}/download`}
                    className="text-slate-700 underline"
                  >
                    Download
                  </a>
                </div>
              </div>
            ))}
          </div>
          <a
            href={job.application_url ?? job.job_url}
            target="_blank"
            rel="noreferrer"
            className="mt-4 block text-sm text-slate-500 underline"
          >
            Open original application
          </a>
        </aside>
      </div>
    </div>
  );
}
