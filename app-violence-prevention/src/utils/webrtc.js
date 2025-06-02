export class WebRTCClient {
    constructor(cameraId, videoElement, onDetection) {
        this.cameraId = cameraId;
        this.videoElement = videoElement;
        this.onDetection = onDetection;
        this.clientId = this.generateClientId();
        this.pc = null;
        this.ws = null;
        this.detectionActive = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.connectionState = 'disconnected';
        
        // Control de video mejorado
        this.lastFrameTime = 0;
        this.frameCount = 0;
        this.droppedFrames = 0;
        
        // Configurar video element
        this.setupVideoElement();
    }

    generateClientId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    setupVideoElement() {
        if (!this.videoElement){ return;}

        // Configurar propiedades del video para mejor rendimiento
        this.videoElement.playsInline = true;
        this.videoElement.muted = true;
        this.videoElement.autoplay = true;
        this.videoElement.controls = false;
        
        // Configurar estilo para mantener aspect ratio
        this.videoElement.style.objectFit = 'cover';
        this.videoElement.style.width = '100%';
        this.videoElement.style.height = '100%';
        
        // Event listeners para monitoreo
        this.videoElement.addEventListener('loadedmetadata', () => {
            console.log(`Video metadata loaded: ${this.videoElement.videoWidth}x${this.videoElement.videoHeight}`);
        });

        this.videoElement.addEventListener('resize', () => {
            console.log(`Video resized: ${this.videoElement.videoWidth}x${this.videoElement.videoHeight}`);
        });

        this.videoElement.addEventListener('stalled', () => {
            console.warn('Video stalled - connection issues?');
        });

        this.videoElement.addEventListener('waiting', () => {
            console.warn('Video waiting for data');
        });

        this.videoElement.addEventListener('canplay', () => {
            console.log('Video ready to play');
        });

        this.videoElement.addEventListener('playing', () => {
            console.log('Video playing');
            this.startFrameMonitoring();
        });

        this.videoElement.addEventListener('pause', () => {
            console.log('Video paused');
            this.stopFrameMonitoring();
        });
    }

    startFrameMonitoring() {
        // Monitorear frames para detectar problemas de rendimiento
        this.frameMonitoringInterval = setInterval(() => {
            if (this.videoElement && this.videoElement.getVideoPlaybackQuality) {
                const quality = this.videoElement.getVideoPlaybackQuality();
                const currentDropped = quality.droppedVideoFrames;
                const currentTotal = quality.totalVideoFrames;
                
                if (currentDropped > this.droppedFrames) {
                    console.warn(`Frames dropped: ${currentDropped - this.droppedFrames}`);
                    this.droppedFrames = currentDropped;
                }
                
                // Log quality periodically
                if (currentTotal % 150 === 0 && currentTotal > 0) { // Every ~10 seconds at 15fps
                    const dropRate = (currentDropped / currentTotal * 100).toFixed(2);
                    console.log(`Video quality: ${currentTotal} frames, ${currentDropped} dropped (${dropRate}%)`);
                }
            }
        }, 2000); // Check every 2 seconds
    }

    stopFrameMonitoring() {
        if (this.frameMonitoringInterval) {
            clearInterval(this.frameMonitoringInterval);
            this.frameMonitoringInterval = null;
        }
    }

    async connect(detectionActive = false) {
        try {
            this.connectionState = 'connecting';
            const wsUrl = `ws://localhost:8000/ws/rtc/${this.clientId}/${this.cameraId}`;
            
            console.log(`Connecting to WebSocket: ${wsUrl}`);
            this.ws = new WebSocket(wsUrl);

            // Promise para manejar la conexión
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('WebSocket connection timeout'));
                }, 10000); // 10 second timeout

                this.ws.onopen = () => {
                    clearTimeout(timeout);
                    console.log('WebSocket connected successfully');
                    this.connectionState = 'connected';
                    this.reconnectAttempts = 0;
                    this.startWebRTC(detectionActive);
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };

                this.ws.onclose = (event) => {
                    clearTimeout(timeout);
                    console.log(`WebSocket closed: ${event.code} ${event.reason}`);
                    this.connectionState = 'disconnected';
                    
                    // Auto-reconnect logic
                    if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.reconnectAttempts++;
                        console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                        setTimeout(() => {
                            this.connect(this.detectionActive);
                        }, 2000 * this.reconnectAttempts); // Exponential backoff
                    } else {
                        this.cleanup();
                    }
                };

                this.ws.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('WebSocket error:', error);
                    this.connectionState = 'error';
                    reject(error);
                };
            });
        } catch (error) {
            console.error('Error connecting WebSocket:', error);
            this.connectionState = 'error';
            throw error;
        }
    }

    async startWebRTC(detectionActive = false) {
        try {
            this.pc = new RTCPeerConnection({
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' } // Backup STUN server
                ],
                iceTransportPolicy: 'all',
                iceCandidatePoolSize: 10
            });

            // Configurar manejo de tracks con mejor control
            this.pc.ontrack = (event) => {
                console.log('Track received:', event.track.kind);
                if (event.track.kind === 'video' && event.streams[0]) {
                    console.log('Setting video source');
                    this.videoElement.srcObject = event.streams[0];
                    
                    // Forzar reproducción
                    this.videoElement.play().catch(error => {
                        console.error('Error playing video:', error);
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
                console.log('RTC Connection state:', this.pc.connectionState);
                this.connectionState = this.pc.connectionState;
                
                if (this.pc.connectionState === 'connected') {
                    console.log('✅ WebRTC connection established');
                    this.reconnectAttempts = 0;
                } else if (this.pc.connectionState === 'failed') {
                    console.error('❌ WebRTC connection failed');
                    this.handleConnectionFailure();
                } else if (this.pc.connectionState === 'disconnected') {
                    console.warn('⚠️ WebRTC disconnected');
                }
            };

            this.pc.oniceconnectionstatechange = () => {
                console.log('ICE connection state:', this.pc.iceConnectionState);
                
                if (this.pc.iceConnectionState === 'failed') {
                    console.error('ICE connection failed');
                    this.handleConnectionFailure();
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

            console.log('WebRTC offer sent');

        } catch (error) {
            console.error('Error in startWebRTC:', error);
            this.cleanup();
            throw error;
        }
    }

    async handleMessage(message) {
        try {
            console.log('Message received:', message.tipo);

            switch (message.tipo) {
                case 'answer':
                    if (!message.sdp) {
                        console.error('Answer message missing SDP:', message);
                        return;
                    }
                    
                    console.log('Processing SDP answer');
                    await this.pc.setRemoteDescription(new RTCSessionDescription({
                        type: 'answer',
                        sdp: message.sdp
                    }));
                    console.log('✅ SDP answer processed successfully');
                    break;

                case 'ice_candidate':
                    if (message.candidate) {
                        await this.pc.addIceCandidate(new RTCIceCandidate(message.candidate));
                        console.log('ICE candidate added');
                    }
                    break;

                case 'deteccion_violencia':
                    console.log('🚨 Violence detection:', message);
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
                    console.log('Detection state:', message.estado);
                    this.detectionActive = message.estado === 'activa';
                    break;

                case 'error':
                    console.error('Server error:', message.mensaje);
                    break;

                default:
                    console.warn('Unknown message type:', message.tipo);
            }
        } catch (error) {
            console.error('Error processing message:', error, message);
        }
    }

    handleConnectionFailure() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting WebRTC reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(async () => {
                try {
                    this.cleanup();
                    await this.connect(this.detectionActive);
                } catch (error) {
                    console.error('Reconnection failed:', error);
                }
            }, 3000 * this.reconnectAttempts); // Exponential backoff
        } else {
            console.error('Max reconnection attempts reached');
            this.cleanup();
        }
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                console.log('Message sent:', message.tipo);
            } catch (error) {
                console.error('Error sending message:', error);
            }
        } else {
            console.error('WebSocket not ready to send message:', message.tipo);
        }
    }

    toggleDetection(enable) {
        this.detectionActive = enable;
        const messageType = enable ? 'iniciar_deteccion' : 'detener_deteccion';
        
        console.log(`${enable ? 'Starting' : 'Stopping'} detection`);

        this.sendMessage({
            tipo: messageType,
            camara_id: this.cameraId,
            cliente_id: this.clientId,
            deteccion_activada: enable
        });
    }

    getConnectionStats() {
        return {
            connectionState: this.connectionState,
            detectionActive: this.detectionActive,
            reconnectAttempts: this.reconnectAttempts,
            frameCount: this.frameCount,
            droppedFrames: this.droppedFrames
        };
    }

    cleanup() {
        console.log('Cleaning up WebRTC resources...');
        
        // Stop frame monitoring
        this.stopFrameMonitoring();
        
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
        
        console.log('✅ Cleanup completed');
    }

    stop() {
        console.log('Stopping WebRTC client...');
        this.toggleDetection(false);
        this.cleanup();
    }
}

export default WebRTCClient;