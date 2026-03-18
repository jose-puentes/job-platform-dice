import { apiBaseUrl, apiFetch } from "@/lib/api";

type DocumentItem = {
  id: string;
  job_id: string;
  document_type: string;
  generation_status: string;
  file_path: string;
  model_name: string;
};

type JobItem = {
  id: string;
  title: string;
};

type JobsResponse = {
  items: JobItem[];
};

export default async function DocumentsPage() {
  let jobs: JobsResponse | null = null;
  let documents: DocumentItem[] = [];

  try {
    jobs = await apiFetch<JobsResponse>("/jobs?page_size=5");
    const lists = await Promise.all(
      jobs.items.map(async (job) => {
        const response = await apiFetch<{ items: DocumentItem[] }>(`/jobs/${job.id}/documents`);
        return response.items.map((document) => ({ ...document, jobTitle: job.title }));
      })
    );
    documents = lists.flat();
  } catch {
    documents = [];
  }

  return (
    <div className="space-y-4">
      <div className="text-sm uppercase tracking-[0.3em] text-slate-500">Generated Files</div>
      <h1 className="text-3xl font-semibold text-slate-900">Documents</h1>
      <div className="space-y-4">
        {documents.length === 0 && (
          <div className="rounded-[24px] border border-slate-200 bg-white p-6 text-slate-600">
            No generated documents yet. Trigger resume or cover letter generation from a job detail page.
          </div>
        )}
        {documents.map((document) => (
          <article key={document.id} className="rounded-[24px] border border-slate-200 bg-white p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{document.document_type}</h2>
                <p className="mt-1 text-sm text-slate-600">{document.file_path}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
                  {document.generation_status}
                </div>
                <a
                  href={`${apiBaseUrl}/documents/${document.id}/download`}
                  className="rounded-xl bg-slate-950 px-3 py-2 text-sm font-medium text-white"
                >
                  Download
                </a>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
