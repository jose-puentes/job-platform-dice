import { getApiBaseUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ documentId: string }> }
) {
  const { documentId } = await params;
  const response = await fetch(`${getApiBaseUrl()}/documents/${documentId}/preview`, {
    cache: "no-store",
  });

  if (!response.ok) {
    return new Response("Unable to preview document.", { status: response.status });
  }

  return new Response(response.body, {
    headers: {
      "Cache-Control": "no-store",
      "Content-Type": response.headers.get("content-type") ?? "text/html; charset=utf-8",
    },
  });
}
