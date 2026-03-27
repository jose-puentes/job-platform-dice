"use client";

import { useEffect, useState } from "react";

import { apiBaseUrl } from "@/lib/api";
import { DocumentPanel } from "./document-panel";

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

type DocumentsPayload = {
  items: DocumentItem[];
  generation_runs: GenerationRunItem[];
};

type ActionStatus = {
  apply?: string;
  resume?: string;
  coverLetter?: string;
};

export function JobActionsPanel({
  jobId,
  documents: initialDocuments,
  applicationLink,
}: {
  jobId: string;
  documents: DocumentsPayload;
  applicationLink: string;
}) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [actionStatus, setActionStatus] = useState<ActionStatus>({});
  const [busyAction, setBusyAction] = useState<ActionStatus>({});

  function setStatus(key: keyof ActionStatus, value: string) {
    setActionStatus((current) => ({ ...current, [key]: value }));
  }

  function setBusy(key: keyof ActionStatus, value: boolean) {
    setBusyAction((current) => ({ ...current, [key]: value ? "busy" : undefined }));
  }

  useEffect(() => {
    const eventSource = new EventSource("/api/job-actions/stream");

    eventSource.addEventListener("document_generation.created", async (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      if (payload.payload?.run?.job_id !== jobId) {
        return;
      }

      const run = payload.payload.run;
      setBusy(run.document_type === "resume" ? "resume" : "coverLetter", false);
      setStatus(
        run.document_type === "resume" ? "resume" : "coverLetter",
        run.document_type === "resume" ? "Resume queued" : "Cover letter queued"
      );
      setDocuments((current) => ({
        ...current,
        generation_runs: [
          {
            id: run.id,
            document_type: run.document_type,
            status: run.status,
            error_message: run.error_message ?? null,
          },
          ...current.generation_runs.filter((item) => item.id !== run.id),
        ],
      }));
    });

    eventSource.addEventListener("document_generation.updated", async (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      if (payload.payload?.run?.job_id !== jobId) {
        return;
      }
      const run = payload.payload.run;

      const response = await fetch(`${apiBaseUrl}/jobs/${jobId}/documents`, {
        cache: "no-store",
      });
      if (response.ok) {
        const next = (await response.json()) as DocumentsPayload;
        setDocuments(next);
      }
      setBusy(run.document_type === "resume" ? "resume" : "coverLetter", false);
      setStatus(
        run.document_type === "resume" ? "resume" : "coverLetter",
        run.status === "completed"
          ? run.document_type === "resume"
            ? "Resume ready"
            : "Cover letter ready"
          : run.status === "failed"
            ? run.error_message || "Generation failed"
            : run.document_type === "resume"
              ? "Resume generating..."
              : "Cover letter generating..."
      );
    });

    eventSource.addEventListener("apply_attempt.created", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      if (payload.payload?.attempt?.job_id !== jobId) {
        return;
      }
      setBusy("apply", false);
      setStatus("apply", "Apply run queued");
    });

    eventSource.addEventListener("apply_attempt.updated", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      if (payload.payload?.attempt?.job_id !== jobId) {
        return;
      }

      const attempt = payload.payload.attempt;
      const application = payload.payload.application;

      if (attempt.status === "running") {
        setStatus("apply", "Applying...");
      } else if (attempt.status === "completed") {
        setStatus(
          "apply",
          application?.application_status === "manual_assist"
            ? "Manual assist required. Documents ready."
            : "Application completed"
        );
      } else if (attempt.status === "failed") {
        setStatus("apply", attempt.error_message || "Apply failed");
      }
      setBusy("apply", false);
    });

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  async function runAction(action: "apply" | "resume" | "cover-letter") {
    const key = action === "cover-letter" ? "coverLetter" : action;
    setBusy(key, true);
    if (action === "apply") {
      setStatus("apply", "Starting apply run...");
    } else if (action === "resume") {
      setStatus("resume", "Starting resume generation...");
    } else {
      setStatus("coverLetter", "Starting cover letter generation...");
    }

    const endpoint =
      action === "apply"
        ? `/jobs/${jobId}/apply`
        : action === "resume"
          ? `/jobs/${jobId}/documents/resume`
          : `/jobs/${jobId}/documents/cover-letter`;

    const response = await fetch(`${apiBaseUrl}${endpoint}`, { method: "POST" });
    if (!response.ok) {
      setBusy(key, false);
      setStatus(key, action === "apply" ? "Failed to start apply run" : "Failed to start generation");
    }
  }

  return (
    <>
      <div className="mt-4 space-y-3">
        <button
          type="button"
          onClick={() => runAction("apply")}
          disabled={busyAction.apply === "busy"}
          className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-medium text-white disabled:bg-slate-300"
        >
          {busyAction.apply === "busy" ? "Starting..." : "Apply"}
        </button>
        <button
          type="button"
          onClick={() => runAction("resume")}
          disabled={busyAction.resume === "busy"}
          className="w-full rounded-2xl bg-teal-700 px-4 py-3 text-sm font-medium text-white disabled:bg-teal-400"
        >
          {busyAction.resume === "busy" ? "Starting..." : "Build Resume"}
        </button>
        <button
          type="button"
          onClick={() => runAction("cover-letter")}
          disabled={busyAction.coverLetter === "busy"}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:bg-slate-100"
        >
          {busyAction.coverLetter === "busy" ? "Starting..." : "Build Cover Letter"}
        </button>
      </div>
      {(actionStatus.apply || actionStatus.resume || actionStatus.coverLetter) && (
        <div className="mt-4 flex flex-wrap gap-2 text-xs">
          {actionStatus.apply && (
            <span className="rounded-full bg-white px-3 py-2 text-slate-700">
              Apply: {actionStatus.apply}
            </span>
          )}
          {actionStatus.resume && (
            <span className="rounded-full bg-teal-50 px-3 py-2 text-teal-700">
              Resume: {actionStatus.resume}
            </span>
          )}
          {actionStatus.coverLetter && (
            <span className="rounded-full bg-amber-50 px-3 py-2 text-amber-700">
              Cover letter: {actionStatus.coverLetter}
            </span>
          )}
        </div>
      )}
      <DocumentPanel documents={documents} />
      <a
        href={applicationLink}
        target="_blank"
        rel="noreferrer"
        className="mt-4 block text-sm text-slate-500 underline"
      >
        Open original application
      </a>
    </>
  );
}
