"use client";

import { useState } from "react";

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

export function DocumentPanel({
  documents,
  onDeleted,
}: {
  documents: { items: DocumentItem[]; generation_runs: GenerationRunItem[] };
  onDeleted?: (document: DocumentItem) => void;
}) {
  const [previewDocumentId, setPreviewDocumentId] = useState<string | null>(null);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const latestDocuments = new Map<string, DocumentItem>();
  const latestRuns = new Map<string, GenerationRunItem>();

  for (const document of documents.items) {
    if (!latestDocuments.has(document.document_type)) {
      latestDocuments.set(document.document_type, document);
    }
  }

  for (const run of documents.generation_runs) {
    if (!latestRuns.has(run.document_type)) {
      latestRuns.set(run.document_type, run);
    }
  }

  const visibleRuns = Array.from(latestRuns.values()).filter((run) => {
    const matchingDocument = latestDocuments.get(run.document_type);
    return !matchingDocument || run.status !== "completed";
  });
  const visibleDocuments = Array.from(latestDocuments.values());

  async function removeDocument(document: DocumentItem) {
    setDeletingDocumentId(document.id);
    try {
      const response = await fetch(`/api/documents/${document.id}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error("Failed to delete document");
      }
      onDeleted?.(document);
      if (previewDocumentId === document.id) {
        setPreviewDocumentId(null);
      }
    } finally {
      setDeletingDocumentId(null);
    }
  }

  return (
    <div className="mt-4 space-y-3 text-sm text-slate-600">
      {visibleDocuments.length === 0 && visibleRuns.length === 0 && (
        <div>No generated documents yet.</div>
      )}
      {visibleRuns.map((run) => (
        <div key={run.id} className="rounded-2xl border border-slate-200 bg-white px-3 py-2">
          <div className="flex items-center justify-between gap-3">
            <div className="font-medium text-slate-900">
              {run.document_type.replaceAll("_", " ")} generation
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
              {run.status}
            </span>
          </div>
          {run.error_message && <div className="mt-1 text-rose-600">{run.error_message}</div>}
        </div>
      ))}
      {visibleDocuments.map((document) => (
        <div key={document.id} className="rounded-2xl border border-slate-200 bg-white px-3 py-3">
          <div className="flex items-center justify-between gap-3">
            <div className="font-medium text-slate-900">
              {document.document_type.replaceAll("_", " ")}
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs text-emerald-700">
                {document.generation_status}
              </span>
              <button
                type="button"
                onClick={() => removeDocument(document)}
                disabled={deletingDocumentId === document.id}
                className="text-xs text-rose-600 underline disabled:text-rose-300"
              >
                {deletingDocumentId === document.id ? "Removing..." : "Remove"}
              </button>
            </div>
          </div>
          <div className="mt-2 flex gap-3 text-sm">
            <button
              type="button"
              onClick={() => setPreviewDocumentId(document.id)}
              className="text-teal-700 underline"
            >
              Preview
            </button>
            <a href={`/api/documents/${document.id}/download`} className="text-slate-700 underline">
              Download
            </a>
          </div>
        </div>
      ))}

      {previewDocumentId && (
        <div className="fixed inset-0 z-50 bg-slate-950/45">
          <div className="ml-auto flex h-full w-full max-w-5xl flex-col overflow-hidden bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <div>
                <div className="text-sm uppercase tracking-[0.2em] text-slate-500">Document Preview</div>
                <div className="text-lg font-semibold text-slate-900">Generated document</div>
              </div>
              <button
                type="button"
                onClick={() => setPreviewDocumentId(null)}
                className="rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700"
              >
                Close
              </button>
            </div>
            <iframe
              src={`/api/documents/${previewDocumentId}/preview`}
              className="min-h-0 flex-1 bg-slate-50"
              title="Document preview"
            />
          </div>
        </div>
      )}
    </div>
  );
}
