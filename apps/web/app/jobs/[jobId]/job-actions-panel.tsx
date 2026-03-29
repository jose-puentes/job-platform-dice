"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

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

type ApplyLogItem = {
  event_type: string;
  message: string;
  metadata: Record<string, unknown>;
  occurred_at: string;
};

type ApplicationItem = {
  id: string;
  application_status: string;
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
  initialApplication,
  isJobActive,
}: {
  jobId: string;
  documents: DocumentsPayload;
  applicationLink: string;
  initialApplication: ApplicationItem | null;
  isJobActive: boolean;
}) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [application, setApplication] = useState<ApplicationItem | null>(initialApplication);
  const [jobIsActive, setJobIsActive] = useState(isJobActive);
  const [actionStatus, setActionStatus] = useState<ActionStatus>({});
  const [busyAction, setBusyAction] = useState<ActionStatus>({});
  const [applyLogs, setApplyLogs] = useState<ApplyLogItem[]>([]);
  const router = useRouter();

  const hasResume = documents.items.some((document) => document.document_type === "resume");
  const hasCoverLetter = documents.items.some((document) => document.document_type === "cover_letter");
  const isApplied = application?.application_status === "applied";
  const isArchived = !jobIsActive;

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

      const response = await fetch(`/api/jobs/${jobId}/documents`, {
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
      const logs = (attempt.metadata?.logs as ApplyLogItem[] | undefined) ?? [];
      setApplyLogs(logs);

      if (attempt.status === "running") {
        setStatus("apply", "Applying...");
      } else if (attempt.status === "completed") {
        if (application) {
          setApplication(application);
        }
        if (application?.application_status === "failed") {
          setJobIsActive(false);
          router.refresh();
        }
        setStatus(
          "apply",
          application?.application_status === "manual_assist"
            ? "Manual assist required. Documents ready."
            : application?.application_status === "failed"
              ? "Job unavailable. Archived."
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
  }, [jobId, router]);

  async function runAction(action: "apply" | "resume" | "cover-letter") {
    const key = action === "cover-letter" ? "coverLetter" : action;
    if (action === "apply" && (isApplied || isArchived)) {
      return;
    }
    if (action === "resume" && hasResume) {
      return;
    }
    if (action === "cover-letter" && hasCoverLetter) {
      return;
    }
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

    const response = await fetch(`/api${endpoint}`, { method: "POST" });
    if (!response.ok) {
      setBusy(key, false);
      let nextMessage = action === "apply" ? "Failed to start apply run" : "Failed to start generation";
      try {
        const payload = (await response.json()) as { detail?: string };
        if (payload.detail) {
          nextMessage = payload.detail;
        }
      } catch {
        // Ignore non-JSON error payloads and keep the generic message.
      }
      setStatus(key, nextMessage);
    }
  }

  return (
    <>
      <div className="mt-4 space-y-3">
        <button
          type="button"
          onClick={() => runAction("apply")}
          disabled={busyAction.apply === "busy" || isApplied || isArchived}
          className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-medium text-white disabled:bg-slate-300"
        >
          {busyAction.apply === "busy"
            ? "Starting..."
            : isApplied
              ? "Applied"
              : isArchived
                ? "Archived"
                : "Apply"}
        </button>
        <button
          type="button"
          onClick={() => runAction("resume")}
          disabled={busyAction.resume === "busy" || hasResume}
          className="w-full rounded-2xl bg-teal-700 px-4 py-3 text-sm font-medium text-white disabled:bg-teal-400"
        >
          {busyAction.resume === "busy" ? "Starting..." : hasResume ? "Resume Ready" : "Build Resume"}
        </button>
        <button
          type="button"
          onClick={() => runAction("cover-letter")}
          disabled={busyAction.coverLetter === "busy" || hasCoverLetter}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:bg-slate-100"
        >
          {busyAction.coverLetter === "busy"
            ? "Starting..."
            : hasCoverLetter
              ? "Cover Letter Ready"
              : "Build Cover Letter"}
        </button>
      </div>
      {isArchived && (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          This job has been archived because it is no longer available to apply.
        </div>
      )}
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
      {applyLogs.length > 0 && (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="text-sm font-semibold text-slate-900">Apply progress</div>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            {applyLogs.map((log) => (
              <div key={`${log.event_type}-${log.occurred_at}`} className="rounded-xl bg-slate-50 px-3 py-2">
                <div className="font-medium text-slate-900">{log.message}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.15em] text-slate-500">
                  {log.event_type.replaceAll(".", " ")}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <DocumentPanel
        documents={documents}
        onDeleted={(document) => {
          setDocuments((current) => ({
            ...current,
            items: current.items.filter((item) => item.id !== document.id),
          }));
          if (document.document_type === "resume") {
            setActionStatus((current) => ({ ...current, resume: "Resume removed" }));
          }
          if (document.document_type === "cover_letter") {
            setActionStatus((current) => ({ ...current, coverLetter: "Cover letter removed" }));
          }
        }}
      />
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
