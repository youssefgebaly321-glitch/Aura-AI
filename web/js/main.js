// Modular main.js - Entry point and coordination
import { StateManager } from './state-manager.js';
import { WebSocketHandler } from './websocket-handler.js';
import { ProviderManager } from './provider-manager.js';
import {
    setupMicrophone,
    startAudioProcessing,
    stopAudioProcessing,
    getScreenVideoTrack,
    isScreenSharingAvailable
} from './audio_handler.js';
import muteManager from './mute-manager.js';
import { autofillForTesting } from './dev.js';
import { loadConfig, isDev, devLog, devWarn, devError } from './config.js';
import liveInterviewUI from './live-interview.js';
import hotkeyManager from './hotkeys.js';
import presetManager from './preset-manager.js';
import screenshotService from './screenshot-service.js';

// Initialize managers
const stateManager = new StateManager();
const webSocketHandler = new WebSocketHandler(stateManager);
const providerManager = new ProviderManager(stateManager, webSocketHandler);

// --- DOM Elements ---
const views = {
    onboarding: document.getElementById('onboarding-view'),
    preflight: document.getElementById('preflight-view'),
    live: document.getElementById('live-view'),
};

const micSelect = document.getElementById('mic-select');
const proceedButton = document.getElementById('proceed-to-checks');
const startButton = document.getElementById('start-interview-button');
const backButton = document.getElementById('back-to-onboarding-btn');


// --- View Management ---
function switchView(targetView) {
    Object.values(views).forEach(view => view.classList.remove('active'));
    views[targetView].classList.add('active');
}

function handleOnboarding() {
    if (stateManager.handleOnboarding()) {
        switchView('preflight');
        runPreFlightChecks();
    }
}

async function runPreFlightChecks() {
    // 1. Microphone Check
    const micPermissionCheck = document.getElementById('check-mic-permission');
    const micSelectionCheck = document.getElementById('check-mic-selection');
    
    webSocketHandler.updateCheckStatus(micPermissionCheck, 'pending', 'Requesting Microphone...');
    const micPermission = await setupMicrophone();
    if (micPermission) {
        webSocketHandler.updateCheckStatus(micPermissionCheck, 'success', 'Microphone Permission OK');
        webSocketHandler.updateCheckStatus(micSelectionCheck, 'success', 'Microphone Selection Ready');
    } else {
        webSocketHandler.updateCheckStatus(micPermissionCheck, 'error', 'Microphone Permission Denied');
        webSocketHandler.updateCheckStatus(micSelectionCheck, 'error', 'Microphone Selection Failed');
        return;
    }

    // 2. Backend Connection
    webSocketHandler.connect();

    // 3. AI Provider Checks
    await providerManager.runPreFlightChecks();
}

// These functions are now handled by the modules

// This function is now handled by WebSocketHandler

// This function is now handled by WebSocketHandler

async function startInterview() {
    switchView('live');
    liveInterviewUI.init();
    liveInterviewUI.initialize();
    hotkeyManager.setEnabled(true);

    const onAudioData = (audioData, speakerHint) => {
        webSocketHandler.sendAudioChunk(audioData, muteManager.isMicrophoneMuted());
    };

    const processingStarted = await startAudioProcessing(micSelect.value, onAudioData);

    if (!processingStarted) {
        alert("Could not start audio streams. Please check permissions and try again.");
        switchView('preflight');
        return;
    }

    webSocketHandler.startInterview();
}

async function endInterview() {
    console.log('🔚 Ending interview and clearing state...');
    
    // Stop all audio processing
    stopAudioProcessing();
    
    // Send end interview signal to backend
    webSocketHandler.endInterview();
    
    // Disable hotkeys
    hotkeyManager.setEnabled(false);
    
    // Clear conversation UI
    if (window.liveInterviewUI) {
        liveInterviewUI.clearConversation();
    }
    
    // Comprehensive state clearing
    stateManager.clearInterviewState();
    
    // Reset preset manager if available
    if (window.presetManager) {
        presetManager.clearNotifications?.();
    }
    
    // Switch back to onboarding
    switchView('onboarding');
    
    console.log('✅ Interview ended and state cleared successfully');
}

// Provider management functions are now handled by ProviderManager


// --- Preset Switching Functions ---
function switchPreset(presetKey) {
    return webSocketHandler.switchPreset(presetKey);
}

// --- Transparency Functions ---
async function setTransparency(level) {
    return await webSocketHandler.setTransparency(level);
}

function getSystemStatus() {
    return stateManager.getSystemStatus();
}

// --- Vision Mode Functions ---
function switchVisionModel() {
    return stateManager.switchVisionModel();
}

function toggleVisionMode() {
    return stateManager.toggleVisionMode();
}

