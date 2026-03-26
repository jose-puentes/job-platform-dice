"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type ScrapeRun = {
  id: string;
  source: string;
  query: string | null;
  location: string | null;
  status: string;
  total_tasks: number;
  completed_tasks: number;
  total_found: number;
  total_inserted: number;
  total_updated: number;
  total_duplicates: number;
  total_failed: number;
  created_at?: string;
  updated_at?: string;
};

type ScrapeRunsDashboardProps = {
  initialRuns: ScrapeRun[];
};

type ScrapeRunEventEnvelope = {
  event_type: string;
  payload: {
    run: ScrapeRun;
  };
};

function getStatusClasses(status: string): string {
  if (status === "completed") {
    return "bg-emerald-50 text-emerald-700";
  }
  if (status === "failed") {
    return "bg-rose-50 text-rose-700";
  }
  if (status === "partial") {
    return "bg-amber-50 text-amber-700";
  }
  return "bg-sky-50 text-sky-700";
}

function upsertRun(currentRuns: ScrapeRun[], nextRun: ScrapeRun): ScrapeRun[] {
  const existingIndex = currentRuns.findIndex((run) => run.id === nextRun.id);

  if (existingIndex === -1) {
    return [nextRun, ...currentRuns];
  }

  const updatedRuns = [...currentRuns];
  updatedRuns[existingIndex] = nextRun;
  return updatedRuns;
}

export function ScrapeRunsDashboard({ initialRuns }: ScrapeRunsDashboardProps) {
  const [runs, setRuns] = useState(initialRuns);
  const [connectionState, setConnectionState] = useState<"connecting" | "live" | "disconnected">(
    "connecting"
  );
  const router = useRouter();

  useEffect(() => {
    setRuns(initialRuns);
  }, [initialRuns]);

  useEffect(() => {
    const eventSource = new EventSource("/api/scrape-runs/stream");

    const handleRunEvent = (event: MessageEvent<string>) => {
      const envelope = JSON.parse(event.data) as ScrapeRunEventEnvelope;
      setRuns((currentRuns) => upsertRun(currentRuns, envelope.payload.run));
    };

    eventSource.addEventListener("connected", () => {
      setConnectionState("live");
    });
    eventSource.addEventListener("scrape_run.created", handleRunEvent);
    eventSource.addEventListener("scrape_run.updated", handleRunEvent);
    eventSource.onopen = () => {
      setConnectionState("live");
    };
    eventSource.onerror = () => {
      setConnectionState("disconnected");
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-[24px] border border-slate-200 bg-slate-50 p-4">
        <div className="text-sm text-slate-600">
          {connectionState === "live" &&
            "Live updates are connected. New run events are pushed to this page automatically."}
          {connectionState === "connecting" && "Connecting to live scrape updates..."}
          {connectionState === "disconnected" &&
            "Live updates are temporarily disconnected. You can reconnect by refreshing the page."}
        </div>
        <button
          type="button"
          onClick={() => router.refresh()}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700"
        >
          Refresh now
        </button>
      </div>

      {runs.length === 0 && (
        <div className="rounded-[24px] border border-slate-200 bg-white p-6 text-slate-600">
          No scrape runs yet. Start one to begin the ingestion pipeline.
        </div>
      )}

      <div className="space-y-4">
        {runs.map((run) => (
          <article key={run.id} className="rounded-[24px] border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">{run.source}</h2>
                <p className="mt-1 text-sm text-slate-600">
                  {run.query ?? "No query"} - {run.location ?? "No location"}
                </p>
              </div>
              <div
                className={`rounded-full px-3 py-1 text-sm font-medium capitalize ${getStatusClasses(run.status)}`}
              >
                {run.status}
              </div>
            </div>
            <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-3 xl:grid-cols-6">
              <div className="rounded-2xl bg-slate-50 p-3">
                Tasks: {run.completed_tasks}/{run.total_tasks}
              </div>
              <div className="rounded-2xl bg-slate-50 p-3">Found: {run.total_found}</div>
              <div className="rounded-2xl bg-slate-50 p-3">Inserted: {run.total_inserted}</div>
              <div className="rounded-2xl bg-slate-50 p-3">Updated: {run.total_updated}</div>
              <div className="rounded-2xl bg-slate-50 p-3">
                Duplicates: {run.total_duplicates}
              </div>
              <div className="rounded-2xl bg-slate-50 p-3">Failed: {run.total_failed}</div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
