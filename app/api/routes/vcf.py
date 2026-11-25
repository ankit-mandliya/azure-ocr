from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.vcf import VCFPreviewResponse
from app.services.vcf_service import VCFParseError, parse_vcf

router = APIRouter(prefix="/vcf", tags=["VCF"])

MAX_VCF_BYTES = 10 * 1024 * 1024
HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


@router.post("/preview", response_model=VCFPreviewResponse)
async def preview_vcf(file: UploadFile = File(..., description="VCF contact file")):
    filename = file.filename or ""
    if not filename.lower().endswith(".vcf"):
        raise HTTPException(status_code=400, detail="Please upload a valid .vcf file.")

    file_bytes = await file.read(MAX_VCF_BYTES + 1)
    if len(file_bytes) > MAX_VCF_BYTES:
        raise HTTPException(status_code=413, detail="The VCF file exceeds the 10 MB upload limit.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded VCF file is empty.")

    try:
        contacts = parse_vcf(file_bytes)
    except VCFParseError as exc:
        raise HTTPException(status_code=HTTP_422, detail=str(exc)) from exc

    return VCFPreviewResponse(
        filename=filename,
        total_contacts=len(contacts),
        contacts=contacts,
    )
