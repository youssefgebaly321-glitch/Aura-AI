import { devLog } from './config.js';
import liveInterviewUI from './live-interview.js';

export class WebSocketHandler {
    constructor(stateManager) {
        this.stateManager = stateManager;
        this.socket = null;
        this.checks = {};
        this.initializeCheckElements();
    }

    initializeCheckElements() {
        this.checks = {
            micPermission: document.getElementById('check-mic-permission'),
            micSelection: document.getElementById('check-mic-selection'),
            backend: document.getElementById('check-backend'),
            deepgram: document.getElementById('check-deepgram'),
            aiProvider: document.getElementById('check-ai-provider'),
            aiSecondaryProvider: document.getElementById('check-ai-secondary-provider'),
            visionProvider: document.getElementById('check-vision-provider'),
            visionSecondaryProvider: document.getElementById('check-vision-secondary-provider'),
        };
    }

    connect() {
        this.updateCheckStatus(this.checks.backend, 'pending', 'Connecting to Backend...');
        this.socket = new WebSocket("ws://127.0.0.1:8002/ws");
        this.stateManager.setSocket(this.socket);

        this.socket.onopen = (e) => {
            console.log("[open] Connection established");
            this.updateCheckStatus(this.checks.backend, 'success', 'Backend Connected');
            this.updateCheckStatus(this.checks.deepgram, 'pending', 'Checking Deepgram API...');
        };

        this.socket.onclose = (event) => {
            this.updateCheckStatus(this.checks.backend, 'error', 'Backend Disconnected');
        };

        this.socket.onerror = (error) => {
            this.updateCheckStatus(this.checks.backend, 'error', 'Backend Connection Failed');
        };

        this.socket.onmessage = (event) => {
            this.handleMessage(JSON.parse(event.data));
        };
    }

