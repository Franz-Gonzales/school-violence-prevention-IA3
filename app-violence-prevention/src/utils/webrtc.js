// utils/webrtc.js
export class WebRTCClient {
    constructor(cameraId, videoElement, onDetection) {
        this.cameraId = cameraId;
        this.videoElement = videoElement;
        this.onDetection = onDetection;
        this.clientId = this.generateClientId();
        this.pc = null;
        this.ws = null;
        this.detectionActive = false;
    }

    generateClientId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    async connect(detectionActive = false) {
        const wsUrl = `ws://localhost:8000/api/v1/cameras/${this.cameraId}/stream?cliente_id=${this.clientId}&camara_id=${this.cameraId}`;
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
            // Configuración simplificada de RTCPeerConnection
            this.pc = new RTCPeerConnection({
                iceServers: [
                    {
                        urls: 'stun:stun.l.google.com:19302'
                    }
                ]
            });

            this.pc.ontrack = (event) => {
                if (event.track.kind === 'video') {
                    this.videoElement.srcObject = event.streams[0];
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
                    this.cleanup();
                }
            };


            // Crear y enviar oferta
            const offer = await this.pc.createOffer({
                offerToReceiveVideo: true,
                offerToReceiveAudio: false
            });

            await this.pc.setLocalDescription(offer);

            this.sendMessage({
                tipo: 'offer',
                sdp: this.pc.localDescription.sdp,
                destino_id: this.clientId,
                deteccion_activada: detectionActive
            });

        } catch (error) {
            console.error('Error en startWebRTC:', error);
            this.cleanup();
            throw error;
        }
    }


    async handleMessage(message) {
        try {
            if (message.tipo === 'answer') {
                if (!message.sdp) {
                    console.error('Mensaje answer no contiene SDP:', message);
                    return;
                }
                await this.pc.setRemoteDescription(new RTCSessionDescription({
                    type: 'answer',
                    sdp: message.sdp
                }));
                console.log('Respuesta answer procesada correctamente');
            } else if (message.tipo === 'ice_candidate') {
                await this.pc.addIceCandidate(new RTCIceCandidate(message.candidate));
            } else if (message.tipo === 'deteccion_violencia') {
                this.onDetection(message);
            }
        } catch (error) {
            console.error('Error al manejar mensaje WebSocket:', error, 'Mensaje:', message);
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
        this.sendMessage({
            tipo: enable ? 'iniciar_deteccion' : 'detener_deteccion',
            camara_id: this.cameraId
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