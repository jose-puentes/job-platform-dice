import { getApiBaseUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET() {
  const response = await fetch(`${getApiBaseUrl()}/scrape-runs/stream`, {
    cache: "no-store",
  });

  if (!response.ok || !response.body) {
    return new Response("Unable to open scrape run event stream.", { status: 502 });
  }

  return new Response(response.body, {
    headers: {
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "Content-Type": "text/event-stream",
      "X-Accel-Buffering": "no",
    },
  });
}
