"""YouTube 업로드 스테이지 - Google API로 영상 업로드."""
import logging
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class UploadStage(Stage):
    name = "upload"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        secrets = self.config.get("client_secrets_file", "client_secrets.json")
        if not Path(secrets).exists():
            log.warning(f"OAuth 클라이언트 시크릿 파일 없음: {secrets}")
            log.warning("업로드를 건너뜁니다. Google Cloud Console에서 OAuth 설정 필요.")
            return ctx

        flow = InstalledAppFlow.from_client_secrets_file(secrets, SCOPES)
        creds = flow.run_local_server(port=0)

        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": ctx.title,
                "description": ctx.description,
                "tags": ctx.tags,
                "categoryId": self.config.get("category_id", "28"),
            },
            "status": {
                "privacyStatus": self.config.get("privacy_status", "private"),
            },
        }

        log.info(f"영상 업로드 중: {ctx.video_path}")
        media = MediaFileUpload(str(ctx.video_path), mimetype="video/mp4", resumable=True)
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = req.execute()

        ctx.video_id = resp["id"]
        ctx.video_url = f"https://youtu.be/{resp['id']}"
        log.info(f"업로드 완료: {ctx.video_url}")

        # 썸네일 업로드
        if ctx.thumbnail_path and ctx.thumbnail_path.exists():
            log.info("썸네일 업로드 중...")
            youtube.thumbnails().set(
                videoId=ctx.video_id,
                media_body=MediaFileUpload(str(ctx.thumbnail_path), mimetype="image/png"),
            ).execute()
            log.info("썸네일 업로드 완료")

        return ctx
