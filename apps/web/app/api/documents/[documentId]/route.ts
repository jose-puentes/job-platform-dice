import { getApiBaseUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ documentId: string }> }
) {
  const { documentId } = await params;
  const response = await fetch(`${getApiBaseUrl()}/documents/${documentId}`, {
    method: "DELETE",
    cache: "no-store",
  });

  return new Response(response.body, {
    status: response.status,
    headers: {
      "Cache-Control": "no-store",
    },
  });
}