// --- Screenshot Functions ---
async function captureScreenshot() {
    return await stateManager.captureScreenshot();
}

async function processScreenshots() {
    return await stateManager.processScreenshots();
}

async function resetScreenshotQueue() {
    return await stateManager.resetScreenshotQueue();
}

// --- Audio Toggle Functions ---
function toggleMicMute() {
    return stateManager.toggleMicMute();
}

function toggleUniversalMute() {
    return stateManager.toggleUniversalMute();
}

// --- Event Listeners ---
function setupEventListeners() {
    proceedButton?.addEventListener('click', handleOnboarding);
    startButton?.addEventListener('click', startInterview);
    backButton?.addEventListener('click', () => switchView('onboarding'));
    
    // Provider change listeners
    const providerSelect = document.getElementById('ai-provider-select');
    const secondaryProviderSelect = document.getElementById('ai-secondary-provider-select');
    const visionProviderSelect = document.getElementById('vision-provider-select');
    const visionSecondaryProviderSelect = document.getElementById('vision-secondary-provider-select');
    
    providerSelect?.addEventListener('change', providerManager.updateModelDropdown.bind(providerManager));
    secondaryProviderSelect?.addEventListener('change', providerManager.updateSecondaryModelDropdown.bind(providerManager));
    visionProviderSelect?.addEventListener('change', providerManager.updateVisionModelDropdown.bind(providerManager));
    visionSecondaryProviderSelect?.addEventListener('change', providerManager.updateSecondaryVisionModelDropdown.bind(providerManager));
}

// Main initialization
window.addEventListener('DOMContentLoaded', async () => {
    await loadConfig();
    await providerManager.loadAiProviders();
    liveInterviewUI.init();
    setupEventListeners();
    setupDeveloperShortcuts();
    setupPresetHotkeys();
    hotkeyManager.setEnabled(false);
    switchView('onboarding');
});

// --- Developer Shortcuts ---
function setupDeveloperShortcuts() {
    
    devLog('🛠️ Developer shortcuts enabled');
    window.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'j') {
            e.preventDefault();
            devLog('🛠️ Auto-filling form via Ctrl+J');
            autofillForTesting();
        }
    });
}

function setupPresetHotkeys() {
    devLog('🎹 Setting up preset switching and vision hotkeys');
    document.addEventListener('keydown', (e) => {
        // Only work during live interview and if not focusing on input fields
        if (!e.target.matches('input, textarea, select') && stateManager.isLiveInterviewActive()) {
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                switch(e.key.toLowerCase()) {
                    case 'q':
                        e.preventDefault();
                        switchPreset('primary');
                        devLog('🔄 Hotkey: Switching to primary preset');
                        break;
                    case 'w': 
                        e.preventDefault();
                        switchPreset('secondary');
                        devLog('🔄 Hotkey: Switching to secondary preset');
                        break;
                    case 'e':
                        e.preventDefault(); 
                        switchPreset('auto');
                        devLog('🔄 Hotkey: Auto-selecting best preset');
                        break;
                    case 't':
                        e.preventDefault();
                        switchVisionModel();
                        devLog('🔄 Hotkey: Switching vision model');
                        break;
                    case 'v':
                        e.preventDefault();
                        toggleVisionMode();
                        devLog('👁️ Hotkey: Toggling vision mode');
                        break;
                    case 's':
                        e.preventDefault();
                        captureScreenshot();
                        devLog('📸 Hotkey: Capturing screenshot');
                        break;
                    case 'p':
                        e.preventDefault();
                        processScreenshots();
                        devLog('🔄 Hotkey: Processing screenshots');
                        break;
                }
            }
        }
    });
}

// --- Global Exports ---
// Make functions globally accessible for hotkeys and external calls
window.switchPreset = switchPreset;
window.setTransparency = setTransparency;
window.getSystemStatus = getSystemStatus;
window.switchVisionModel = switchVisionModel;
window.toggleVisionMode = toggleVisionMode;
window.captureScreenshot = captureScreenshot;
window.processScreenshots = processScreenshots;
window.resetScreenshotQueue = resetScreenshotQueue;
window.toggleMicMute = toggleMicMute;
window.toggleUniversalMute = toggleUniversalMute;
window.endInterview = endInterview;
window.getScreenVideoTrack = getScreenVideoTrack;
window.isScreenSharingAvailable = isScreenSharingAvailable;

// Export managers for other modules
window.appState = stateManager.getState();
window.sendSocketMessage = (type, payload) => webSocketHandler.sendMessage(type, payload);
window.webSocketHandler = webSocketHandler;

// Export for external use
export { switchView, startInterview, endInterview, stateManager, webSocketHandler, providerManager };