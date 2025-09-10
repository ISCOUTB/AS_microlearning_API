from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from hashids import Hashids

# Crear app FastAPI
app = FastAPI()

# Configurar hashids
hashids = Hashids(min_length=8, salt="mi_salt_secreto")

# Montar carpeta de imágenes como estática para el logo
app.mount("/static", StaticFiles(directory="images"), name="static")

# Base de datos de videos
VIDEOS = {
    1: {"archivo": "Videos/Video1.mp4", "likes": 0, "vistas": 0},
    2: {"archivo": "Videos/Video2.mp4", "likes": 0, "vistas": 0},
    3: {"archivo": "Videos/Video3.mp4", "likes": 0, "vistas": 0},
}


# Página principal
@app.get("/", response_class=HTMLResponse)
def pagina_principal():
    # Codificar IDs
    hash_ids = {i: hashids.encode(i) for i in VIDEOS.keys()}

    # Generar bloques HTML dinámicos para cada video
    videos_html = ""
    for i, hash_id in hash_ids.items():
        videos_html += f"""
        <main>
            <video id="videoPlayer{i}" controls>
                <source src="/videos/{hash_id}/archivo" type="video/mp4">
                Tu navegador no soporta video.
            </video>

            <div class="actions">
                <button onclick="darLike('{hash_id}')">❤️</button>
                <button onclick="mostrarEstadisticas('{hash_id}', 'stats{i}')">📊</button>
                <button onclick="mostrarVideo('{hash_id}', 'videoPlayer{i}', 'stats{i}')">🔄</button>
            </div>

            <div id="stats{i}" style="display:none;">
                <p class="view">Vistas Totales: <span id="vistas_{hash_id}"></span></p>
                <p class="like">Likes Totales: <span id="likes_{hash_id}"></span></p>
            </div>
        </main>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Plataforma de Video</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #fafafa;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}

            header {{
                width: 100%;
                background: white;
                border-bottom: 1px solid #dbdbdb;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 10px 0;
                position: sticky;
                top: 0;
                z-index: 1000;
            }}

            .logo {{
                font-size: 22px;
                font-weight: bold;
                color: #262626;
                font-family: 'Arial Rounded MT Bold', Arial, sans-serif;
            }}

            main {{
                margin-top: 20px;
                width: 100%;
                max-width: 700px;
                background: white;
                border: 1px solid #dbdbdb;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                margin-bottom: 40px;
            }}

            video {{
                width: 100%;
                max-height: 500px;   /* limita altura */
                object-fit: contain; /* mantiene proporción original */
                background: black;
                display: block;
            }}

            .actions {{
                padding: 10px;
                display: flex;
                justify-content: space-around;
                align-items: center;
            }}

            button {{
                border: none;
                background: none;
                cursor: pointer;
                font-size: 20px;
                padding: 8px;
                transition: transform 0.2s ease;
            }}

            button:hover {{
                transform: scale(1.2);
            }}

            #statsContainer {{
                padding: 15px;
                border-top: 1px solid #eee;
                text-align: left;
                font-size: 14px;
            }}

            .like {{
                color: #ed4956;
                font-weight: bold;
            }}

            .view {{
                color: #3897f0;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo">VideoApp</div>
            <img src="/static/image.png" alt="Logo" style="height:40px; margin-left:20px;">
        </header>

        {videos_html}

        <script>
            async function mostrarVideo(hashId, playerId, statsId){{
                await fetch(`/videos/${{hashId}}/vistas`, {{method: 'PUT'}});
                document.getElementById(statsId).style.display = 'none';
                const video = document.getElementById(playerId);
                video.pause();
                video.currentTime = 0;
                video.play();
            }}

            async function darLike(hashId){{
                await fetch(`/videos/${{hashId}}/likes`, {{method: 'PUT'}});
                alert('❤️ Like registrado!');
            }}

            async function mostrarEstadisticas(hashId, statsId){{
                const res = await fetch(`/videos/${{hashId}}/estadisticas`);
                const data = await res.json();
                document.getElementById(statsId).style.display = 'block';
                document.getElementById(`vistas_${{hashId}}`).textContent = data.total_vistas;
                document.getElementById(`likes_${{hashId}}`).textContent = data.total_likes;
            }}
        </script>
    </body>
    </html>
    """


# --- Endpoints de la API ---

@app.get("/videos/{hash_id}/archivo")
def servir_video(hash_id: str):
    decoded = hashids.decode(hash_id)
    if not decoded:
        return JSONResponse({"error": "ID inválido"}, status_code=400)
    video_id = decoded[0]

    video = VIDEOS.get(video_id)
    if not video:
        return JSONResponse({"error": "Video no encontrado"}, status_code=404)
    return FileResponse(video["archivo"], media_type="video/mp4")


@app.put("/videos/{hash_id}/vistas")
def registrar_vista(hash_id: str):
    decoded = hashids.decode(hash_id)
    if not decoded:
        return JSONResponse({"error": "ID inválido"}, status_code=400)
    video_id = decoded[0]

    if video_id in VIDEOS:
        VIDEOS[video_id]["vistas"] += 1
        return {"ok": True, "total_vistas": VIDEOS[video_id]["vistas"]}
    return {"error": "Video no encontrado"}


@app.put("/videos/{hash_id}/likes")
def registrar_like(hash_id: str):
    decoded = hashids.decode(hash_id)
    if not decoded:
        return JSONResponse({"error": "ID inválido"}, status_code=400)
    video_id = decoded[0]

    if video_id in VIDEOS:
        VIDEOS[video_id]["likes"] += 1
        return {"ok": True, "total_likes": VIDEOS[video_id]["likes"]}
    return {"error": "Video no encontrado"}


@app.get("/videos/{hash_id}/estadisticas")
def estadisticas(hash_id: str):
    decoded = hashids.decode(hash_id)
    if not decoded:
        return JSONResponse({"error": "ID inválido"}, status_code=400)
    video_id = decoded[0]

    video = VIDEOS.get(video_id)
    if not video:
        return {"error": "Video no encontrado"}
    return {"total_vistas": video["vistas"], "total_likes": video["likes"]}
