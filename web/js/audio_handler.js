// --- audio_handler.js ---
// This module handles all interactions with the Web Media APIs
// for capturing and processing audio via an AudioWorklet.

import { devLog, devError } from './config.js';

let audioContext = null;
let micStream = null;
let systemStream = null;
let isMuted = true; // Default to muted for privacy
let micGainNode = null;

/**
 * Requests permission to use the microphone and populates the dropdown.
 * @returns {Promise<boolean>} True if permission was granted, false otherwise.
 */
export async function setupMicrophone() {
    const micSelect = document.getElementById('mic-select');
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        stream.getTracks().forEach(track => track.stop());

        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioDevices = devices.filter(device => device.kind === 'audioinput');

        if (audioDevices.length === 0) return false;

        micSelect.innerHTML = '';
        audioDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.textContent = device.label || `Microphone ${micSelect.options.length + 1}`;
            micSelect.appendChild(option);
        });
        
        micSelect.disabled = false;
        return true;
    } catch (err) {
        devError("Error setting up microphone:", err);
        return false;
    }
}

/**
 * Starts audio processing by setting up the AudioContext, loading the worklet,
 * and connecting the audio streams.
 * @param {string} micId - The deviceId of the selected microphone.
 * @param {function} onAudioData - Callback function to handle the processed PCM audio data.
 * @returns {Promise<boolean>} True if processing started successfully.
 */
export async function startAudioProcessing(micId, onAudioData) {
    try {
        // 1. Get Audio Streams
        micStream = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: { exact: micId } } });
        systemStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });

        if (!micStream || !systemStream) {
            console.error("Could not get both audio streams.");
            stopAudioProcessing();
            return false;
        }

        // 2. Setup AudioContext and Worklet
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log(`🎵 AudioContext: ${audioContext.sampleRate}Hz`); // Keep this as it's important for debugging
        await audioContext.audioWorklet.addModule('/static/js/audio_processor.js');
        
        // 3. Create a single mixed processor for better diarization
        const mixedProcessor = new AudioWorkletNode(audioContext, 'mixed-processor');

        // Handle mixed audio with mute-aware speaker detection
        let audioProcessingCounter = 0; // For throttled logging
        
        mixedProcessor.port.onmessage = (event) => {
            const { audioData, micLevel, systemLevel } = event.data;
            
            let speakerHint;
            
            if (isMuted) {
                // When muted, ALL audio is considered as interviewer speech
                // This handles multiple interviewers or any external audio
                speakerHint = 'system'; // Always treat as interviewer when muted
                
                // Log only every 100th message to avoid console spam
                if (audioProcessingCounter % 100 === 0) {
                    devLog(`🔇 Muted mode: All audio treated as interviewer (mic: ${micLevel.toFixed(3)}, sys: ${systemLevel.toFixed(3)})`);
                }
            } else {
                // When unmuted, use volume-based detection to distinguish speakers
                // If system audio is much louder, likely interviewer speaking
                // If microphone is louder, likely candidate speaking
                speakerHint = systemLevel > micLevel * 2 ? 'system' : 'microphone';
                
                // Log only every 100th message to avoid console spam
                if (audioProcessingCounter % 100 === 0) {
                    devLog(`🎤 Unmuted mode: Speaker detected as ${speakerHint} (mic: ${micLevel.toFixed(3)}, sys: ${systemLevel.toFixed(3)})`);
                }
            }
            
            audioProcessingCounter++;
            onAudioData(audioData, speakerHint);
        };

        // 4. Connect both sources to the mixed processor with mute control
        const micSource = audioContext.createMediaStreamSource(micStream);
        const systemSource = audioContext.createMediaStreamSource(systemStream);
        
        // Create gain node for microphone muting (starts muted by default)
        micGainNode = audioContext.createGain();
        micGainNode.gain.value = isMuted ? 0 : 1;
        devLog(`🎤 Microphone initialized as ${isMuted ? 'muted' : 'unmuted'} by default`);
        
        // Connect mic through gain node for mute control
        micSource.connect(micGainNode);
        micGainNode.connect(mixedProcessor);
        
        // System audio connects directly (we don't want to mute interviewer)
        systemSource.connect(mixedProcessor);

        // The video track from getDisplayMedia is not needed.
        systemStream.getVideoTracks().forEach(track => track.stop());

        devLog("✅ Audio processing started successfully");
        return true;

    } catch (err) {
        console.error("❌ Error starting audio processing:", err);
        stopAudioProcessing();
        return false;
    }
}

/**
 * Mute or unmute the microphone input to the app
 * @param {boolean} mute - True to mute, false to unmute
 */
export function setMicrophoneMute(mute) {
    const wasDebugMode = isMuted;
    isMuted = mute;
    
    if (micGainNode) {
        // Smooth transition to avoid audio pops
        micGainNode.gain.setTargetAtTime(mute ? 0 : 1, audioContext.currentTime, 0.1);
        
        // Log the mute state change with implications
        if (mute) {
            console.log(`🔇 Microphone MUTED - All audio will be treated as interviewer speech`);
        } else {
            console.log(`🎤 Microphone UNMUTED - Audio detection based on volume levels (candidate vs interviewer)`);
        }
    }
    return isMuted;
}

/**
 * Get current mute state
 */
export function isMicrophoneMuted() {
    return isMuted;
}

/**
 * Toggle microphone mute state
 */
export function toggleMicrophoneMute() {
    return setMicrophoneMute(!isMuted);
}

/**
 * Get current audio processing mode information
 */
export function getAudioProcessingMode() {
    return {
        isMuted: isMuted,
        mode: isMuted ? 'All audio treated as interviewer' : 'Volume-based speaker detection',
        description: isMuted
            ? 'Microphone muted - All voices (1 or multiple interviewers) processed as interviewer speech'
            : 'Microphone unmuted - Distinguishing between candidate and interviewer based on audio levels'
    };
}

/**
 * Stops all audio streams and closes the AudioContext.
 */
export function stopAudioProcessing() {
    console.log("Stopping audio processing.");
    if (micStream) {
        micStream.getTracks().forEach(track => track.stop());
        micStream = null;
    }
    if (systemStream) {
        systemStream.getTracks().forEach(track => track.stop());
        systemStream = null;
    }
    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
        audioContext = null;
    }
    
    // Reset mute state to default (muted)
    isMuted = true;
    micGainNode = null;
}