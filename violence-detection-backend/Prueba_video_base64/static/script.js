class VideoRecorderApp {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadVideos();
    }

    bindEvents() {
        document.getElementById('recordBtn').addEventListener('click', () => this.recordVideo());
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadVideos());
        document.getElementById('closePlayer').addEventListener('click', () => this.closePlayer());
    }

    showStatus(message, type = 'success') {
        const statusDiv = document.getElementById('status');
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        statusDiv.style.display = 'block';
        
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }
    }

    async recordVideo() {
        const recordBtn = document.getElementById('recordBtn');
        const originalText = recordBtn.textContent;
        
        try {
            recordBtn.textContent = '🎬 Grabando...';
            recordBtn.disabled = true;
            
            this.showStatus('Iniciando grabación... Sigue las instrucciones en la ventana de la cámara.', 'loading');
            
            const response = await fetch('/record-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            
            const result = await response.json();
            
            this.showStatus(`¡Video grabado exitosamente! Archivo: ${result.filename}`, 'success');
            this.loadVideos(); // Recargar la lista
            
        } catch (error) {
            console.error('Error grabando video:', error);
            this.showStatus(`Error grabando video: ${error.message}`, 'error');
        } finally {
            recordBtn.textContent = originalText;
            recordBtn.disabled = false;
        }
    }

    async loadVideos() {
        try {
            const response = await fetch('/videos');
            if (!response.ok) {
                throw new Error('Error cargando videos');
            }
            
            const videos = await response.json();
            this.displayVideos(videos);
            
        } catch (error) {
            console.error('Error cargando videos:', error);
            this.showStatus('Error cargando videos', 'error');
        }
    }

    displayVideos(videos) {
        const videoList = document.getElementById('videoList');
        
        if (videos.length === 0) {
            videoList.innerHTML = '<div class="empty-state">No hay videos grabados aún. ¡Graba tu primer video!</div>';
            return;
        }
        
        videoList.innerHTML = videos.map(video => `
            <div class="video-item">
                <div class="video-info">
                    <h4>📹 ${video.filename}</h4>
                    <p><strong>Fecha:</strong> ${new Date(video.created_at).toLocaleString()}</p>
                    <p><strong>Duración:</strong> ${video.duration.toFixed(1)} segundos</p>
                    <p><strong>Tamaño:</strong> ${this.formatFileSize(video.file_size)}</p>
                </div>
                <div class="video-actions">
                    <button class="btn btn-primary" onclick="app.playVideo(${video.id})">
                        ▶️ Reproducir
                    </button>
                    <button class="btn btn-danger" onclick="app.deleteVideo(${video.id})">
                        🗑️ Eliminar
                    </button>
                </div>
            </div>
        `).join('');
    }

    async playVideo(videoId) {
        try {
            this.showStatus('Cargando video...', 'loading');
            
            const response = await fetch(`/videos/${videoId}`);
            if (!response.ok) {
                throw new Error('Error cargando video');
            }
            
            const video = await response.json();
            console.log('Video data received:', {
                id: video.id,
                filename: video.filename,
                base64_length: video.video_base64?.length || 0,
                base64_preview: video.video_base64?.substring(0, 50) + '...'
            });
            
            if (!video.video_base64 || video.video_base64.length === 0) {
                throw new Error('El video no tiene datos Base64');
            }
            
            // USAR SIEMPRE MP4 YA QUE TODOS LOS VIDEOS SE CONVIERTEN
            const mimeType = 'video/mp4';
            console.log('MIME type:', mimeType);
            
            // Crear data URL para el video
            const dataUrl = `data:${mimeType};base64,${video.video_base64}`;
            
            // Mostrar el reproductor
            const videoPlayer = document.getElementById('videoPlayer');
            const videoElement = document.getElementById('videoElement');
            
            // Limpiar reproductor anterior
            videoElement.src = '';
            videoElement.load();
            
            // Establecer nueva fuente
            videoElement.src = dataUrl;
            videoPlayer.style.display = 'block';
            
            // Agregar event listeners mejorados
            videoElement.onloadstart = () => {
                console.log('Video load started');
                this.showStatus('Cargando video...', 'loading');
            };
            
            videoElement.onloadeddata = () => {
                console.log('Video data loaded');
                this.showStatus('Video cargado', 'success');
            };
            
            videoElement.oncanplay = () => {
                console.log('Video can play');
                this.showStatus(`Listo para reproducir: ${video.filename}`, 'success');
            };
            
            videoElement.onerror = (e) => {
                console.error('Video error:', e);
                console.error('Video element error details:', {
                    error: videoElement.error,
                    networkState: videoElement.networkState,
                    readyState: videoElement.readyState
                });
                this.showStatus('Error: El video no se puede reproducir. Codec no compatible.', 'error');
            };
            
            // Scroll al reproductor
            videoPlayer.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error reproduciendo video:', error);
            this.showStatus(`Error cargando video: ${error.message}`, 'error');
        }
    }

    closePlayer() {
        const videoPlayer = document.getElementById('videoPlayer');
        const videoElement = document.getElementById('videoElement');
        
        videoElement.src = '';
        videoPlayer.style.display = 'none';
    }

    async deleteVideo(videoId) {
        if (!confirm('¿Estás seguro de que quieres eliminar este video?')) {
            return;
        }
        
        try {
            const response = await fetch(`/videos/${videoId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Error eliminando video');
            }
            
            this.showStatus('Video eliminado exitosamente', 'success');
            this.loadVideos(); // Recargar la lista
            
        } catch (error) {
            console.error('Error eliminando video:', error);
            this.showStatus('Error eliminando video', 'error');
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Inicializar la aplicación
const app = new VideoRecorderApp();