    handleMessage(data) {
        devLog("Received from backend:", data);

        switch (data.type) {
            case 'api_key_status':
                this.handleApiKeyStatus(data.payload);
                break;
            case 'transcript_update':
                this.handleTranscriptUpdate(data.payload);
                break;
            case 'ai_answer':
                this.handleAiAnswer(data.payload);
                break;
            case 'preset_initialized':
                this.handlePresetInitialized(data.payload);
                break;
            case 'preset_switched':
                this.handlePresetSwitched(data.payload);
                break;
            case 'preset_switch_failed':
                this.handlePresetSwitchFailed(data.payload);
                break;
            case 'system_status':
                this.handleSystemStatus(data.payload);
                break;
            case 'vision_analysis_result':
                this.handleVisionAnalysisResult(data.payload);
                break;
            case 'error':
                this.handleError(data.payload);
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    handleApiKeyStatus({ service, valid }) {
        const checkElement = service === 'deepgram' ? this.checks.deepgram : this.checks.aiProvider;
        const serviceName = service.charAt(0).toUpperCase() + service.slice(1);

        if (valid) {
            this.updateCheckStatus(checkElement, 'success', `${serviceName} API OK`);
        } else {
            this.updateCheckStatus(checkElement, 'error', `${serviceName} API Key Invalid`);
        }
        this.checkAllSystemsGo();
    }

    handleTranscriptUpdate(payload) {
        if (window.liveInterviewUI) {
            if (payload.is_final) {
                liveInterviewUI.addInterviewerQuestion(payload.transcript, false);
                liveInterviewUI.showActivity('Generating response...');
            } else {
                liveInterviewUI.addInterviewerQuestion(payload.transcript, true);
            }
        }
    }

    handleAiAnswer(payload) {
        if (window.liveInterviewUI) {
            const filteredAnswer = this.filterThinkingContent(payload.answer);
            liveInterviewUI.addAIResponse(filteredAnswer, {
                preset: payload.preset_used,
                success: payload.success,
                error: payload.error_info,
                fallback: payload.fallback_info
            });
        }
    }

    handlePresetInitialized(payload) {
        this.stateManager.updateState({
            currentPreset: payload.current_preset,
            availablePresets: payload.available_presets
        });
        
        if (window.presetManager) {
            presetManager.updatePresetDisplay(payload.current_preset);
            presetManager.updateHealthStatus(payload.health_status);
        }
        
        devLog("Preset system initialized:", payload);
    }

    handlePresetSwitched(payload) {
        this.stateManager.updateState({ currentPreset: payload.current_preset });
        
        if (window.presetManager) {
            presetManager.updatePresetDisplay(payload.current_preset);
            presetManager.showSwitchNotification(payload);
        }
        
        devLog("Preset switched:", payload);
    }

    handlePresetSwitchFailed(payload) {
        if (window.presetManager) {
            presetManager.showErrorNotification(payload.error, payload);
        }
        console.error("Preset switch failed:", payload);
    }

    handleSystemStatus(payload) {
        this.stateManager.updateState({ systemStatus: payload });
        devLog("System status update:", payload);
    }

    handleVisionAnalysisResult(result) {
        console.log('📥 Received vision analysis result:', result.success ? 'SUCCESS' : 'FAILED');
        
        // Calculate processing time
        const endTime = Date.now();
        const processingDuration = this.visionProcessingStartTime ? 
            endTime - this.visionProcessingStartTime : null;
        
        if (processingDuration) {
            console.log(`⏱️ Vision analysis completed in ${processingDuration}ms`);
        }
        
        // Remove processing status indicator
        this.hideVisionProcessingStatus();
        
        if (result.success) {
            if (window.liveInterviewUI) {
                console.log('📺 Displaying vision analysis in conversation');
                
                const filteredAnalysis = this.filterThinkingContent(result.analysis);
                
                liveInterviewUI.addVisionAnalysis(filteredAnalysis, {
                    screenshotCount: result.screenshot_count,
                    model: result.metadata.model,
                    provider: result.metadata.provider,
                    languages: result.languages,
                    processingDuration: processingDuration
                });
            } else {
                console.warn('⚠️ liveInterviewUI not available for vision display');
            }
            
            if (window.visionAnalysisResolver) {
                console.log('✅ Resolving vision analysis promise');
                window.visionAnalysisResolver(result);
                window.visionAnalysisResolver = null;
            } else {
                console.warn('⚠️ No vision analysis resolver found');
            }
            
            devLog("Vision analysis completed successfully");
        } else {
            console.error("❌ Vision analysis failed:", result.error);
            
            if (window.liveInterviewUI) {
                liveInterviewUI.addMessage(
                    `I'm sorry, there was an error analyzing the screenshots: ${result.error}`,
                    'ai-response'
                );
            }
            
            if (window.visionAnalysisResolver) {
                console.log('❌ Resolving vision analysis promise with error');
                window.visionAnalysisResolver({
                    success: false,
                    error: result.error
                });
                window.visionAnalysisResolver = null;
            } else {
                console.warn('⚠️ No vision analysis resolver found for error handling');
            }
        }
        
        // Clear processing timer
        this.visionProcessingStartTime = null;
    }

    // Show vision processing status and start timing
    showVisionProcessingStatus(screenshotCount, provider, model) {
        this.visionProcessingStartTime = Date.now();
        
        if (window.liveInterviewUI && liveInterviewUI.addMessage) {
            // Add processing indicator to conversation
            const processingMessage = `🔄 Analyzing ${screenshotCount} screenshot${screenshotCount !== 1 ? 's' : ''} with ${provider} - ${model}...`;
            
            // Create a temporary message element for processing status
            const conversationContainer = document.getElementById('conversation-container') || 
                                         document.querySelector('.conversation-stream');
            
            if (conversationContainer) {
                // Remove any existing processing status
                const existingStatus = conversationContainer.querySelector('.vision-processing-indicator');
                if (existingStatus) {
                    existingStatus.remove();
                }

                const statusDiv = document.createElement('div');
                statusDiv.className = 'message ai-response vision-processing-indicator';
                statusDiv.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px; color: #6366f1; font-weight: 500;">
                        <div class="processing-spinner" style="width: 16px; height: 16px; border: 2px solid #e5e7eb; border-top: 2px solid #6366f1; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                        ${processingMessage}
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                        Processing time: 10-45 seconds (optimized for speed)
                    </div>
                `;
                
                // Add spinner animation if not already present
                if (!document.getElementById('vision-spinner-styles')) {
                    const style = document.createElement('style');
                    style.id = 'vision-spinner-styles';
                    style.textContent = `
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    `;
                    document.head.appendChild(style);
                }
                
                conversationContainer.appendChild(statusDiv);
                statusDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
                this.visionProcessingElement = statusDiv;
            }
        }
        
        console.log(`🔄 Vision processing started: ${screenshotCount} screenshots`);
    }

    hideVisionProcessingStatus() {
        if (this.visionProcessingElement) {
            this.visionProcessingElement.remove();
            this.visionProcessingElement = null;
        }
    }

    handleError(payload) {
        console.error("WebSocket error:", payload);
        if (window.presetManager) {
            presetManager.showErrorNotification(payload.message);
        }
    }

    sendMessage(type, payload) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type, payload }));
        }
    }

    sendAudioChunk(chunk, is_muted) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const message = JSON.stringify({
                type: 'audio_chunk',
                payload: {
                    audio: Array.from(new Uint8Array(chunk)),
                    is_muted: is_muted
                }
            });
            this.socket.send(message);
        }
    }

    startInterview() {
        const state = this.stateManager.getState();
        const initialMuteStatus = window.muteManager?.getMuteStatus() || { microphone: false, universal: false };
        
        const interviewPayload = {
            aiProvider: state.selectedProvider,
            onboardingData: state.onboardingData,
            is_muted: initialMuteStatus.microphone,
            is_universally_muted: initialMuteStatus.universal,
            process_all_speakers: true,
        };
        
        if (state.selectedSecondaryProvider.name && state.selectedSecondaryProvider.model) {
            interviewPayload.aiSecondaryProvider = state.selectedSecondaryProvider;
        }
        
        if (state.selectedVisionProvider.name && state.selectedVisionProvider.model) {
            interviewPayload.visionProvider = state.selectedVisionProvider;
        }
        
        if (state.selectedSecondaryVisionProvider.name && state.selectedSecondaryVisionProvider.model) {
            interviewPayload.visionSecondaryProvider = state.selectedSecondaryVisionProvider;
        }
        
        this.sendMessage('start_interview', interviewPayload);
    }

    endInterview() {
        this.sendMessage('end_interview', {});
        
        // Clear any pending message handlers
        if (this.socket) {
            // Set socket to null after sending end message
            setTimeout(() => {
                this.stateManager.updateState({ socket: null });
            }, 100);
        }
    }

    switchPreset(presetKey) {
        console.log(`🎮 switchPreset called: ${presetKey} (could be from global hotkey)`);
        
        if (!this.stateManager.isLiveInterviewActive()) {
            console.warn('⚠️ Preset switching only available during live interview');
            if (window.presetManager) {
                presetManager.showErrorNotification('Start the interview first before switching AI presets');
            } else {
                alert('Please start the interview before switching AI presets');
            }
            return false;
        }
        
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.sendMessage('switch_preset', { preset_key: presetKey });
        } else {
            console.error('Cannot switch preset: WebSocket not connected');
            if (window.presetManager) {
                presetManager.showErrorNotification('WebSocket not connected - please restart the interview');
            }
        }
    }

    async setTransparency(level) {
        console.log(`🎮 setTransparency called: ${level} (could be from global hotkey)`);
        
        try {
            let endpoint = '';
            let opacity = '';
            
            switch(level) {
                case 'transparent':
                    endpoint = '/api/transparency/presets/transparent';
                    opacity = '40%';
                    break;
                case 'semi':
                    endpoint = '/api/transparency/presets/semi-transparent';
                    opacity = '70%';
                    break;
                case 'opaque':
                    endpoint = '/api/transparency/presets/opaque';
                    opacity = '100%';
                    break;
                default:
                    console.warn(`⚠️ Unknown transparency level: ${level}`);
                    return false;
            }
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log(`✅ Transparency set to ${opacity} globally`);
                
                if (window.presetManager) {
                    presetManager.showSwitchNotification({
                        message: `Window transparency: ${opacity}`,
                        type: 'transparency'
                    });
                }
                
                devLog(`🔍 Global transparency set to: ${opacity}`);
                return true;
            } else {
                console.error('❌ Failed to set transparency:', result);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Error setting transparency:', error);
            
            if (window.presetManager) {
                presetManager.showErrorNotification('Failed to set window transparency');
            }
            
            return false;
        }
    }

    updateCheckStatus(checkElement, status, text) {
        if (!checkElement) return;
        
        const indicator = checkElement.querySelector('.indicator');
        const textNode = Array.from(checkElement.childNodes).find(node =>
            node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== ''
        );
        
        if (indicator) {
            indicator.textContent = status === 'success' ? '🟢' : status === 'error' ? '🔴' : '⚪';
        }
        
        if (textNode) {
            textNode.nodeValue = ` ${text}`;
        }
    }

    checkAllSystemsGo() {
        const visibleChecks = Object.values(this.checks).filter(check => 
            check && check.style.display !== 'none' && getComputedStyle(check).display !== 'none'
        );
        
        const allGreen = visibleChecks.every(
            check => check.querySelector('.indicator')?.textContent === '🟢'
        );
        
        const startButton = document.getElementById('start-interview-button');
        if (startButton) {
            startButton.disabled = !allGreen;
        }
        
        if (allGreen) {
            console.log("All systems go! Ready to start interview.");
            
            // Log which providers were verified
            const verifiedProviders = [];
            if (this.checks.aiProvider.querySelector('.indicator')?.textContent === '🟢') {
                const state = this.stateManager.getState();
                verifiedProviders.push(`Primary: ${state.selectedProvider.name}`);
            }
            if (this.checks.aiSecondaryProvider.style.display !== 'none' && 
                this.checks.aiSecondaryProvider.querySelector('.indicator')?.textContent === '🟢') {
                const state = this.stateManager.getState();
                verifiedProviders.push(`Secondary: ${state.selectedSecondaryProvider.name}`);
            }
            if (this.checks.visionProvider.style.display !== 'none' && 
                this.checks.visionProvider.querySelector('.indicator')?.textContent === '🟢') {
                const state = this.stateManager.getState();
                verifiedProviders.push(`Vision: ${state.selectedVisionProvider.name}`);
            }
            
            devLog('✅ All verified providers:', verifiedProviders);
        } else {
            devLog('⚠️ Some checks are still pending or failed');
        }
    }

    filterThinkingContent(content) {
        if (!content || typeof content !== 'string') {
            return content;
        }
        
        // Remove content between <think> and </think> tags (case insensitive, multiline)
        const thinkingRegex = /<think\s*>[\s\S]*?<\/think\s*>/gi;
        let filteredContent = content.replace(thinkingRegex, '');
        
        // Clean up any extra whitespace or newlines left behind
        filteredContent = filteredContent.replace(/\n\s*\n\s*\n/g, '\n\n').trim();
        
        return filteredContent;
    }
} 