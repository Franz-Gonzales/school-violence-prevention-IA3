export class WebRTCClient {
    constructor(cameraId, videoElement, onDetection, onStatusChange) {
        this.cameraId = cameraId;
        this.videoElement = videoElement;
        this.onDetection = onDetection;
        this.onStatusChange = onStatusChange || (() => {}); // Callback para cambios de estado
        this.clientId = this.generateClientId();
        this.pc = null;
        this.ws = null;
        this.detectionActive = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.connectionState = 'disconnected';
        
        // Métricas de rendimiento
        this.stats = {
            frameRate: 0,
            bandwidth: 0,
            packetsLost: 0,
            timestamp: Date.now(),
            totalFrames: 0,
            droppedFrames: 0
        };
        
        // Monitoreo de calidad
        this.qualityMonitor = null;
        this.lastStatsTime = 0;
        
        // Estados detallados
        this.states = {
            websocket: 'disconnected',    // disconnected, connecting, connected, error
            webrtc: 'disconnected',       // disconnected, connecting, connected, failed
            video: 'loading',             // loading, playing, stalled, error
            detection: 'inactive'         // inactive, starting, active, stopping
        };
        
        // Configurar video element
        this.setupVideoElement();
        
        // Iniciar monitoreo de estadísticas
        this.startStatsMonitoring();
    }

    generateClientId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // Notificar cambios de estado
    notifyStateChange(type, newState, details = {}) {
        this.states[type] = newState;
        console.log(`🔄 Estado ${type}: ${newState}`, details);
        
        this.onStatusChange({
            type,
            state: newState,
            details,
            timestamp: new Date(),
            clientId: this.clientId
        });
    }

    setupVideoElement() {
        if (!this.videoElement) {return;}

        // Configurar propiedades del video para mejor rendimiento
        this.videoElement.playsInline = true;
        this.videoElement.muted = true;
        this.videoElement.autoplay = true;
        this.videoElement.controls = false;
        
        // Configurar estilo para mantener aspect ratio
        this.videoElement.style.objectFit = 'cover';
        this.videoElement.style.width = '100%';
        this.videoElement.style.height = '100%';
        
        // Event listeners mejorados para monitoreo
        this.videoElement.addEventListener('loadstart', () => {
            this.notifyStateChange('video', 'loading', { message: 'Iniciando carga de video' });
        });

        this.videoElement.addEventListener('loadedmetadata', () => {
            const { videoWidth, videoHeight } = this.videoElement;
            this.notifyStateChange('video', 'loaded', { 
                resolution: `${videoWidth}x${videoHeight}`,
                message: `Video cargado: ${videoWidth}x${videoHeight}`
            });
        });

        this.videoElement.addEventListener('canplay', () => {
            this.notifyStateChange('video', 'ready', { message: 'Video listo para reproducir' });
        });

        this.videoElement.addEventListener('playing', () => {
            this.notifyStateChange('video', 'playing', { message: 'Video reproduciéndose' });
            this.startQualityMonitoring();
        });

        this.videoElement.addEventListener('pause', () => {
            this.notifyStateChange('video', 'paused', { message: 'Video pausado' });
            this.stopQualityMonitoring();
        });

        this.videoElement.addEventListener('stalled', () => {
            this.notifyStateChange('video', 'stalled', { 
                message: 'Video pausado - problemas de red',
                severity: 'warning'
            });
        });

        this.videoElement.addEventListener('waiting', () => {
            this.notifyStateChange('video', 'buffering', { 
                message: 'Video esperando datos',
                severity: 'warning'
            });
        });

        this.videoElement.addEventListener('error', (e) => {
            this.notifyStateChange('video', 'error', { 
                message: 'Error en la reproducción del video',
                error: e.target.error,
                severity: 'error'
            });
        });

        // Monitoreo de calidad de video
        this.videoElement.addEventListener('progress', () => {
            if (this.videoElement.buffered.length > 0) {
                const buffered = this.videoElement.buffered.end(0);
                const current = this.videoElement.currentTime;
                const bufferHealth = Math.max(0, buffered - current);
                
                if (bufferHealth < 1) { // Menos de 1 segundo en buffer
                    this.notifyStateChange('video', 'low_buffer', {
                        bufferHealth,
                        message: `Buffer bajo: ${bufferHealth.toFixed(1)}s`,
                        severity: 'warning'
                    });
                }
            }
        });
    }

    startQualityMonitoring() {
        this.qualityMonitor = setInterval(() => {
            this.updateVideoStats();
        }, 2000); // Cada 2 segundos
    }

    stopQualityMonitoring() {
        if (this.qualityMonitor) {
            clearInterval(this.qualityMonitor);
            this.qualityMonitor = null;
        }
    }

    updateVideoStats() {
        if (!this.videoElement || !this.pc) {return;}

        // Obtener estadísticas de WebRTC
        this.pc.getStats().then(stats => {
            let inboundRtp = null;
            let remoteInboundRtp = null;

            stats.forEach(report => {
                if (report.type === 'inbound-rtp' && report.mediaType === 'video') {
                    inboundRtp = report;
                } else if (report.type === 'remote-inbound-rtp' && report.mediaType === 'video') {
                    remoteInboundRtp = report;
                }
            });

            if (inboundRtp) {
                const now = Date.now();
                const timeDiff = (now - this.lastStatsTime) / 1000;
                
                if (this.lastStatsTime > 0 && timeDiff > 0) {
                    // Calcular FPS
                    const framesDiff = inboundRtp.framesReceived - (this.stats.lastFramesReceived || 0);
                    this.stats.frameRate = Math.round(framesDiff / timeDiff);
                    
                    // Calcular bandwidth
                    const bytesDiff = inboundRtp.bytesReceived - (this.stats.lastBytesReceived || 0);
                    this.stats.bandwidth = Math.round((bytesDiff * 8) / (timeDiff * 1024)); // kbps
                    
                    // Frames perdidos
                    this.stats.packetsLost = inboundRtp.packetsLost || 0;
                    this.stats.totalFrames = inboundRtp.framesReceived || 0;
                }
                
                this.stats.lastFramesReceived = inboundRtp.framesReceived;
                this.stats.lastBytesReceived = inboundRtp.bytesReceived;
                this.lastStatsTime = now;

                // Notificar estadísticas
                this.onStatusChange({
                    type: 'stats',
                    state: 'updated',
                    details: { ...this.stats },
                    timestamp: new Date()
                });
            }
        }).catch(error => {
            console.warn('Error obteniendo estadísticas WebRTC:', error);
        });

        // Obtener calidad de video del elemento
        if (this.videoElement.getVideoPlaybackQuality) {
            const quality = this.videoElement.getVideoPlaybackQuality();
            const currentDropped = quality.droppedVideoFrames;
            const currentTotal = quality.totalVideoFrames;
            
            if (currentDropped > this.stats.droppedFrames) {
                const newDropped = currentDropped - this.stats.droppedFrames;
                this.notifyStateChange('video', 'frames_dropped', {
                    framesDropped: newDropped,
                    totalDropped: currentDropped,
                    dropRate: ((currentDropped / currentTotal) * 100).toFixed(2),
                    message: `${newDropped} frames perdidos`,
                    severity: 'warning'
                });
            }
            
            this.stats.droppedFrames = currentDropped;
            this.stats.totalFrames = currentTotal;
        }
    }

    startStatsMonitoring() {
        // Monitoreo general cada 5 segundos
        this.statsInterval = setInterval(() => {
            this.onStatusChange({
                type: 'heartbeat',
                state: 'active',
                details: {
                    connectionState: this.connectionState,
                    detectionActive: this.detectionActive,
                    states: { ...this.states },
                    uptime: Date.now() - this.stats.timestamp
                },
                timestamp: new Date()
            });
        }, 5000);
    }

    async connect(detectionActive = false) {
        try {
            this.connectionState = 'connecting';
            this.notifyStateChange('websocket', 'connecting', { message: 'Conectando WebSocket...' });
            
            const wsUrl = `ws://localhost:8000/ws/rtc/${this.clientId}/${this.cameraId}`;
            console.log(`🔌 Conectando a WebSocket: ${wsUrl}`);
            
            this.ws = new WebSocket(wsUrl);

            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    this.notifyStateChange('websocket', 'error', { 
                        message: 'Timeout en conexión WebSocket',
                        severity: 'error'
                    });
                    reject(new Error('WebSocket connection timeout'));
                }, 10000);

                this.ws.onopen = () => {
                    clearTimeout(timeout);
                    console.log('✅ WebSocket conectado exitosamente');
                    this.connectionState = 'connected';
                    this.reconnectAttempts = 0;
                    this.notifyStateChange('websocket', 'connected', { 
                        message: 'WebSocket conectado exitosamente' 
                    });
                    this.startWebRTC(detectionActive);
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('❌ Error parsing WebSocket message:', error);
                        this.notifyStateChange('websocket', 'error', {
                            message: 'Error procesando mensaje del servidor',
                            error: error.message,
                            severity: 'error'
                        });
                    }
                };

                this.ws.onclose = (event) => {
                    clearTimeout(timeout);
                    console.log(`🔌 WebSocket cerrado: ${event.code} ${event.reason}`);
                    this.connectionState = 'disconnected';
                    this.notifyStateChange('websocket', 'disconnected', {
                        code: event.code,
                        reason: event.reason,
                        wasClean: event.wasClean,
                        message: `Conexión cerrada: ${event.reason}`
                    });
                    
                    // Auto-reconnect logic
                    if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.reconnectAttempts++;
                        const delay = 2000 * this.reconnectAttempts;
                        
                        this.notifyStateChange('websocket', 'reconnecting', {
                            attempt: this.reconnectAttempts,
                            maxAttempts: this.maxReconnectAttempts,
                            delay: delay / 1000,
                            message: `Reintentando conexión ${this.reconnectAttempts}/${this.maxReconnectAttempts} en ${delay/1000}s`
                        });
                        
                        setTimeout(() => {
                            this.connect(this.detectionActive);
                        }, delay);
                    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                        this.notifyStateChange('websocket', 'failed', {
                            message: 'Máximo número de reintentos alcanzado',
                            severity: 'error'
                        });
                        this.cleanup();
                    }
                };

                this.ws.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('❌ WebSocket error:', error);
                    this.connectionState = 'error';
                    this.notifyStateChange('websocket', 'error', {
                        message: 'Error en la conexión WebSocket',
                        error,
                        severity: 'error'
                    });
                    reject(error);
                };
            });
        } catch (error) {
            console.error('❌ Error connecting WebSocket:', error);
            this.connectionState = 'error';
            this.notifyStateChange('websocket', 'error', {
                message: 'Error iniciando conexión WebSocket',
                error: error.message,
                severity: 'error'
            });
            throw error;
        }
    }

    async startWebRTC(detectionActive = false) {
        try {
            this.notifyStateChange('webrtc', 'connecting', { 
                message: 'Estableciendo conexión WebRTC...' 
            });

            this.pc = new RTCPeerConnection({
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' }
                ],
                iceTransportPolicy: 'all',
                iceCandidatePoolSize: 10
            });

            // Configurar manejo de tracks con mejor control
            this.pc.ontrack = (event) => {
                console.log('📹 Track recibido:', event.track.kind);
                if (event.track.kind === 'video' && event.streams[0]) {
                    console.log('📹 Configurando video source');
                    this.videoElement.srcObject = event.streams[0];
                    
                    this.notifyStateChange('webrtc', 'track_received', {
                        trackKind: event.track.kind,
                        streamId: event.streams[0].id,
                        message: 'Stream de video recibido'
                    });
                    
                    // Forzar reproducción
                    this.videoElement.play().catch(error => {
                        console.error('❌ Error playing video:', error);
                        this.notifyStateChange('video', 'error', {
                            message: 'Error iniciando reproducción',
                            error: error.message,
                            severity: 'error'
                        });
                    });
                }
            };

            this.pc.onicecandidate = (event) => {
                if (event.candidate) {
                    this.sendMessage({
                        tipo: 'ice_candidate',
                        candidate: event.candidate,
                        destino_id: this.clientId
                    });
                }
            };

            this.pc.onconnectionstatechange = () => {
                const state = this.pc.connectionState;
                console.log('🔗 RTC Connection state:', state);
                this.connectionState = state;
                
                const stateMessages = {
                    'connecting': 'Estableciendo conexión WebRTC...',
                    'connected': 'Conexión WebRTC establecida exitosamente',
                    'disconnected': 'Conexión WebRTC desconectada',
                    'failed': 'Falló la conexión WebRTC',
                    'closed': 'Conexión WebRTC cerrada'
                };
                
                this.notifyStateChange('webrtc', state, {
                    message: stateMessages[state] || `Estado WebRTC: ${state}`
                });
                
                if (state === 'connected') {
                    this.reconnectAttempts = 0;
                } else if (state === 'failed') {
                    this.handleConnectionFailure();
                }
            };

            this.pc.oniceconnectionstatechange = () => {
                const state = this.pc.iceConnectionState;
                console.log('🧊 ICE connection state:', state);
                
                if (state === 'failed') {
                    this.notifyStateChange('webrtc', 'ice_failed', {
                        message: 'Falló la conexión ICE',
                        severity: 'error'
                    });
                    this.handleConnectionFailure();
                } else if (state === 'disconnected') {
                    this.notifyStateChange('webrtc', 'ice_disconnected', {
                        message: 'Conexión ICE desconectada',
                        severity: 'warning'
                    });
                }
            };

            // Crear offer con configuración optimizada
            const offer = await this.pc.createOffer({
                offerToReceiveVideo: true,
                offerToReceiveAudio: false,
                voiceActivityDetection: false
            });

            await this.pc.setLocalDescription(offer);

            // Enviar offer con estado de detección
            this.sendMessage({
                tipo: 'offer',
                sdp: this.pc.localDescription.sdp,
                destino_id: this.clientId,
                deteccion_activada: detectionActive,
                camara_id: this.cameraId
            });

            console.log('📤 WebRTC offer enviado');

        } catch (error) {
            console.error('❌ Error in startWebRTC:', error);
            this.notifyStateChange('webrtc', 'error', {
                message: 'Error estableciendo conexión WebRTC',
                error: error.message,
                severity: 'error'
            });
            this.cleanup();
            throw error;
        }
    }

    async handleMessage(message) {
        try {
            console.log('📨 Mensaje recibido:', message.tipo);

            switch (message.tipo) {
                case 'answer':
                    if (!message.sdp) {
                        console.error('❌ Answer message missing SDP:', message);
                        this.notifyStateChange('webrtc', 'error', {
                            message: 'Respuesta del servidor sin SDP',
                            severity: 'error'
                        });
                        return;
                    }
                    
                    console.log('📥 Procesando SDP answer');
                    await this.pc.setRemoteDescription(new RTCSessionDescription({
                        type: 'answer',
                        sdp: message.sdp
                    }));
                    
                    this.notifyStateChange('webrtc', 'answer_processed', {
                        message: 'Respuesta SDP procesada exitosamente'
                    });
                    break;

                case 'ice_candidate':
                    if (message.candidate) {
                        await this.pc.addIceCandidate(new RTCIceCandidate(message.candidate));
                        console.log('🧊 ICE candidate agregado');
                    }
                    break;

                case 'deteccion_violencia':
                    console.log('🚨 Detección de violencia:', message);
                    this.notifyStateChange('detection', 'violence_detected', {
                        probability: message.probabilidad,
                        peopleCount: message.personas_detectadas,
                        message: `Violencia detectada: ${(message.probabilidad * 100).toFixed(1)}%`,
                        severity: 'critical'
                    });
                    
                    if (this.onDetection) {
                        this.onDetection({
                            violencia_detectada: true,
                            probabilidad: message.probabilidad || 0,
                            personas_detectadas: message.personas_detectadas || 0,
                            mensaje: message.mensaje || 'Violencia detectada',
                            timestamp: new Date()
                        });
                    }
                    break;

                case 'deteccion_estado':
                    const detectionState = message.estado === 'activa' ? 'active' : 'inactive';
                    console.log('🔍 Estado de detección:', detectionState);
                    this.detectionActive = message.estado === 'activa';
                    this.notifyStateChange('detection', detectionState, {
                        message: `Detección ${detectionState === 'active' ? 'activada' : 'desactivada'}`
                    });
                    break;

                case 'error':
                    console.error('❌ Error del servidor:', message.mensaje);
                    this.notifyStateChange('websocket', 'server_error', {
                        message: `Error del servidor: ${message.mensaje}`,
                        severity: 'error'
                    });
                    break;

                default:
                    console.warn('⚠️ Tipo de mensaje desconocido:', message.tipo);
                    this.notifyStateChange('websocket', 'unknown_message', {
                        messageType: message.tipo,
                        message: `Mensaje desconocido: ${message.tipo}`,
                        severity: 'warning'
                    });
            }
        } catch (error) {
            console.error('❌ Error processing message:', error, message);
            this.notifyStateChange('websocket', 'message_error', {
                message: 'Error procesando mensaje del servidor',
                error: error.message,
                originalMessage: message,
                severity: 'error'
            });
        }
    }

    handleConnectionFailure() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = 3000 * this.reconnectAttempts;
            
            this.notifyStateChange('webrtc', 'reconnecting', {
                attempt: this.reconnectAttempts,
                maxAttempts: this.maxReconnectAttempts,
                delay: delay / 1000,
                message: `Reintentando conexión WebRTC ${this.reconnectAttempts}/${this.maxReconnectAttempts} en ${delay/1000}s`
            });
            
            setTimeout(async () => {
                try {
                    this.cleanup();
                    await this.connect(this.detectionActive);
                } catch (error) {
                    console.error('❌ Reconnection failed:', error);
                    this.notifyStateChange('webrtc', 'reconnect_failed', {
                        message: 'Falló el reintento de conexión',
                        error: error.message,
                        severity: 'error'
                    });
                }
            }, delay);
        } else {
            console.error('❌ Max reconnection attempts reached');
            this.notifyStateChange('webrtc', 'failed', {
                message: 'Máximo número de reintentos WebRTC alcanzado',
                severity: 'error'
            });
            this.cleanup();
        }
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                console.log('📤 Mensaje enviado:', message.tipo);
            } catch (error) {
                console.error('❌ Error sending message:', error);
                this.notifyStateChange('websocket', 'send_error', {
                    message: 'Error enviando mensaje',
                    error: error.message,
                    messageType: message.tipo,
                    severity: 'error'
                });
            }
        } else {
            console.error('❌ WebSocket not ready to send message:', message.tipo);
            this.notifyStateChange('websocket', 'not_ready', {
                message: 'WebSocket no está listo para enviar mensajes',
                messageType: message.tipo,
                readyState: this.ws?.readyState,
                severity: 'warning'
            });
        }
    }

    toggleDetection(enable) {
        const previousState = this.detectionActive;
        this.detectionActive = enable;
        const messageType = enable ? 'iniciar_deteccion' : 'detener_deteccion';
        
        this.notifyStateChange('detection', enable ? 'starting' : 'stopping', {
            message: `${enable ? 'Iniciando' : 'Deteniendo'} detección...`
        });

        console.log(`🔍 ${enable ? 'Iniciando' : 'Deteniendo'} detección`);

        this.sendMessage({
            tipo: messageType,
            camara_id: this.cameraId,
            cliente_id: this.clientId,
            deteccion_activada: enable
        });

        // Si falla el envío, revertir estado
        setTimeout(() => {
            if (this.states.detection === 'starting' || this.states.detection === 'stopping') {
                this.detectionActive = previousState;
                this.notifyStateChange('detection', 'error', {
                    message: 'Timeout cambiando estado de detección',
                    severity: 'warning'
                });
            }
        }, 5000);
    }

    getConnectionStats() {
        return {
            connectionState: this.connectionState,
            detectionActive: this.detectionActive,
            reconnectAttempts: this.reconnectAttempts,
            states: { ...this.states },
            stats: { ...this.stats },
            uptime: Date.now() - this.stats.timestamp
        };
    }

    cleanup() {
        console.log('🧹 Limpiando recursos WebRTC...');
        
        // Stop quality monitoring
        this.stopQualityMonitoring();
        
        // Stop stats monitoring
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
            this.statsInterval = null;
        }
        
        // Close peer connection
        if (this.pc) {
            this.pc.close();
            this.pc = null;
        }
        
        // Close WebSocket
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        // Clear video
        if (this.videoElement) {
            if (this.videoElement.srcObject) {
                const tracks = this.videoElement.srcObject.getTracks();
                tracks.forEach(track => track.stop());
            }
            this.videoElement.srcObject = null;
        }
        
        // Reset state
        this.connectionState = 'disconnected';
        this.detectionActive = false;
        this.reconnectAttempts = 0;
        
        // Reset all states
        Object.keys(this.states).forEach(key => {
            this.states[key] = key === 'video' ? 'loading' : 'disconnected';
        });
        
        this.notifyStateChange('system', 'cleanup_complete', {
            message: 'Recursos WebRTC liberados completamente'
        });
        
        console.log('✅ Cleanup completado');
    }

    stop() {
        console.log('🛑 Deteniendo cliente WebRTC...');
        this.notifyStateChange('system', 'stopping', {
            message: 'Deteniendo cliente WebRTC...'
        });
        
        this.toggleDetection(false);
        this.cleanup();
        
        this.notifyStateChange('system', 'stopped', {
            message: 'Cliente WebRTC detenido completamente'
        });
    }
}

export default WebRTCClient;