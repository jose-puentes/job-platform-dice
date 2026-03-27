import { getApiBaseUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ documentId: string }> }
) {
  const { documentId } = await params;
  const response = await fetch(`${getApiBaseUrl()}/documents/${documentId}/download`, {
    cache: "no-store",
  });

  if (!response.ok) {
    return new Response("Unable to download document.", { status: response.status });
  }

  const headers = new Headers();
  headers.set("Cache-Control", "no-store");
  headers.set(
    "Content-Type",
    response.headers.get("content-type") ??
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  );

  const contentDisposition = response.headers.get("content-disposition");
  if (contentDisposition) {
    headers.set("Content-Disposition", contentDisposition);
  }

  return new Response(response.body, { headers });
}
