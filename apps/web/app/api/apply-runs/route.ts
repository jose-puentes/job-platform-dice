import { getApiBaseUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.text();
  const response = await fetch(`${getApiBaseUrl()}/apply-runs`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json",
    },
    body,
  });

  return new Response(response.body, {
    status: response.status,
    headers: {
      "Cache-Control": "no-store",
      "Content-Type": response.headers.get("content-type") ?? "application/json",
    },
  });
}
