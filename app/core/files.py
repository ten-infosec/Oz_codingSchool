import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status


# ===== Media Files (5일차 명세 1-5, 담당: 엄태은) =====
# 업로드 파일을 서버 로컬 저장소(media/)에 저장하고 지우는 공통 도구


# 프로젝트 최상위/media (app/main.py가 /media 주소로 이 폴더를 연결해 둠)
MEDIA_ROOT = Path(__file__).resolve().parent.parent.parent / "media"
XRAY_DIR = MEDIA_ROOT / "xray"

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB

# 허용 형식: 확장자 + 파일 맨 앞 바이트(시그니처)
# content_type은 클라이언트가 마음대로 적을 수 있어서, 파일 내용의 시그니처까지 확인한다
_IMAGE_SIGNATURES = {
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8\xff",
}


def _detect_extension(head: bytes) -> str | None:
    for ext, signature in _IMAGE_SIGNATURES.items():
        if head.startswith(signature):
            return ext
    return None


async def save_xray_image(upload: UploadFile) -> tuple[Path, str]:
    """X-ray 이미지를 검증하고 저장한다. (저장 경로, 응답용 URL)을 돌려준다."""
    # 10MB를 1바이트라도 넘는지 알기 위해 최대 10MB+1바이트까지만 읽는다
    content = await upload.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="이미지는 10MB 이하만 업로드할 수 있습니다.",
        )

    ext = _detect_extension(content[:8])
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="jpeg 또는 png 이미지만 업로드할 수 있습니다.",
        )

    # 원래 파일 이름은 쓰지 않는다 (덮어쓰기·경로 조작 방지) → 랜덤 이름
    XRAY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    path = XRAY_DIR / filename
    path.write_bytes(content)

    return path, f"/media/xray/{filename}"


def delete_media_file(url: str) -> None:
    """/media/... 주소에 해당하는 파일을 지운다. 이미 없으면 넘어간다."""
    if not url.startswith("/media/"):
        return
    path = (MEDIA_ROOT / url.removeprefix("/media/")).resolve()
    # media 폴더 밖의 파일은 절대 지우지 않는다
    if MEDIA_ROOT.resolve() not in path.parents:
        return
    path.unlink(missing_ok=True)


def media_url_to_path(url: str) -> Path:
    """/media/... 주소를 실제 파일 경로로 바꾼다. (6일차 AI 예측에서 X-ray 파일을 열 때 사용)"""
    # media 폴더 밖을 가리키는 주소(../ 등)는 없는 파일로 취급한다
    path = (MEDIA_ROOT / url.removeprefix("/media/")).resolve()
    if not url.startswith("/media/") or MEDIA_ROOT.resolve() not in path.parents:
        raise FileNotFoundError(f"media 폴더 밖의 경로입니다: {url}")
    return path
