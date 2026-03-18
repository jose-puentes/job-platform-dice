from uuid import UUID

from fastapi import APIRouter, Response

from app.clients.services import ai_service_client

router = APIRouter(tags=["documents"])


@router.get("/api/v1/documents/{document_id}/download")
async def download_document(document_id: UUID) -> Response:
    async with ai_service_client() as client:
        response = await client.get(f"/internal/documents/{document_id}/download")
        response.raise_for_status()
        return Response(
            content=response.content,
            media_type=response.headers.get(
                "content-type",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            headers={
                "content-disposition": response.headers.get("content-disposition", ""),
            },
        )
