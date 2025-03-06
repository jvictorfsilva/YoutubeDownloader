import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pytubefix import YouTube  # certifique-se de instalar e usar a versão corrigida do pytube
from moviepy import VideoFileClip, AudioFileClip
from tempfile import NamedTemporaryFile

app = FastAPI()

# Diretório para armazenar os arquivos baixados em cache
CACHE_DIR = "./cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def gerar_nome_cache(url: str, formato: str, resolucao: str = None):
    """
    Gera um nome de arquivo único para o cache baseado na URL, formato e resolução.
    """
    # Extraindo o ID do vídeo (exemplo simples, pode ser melhorado)
    video_id = url.split("v=")[-1].split("&")[0]
    resolucao_texto = resolucao if resolucao else "default"
    return os.path.join(CACHE_DIR, f"{video_id}_{formato}_{resolucao_texto}.mp4")

@app.get("/download")
async def download_video(url: str, formato: str, resolucao: str = None):
    """
    Endpoint que processa o download do vídeo ou apenas do áudio.
    Parâmetros:
      - url: URL do vídeo do YouTube.
      - formato: "video" ou "audio".
      - resolucao: (opcional) resolução desejada para vídeo (ex: "720p").
    """
    if formato not in ["audio", "video"]:
        raise HTTPException(status_code=400, detail="Formato inválido. Escolha 'audio' ou 'video'.")
    
    cache_file = gerar_nome_cache(url, formato, resolucao)
    
    # Se o arquivo já foi baixado, retorna do cache
    if os.path.exists(cache_file):
        return FileResponse(cache_file, media_type='video/mp4', filename=os.path.basename(cache_file))
    
    try:
        yt = YouTube(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar URL: {e}")
    
    if formato == "video":
        # Seleciona o stream de vídeo com o método DASH para a resolução escolhida
        video_stream = yt.streams.filter(adaptive=True, mime_type="video/mp4", res=resolucao).first()
        if not video_stream:
            raise HTTPException(status_code=404, detail="Stream de vídeo com a resolução desejada não encontrada.")
        
        # Baixa o vídeo (somente o stream de vídeo)
        video_path = os.path.join(CACHE_DIR, f"{yt.video_id}_video.mp4")
        video_stream.download(output_path=CACHE_DIR, filename=f"{yt.video_id}_video.mp4")
        
        # Baixa o stream de áudio (pode ser adaptado para escolher o melhor áudio)
        audio_stream = yt.streams.filter(only_audio=True, mime_type="audio/mp4").first()
        if not audio_stream:
            raise HTTPException(status_code=404, detail="Stream de áudio não encontrado.")
        audio_path = os.path.join(CACHE_DIR, f"{yt.video_id}_audio.mp4")
        audio_stream.download(output_path=CACHE_DIR, filename=f"{yt.video_id}_audio.mp4")
        
        try:
            # Carrega os arquivos com moviepy
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            video_clip.audio = audio_clip
            # Associa o áudio ao vídeo            # Salva o arquivo final
            video_clip.write_videofile(cache_file, codec="libx264", audio_codec="aac")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao processar vídeo: {e}")
        finally:
            # Fecha os clips e remove os arquivos temporários
            video_clip.close()
            audio_clip.close()
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
    elif formato == "audio":
        # Baixa somente o áudio
        audio_stream = yt.streams.filter(only_audio=True, mime_type="audio/mp4").first()
        if not audio_stream:
            raise HTTPException(status_code=404, detail="Stream de áudio não encontrado.")
        # Neste exemplo, o áudio é salvo diretamente no cache
        audio_stream.download(output_path=CACHE_DIR, filename=os.path.basename(cache_file))
    
    return FileResponse(cache_file, media_type='video/mp4', filename=os.path.basename(cache_file))
