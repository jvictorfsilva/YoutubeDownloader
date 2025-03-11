import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pytubefix import YouTube
from moviepy import VideoFileClip, AudioFileClip
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_DIR = "/tmp/cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def gerar_nome_cache(url: str, formato: str, resolucao: str = None):
    video_id = url.split("v=")[-1].split("&")[0]
    resolucao_texto = resolucao if resolucao else "default"
    return os.path.join(CACHE_DIR, f"{video_id}_{formato}_{resolucao_texto}.mp4")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] Unhandled exception in route {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500, content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.get("/")
async def root():
    return {"message": "OK"}


@app.get("/download")
async def download_video(url: str, formato: str, resolucao: str = None):
    if formato not in ["audio", "video"]:
        raise HTTPException(
            status_code=400, detail="Invalid format. Choose 'audio' or 'video'."
        )

    cache_file = gerar_nome_cache(url, formato, resolucao)

    if os.path.exists(cache_file):
        return FileResponse(
            cache_file, media_type="video/mp4", filename=os.path.basename(cache_file)
        )

    try:
        yt = YouTube(url)
    except Exception as e:
        print(f"[ERROR] Failed to process YouTube URL: {url} | Exception: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to process YouTube URL: {str(e)}"
        )

    if formato == "video":
        try:
            video_stream = yt.streams.filter(
                adaptive=True, mime_type="video/mp4", res=resolucao
            ).first()
            if not video_stream:
                raise HTTPException(
                    status_code=404,
                    detail="Video stream with requested resolution not found.",
                )

            video_path = os.path.join(CACHE_DIR, f"{yt.video_id}_video.mp4")
            video_stream.download(
                output_path=CACHE_DIR, filename=f"{yt.video_id}_video.mp4"
            )

            audio_stream = yt.streams.filter(
                only_audio=True, mime_type="audio/mp4"
            ).first()
            if not audio_stream:
                raise HTTPException(status_code=404, detail="Audio stream not found.")
            audio_path = os.path.join(CACHE_DIR, f"{yt.video_id}_audio.mp4")
            audio_stream.download(
                output_path=CACHE_DIR, filename=f"{yt.video_id}_audio.mp4"
            )

            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            video_clip.audio = audio_clip

            video_clip.write_videofile(cache_file, codec="libx264", audio_codec="aac")
        except Exception as e:
            print(f"[ERROR] Error while processing video/audio merge: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error during video/audio processing: {str(e)}"
            )
        finally:
            try:
                video_clip.close()
                audio_clip.close()
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception as cleanup_err:
                print(
                    f"[WARNING] Error while cleaning up temporary files: {cleanup_err}"
                )

    elif formato == "audio":
        try:
            audio_stream = yt.streams.filter(
                only_audio=True, mime_type="audio/mp4"
            ).first()
            if not audio_stream:
                raise HTTPException(status_code=404, detail="Audio stream not found.")
            audio_stream.download(
                output_path=CACHE_DIR, filename=os.path.basename(cache_file)
            )
        except Exception as e:
            print(f"[ERROR] Error while downloading audio: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error during audio download: {str(e)}"
            )

    return FileResponse(
        cache_file, media_type="video/mp4", filename=os.path.basename(cache_file)
    )
