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
        this.maxReconnectAttempts = 3;  // Máximo de intentos de reconexión
    }

    generateClientId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    async connect(detectionActive = false) {
        const wsUrl = `ws://localhost:8000/ws/rtc/${this.clientId}/${this.cameraId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket conectado');
            this.startWebRTC(detectionActive);
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log('Mensaje recibido en frontend:', message);
            this.handleMessage(message);
        };

        this.ws.onclose = () => {
            console.log('WebSocket desconectado');
            this.cleanup();
        };

        this.ws.onerror = (error) => {
            console.error('Error en WebSocket:', error);
        };
    }

    async startWebRTC(detectionActive = false) {
        try {
            this.pc = new RTCPeerConnection({
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' }
                ]
            });

            // Mejorar manejo de eventos
            this.pc.ontrack = (event) => {
                if (event.track.kind === 'video') {
                    this.videoElement.srcObject = event.streams[0];
                    console.log('Track de video recibido');
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
                console.log('Estado de conexión WebRTC:', this.pc.connectionState);
                if (this.pc.connectionState === 'failed') {
                    console.error('Conexión WebRTC fallida');
                    if (this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.reconnectAttempts++;
                        console.log(`Intento de reconexión ${this.reconnectAttempts}...`);
                        this.cleanup();
                        setTimeout(() => this.connect(this.detectionActive), 2000);
                    } else {
                        this.cleanup();
                    }
                }
            };

            const offer = await this.pc.createOffer({
                offerToReceiveVideo: true,
                offerToReceiveAudio: false
            });

            await this.pc.setLocalDescription(offer);

            // Enviar oferta con estado de detección
            this.sendMessage({
                tipo: 'offer',
                sdp: this.pc.localDescription.sdp,
                destino_id: this.clientId,
                deteccion_activada: detectionActive,
                camara_id: this.cameraId
            });

        } catch (error) {
            console.error('Error en startWebRTC:', error);
            this.cleanup();
            throw error;
        }
    }

    async handleMessage(message) {
        try {
            console.log('Mensaje recibido:', message);

            switch (message.tipo) {
                case 'answer':
                    if (!message.sdp) {
                        console.error('Mensaje answer no contiene SDP:', message);
                        return;
                    }
                    await this.pc.setRemoteDescription(new RTCSessionDescription({
                        type: 'answer',
                        sdp: message.sdp
                    }));
                    console.log('Respuesta SDP procesada');
                    break;

                case 'ice_candidate':
                    await this.pc.addIceCandidate(new RTCIceCandidate(message.candidate));
                    break;

                case 'deteccion_violencia':
                    console.log('Detección de violencia:', message);
                    if (this.onDetection) {
                        this.onDetection(message);
                    }
                    break;

                case 'deteccion_estado':
                    console.log('Estado de detección:', message);
                    this.detectionActive = message.estado === 'activa';
                    break;

                default:
                    console.warn('Tipo de mensaje desconocido:', message.tipo);
            }
        } catch (error) {
            console.error('Error procesando mensaje:', error, message);
        }
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('Enviando mensaje:', message);
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket no está abierto para enviar mensaje:', message);
        }
    }

    toggleDetection(enable) {
        this.detectionActive = enable;
        const messageType = enable ? 'iniciar_deteccion' : 'detener_deteccion';
        console.log(`Enviando mensaje ${messageType}`);

        this.sendMessage({
            tipo: messageType,
            camara_id: this.cameraId,
            cliente_id: this.clientId,
            deteccion_activada: enable  // Agregar este campo
        });
    }

    cleanup() {
        if (this.pc) {
            this.pc.close();
            this.pc = null;
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        if (this.videoElement.srcObject) {
            this.videoElement.srcObject.getTracks().forEach(track => track.stop());
            this.videoElement.srcObject = null;
        }
    }

    stop() {
        this.toggleDetection(false);
        this.cleanup();
    }
}

export default WebRTCClient;