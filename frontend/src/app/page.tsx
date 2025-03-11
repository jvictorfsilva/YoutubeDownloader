"use client";
import { useState } from "react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [formato, setFormato] = useState("video");
  const [resolucao, setResolucao] = useState("720p");
  const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL;

  const handleDownload = () => {
    // Monta a URL do endpoint do backend com os parâmetros
    let apiUrl = `${NEXT_PUBLIC_API_URL}/download?url=${encodeURIComponent(
      url
    )}&formato=${formato}`;
    if (formato === "video") {
      apiUrl += `&resolucao=${resolucao}`;
    }
    // Redireciona para o endpoint para iniciar o download
    window.location.href = apiUrl;
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>YouTube Downloader</h1>
      <input
        type="text"
        placeholder="Cole a URL do vídeo"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={{ width: "100%", padding: "0.5rem", marginBottom: "1rem" }}
      />
      <div style={{ marginBottom: "1rem" }}>
        <label>
          <input
            type="radio"
            value="video"
            checked={formato === "video"}
            onChange={() => setFormato("video")}
          />{" "}
          Vídeo
        </label>
        <label style={{ marginLeft: "1rem" }}>
          <input
            type="radio"
            value="audio"
            checked={formato === "audio"}
            onChange={() => setFormato("audio")}
          />{" "}
          Áudio
        </label>
      </div>
      {formato === "video" && (
        <div style={{ marginBottom: "1rem" }}>
          <label>Resolução: </label>
          <select
            value={resolucao}
            onChange={(e) => setResolucao(e.target.value)}
          >
            <option value="144p">144p</option>
            <option value="240p">240p</option>
            <option value="360p">360p</option>
            <option value="480p">480p</option>
            <option value="720p">720p</option>
            <option value="1080p">1080p</option>
            <option value="1440p">1440p</option>
            <option value="2160p">2160p</option>
          </select>
        </div>
      )}
      <button onClick={handleDownload}>Baixar</button>
    </div>
  );
}
