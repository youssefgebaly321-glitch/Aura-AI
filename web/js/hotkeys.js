// Hotkeys Module for Aura
// Provides keyboard shortcuts for transparency and other controls

import { devLog } from './config.js';
import muteManager from './mute-manager.js';

class HotkeyManager {
    constructor() {
        this.transparencyLevels = [0.2, 0.4, 0.6, 0.8, 1.0]; // 5 levels: 20%, 40%, 60%, 80%, 100%
        this.currentTransparencyLevel = 3; // Default to 80% (index 3)
        this.isEnabled = true;
        this.isAlwaysOnTop = true; // Track always-on-top state
        
        this.setupEventListeners();
        devLog('🎹 Hotkey manager initialized');
    }

    setupEventListeners() {
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        document.addEventListener('keyup', this.handleKeyUp.bind(this));
        
        // Prevent default browser shortcuts that might interfere
        document.addEventListener('keydown', (e) => {
            // Prevent default browser actions for Alt+[ and Alt+]
            if (e.altKey && ['[', ']', 'm', 'u'].includes(e.key.toLowerCase())) {
                e.preventDefault();
            }
        });
    }

    handleKeyDown(event) {
        if (!this.isEnabled) return;

        // Check for Alt+M for microphone mute
        if (event.altKey && event.key.toLowerCase() === 'm') {
            this.toggleMicrophoneMute();
            return;
        }

        // Check for Alt+U for universal mute/pause
        if (event.altKey && event.key.toLowerCase() === 'u') {
            this.toggleUniversalMute();
            return;
        }

        // Check for Alt+[ to decrease transparency
        if (event.altKey && event.key === '[') {
            this.decreaseTransparency();
            return;
        }

        // Check for Alt+] to increase transparency
        if (event.altKey && event.key === ']') {
            this.increaseTransparency();
            return;
        }
    }

    handleKeyUp(event) {
        // This method is kept for event listener consistency, but is currently empty.
    }

    decreaseTransparency() {
        if (this.currentTransparencyLevel > 0) {
            this.currentTransparencyLevel--;
            this.applyTransparency();
        }
    }

    increaseTransparency() {
        if (this.currentTransparencyLevel < this.transparencyLevels.length - 1) {
            this.currentTransparencyLevel++;
            this.applyTransparency();
        }
    }

    async applyTransparency() {
        const transparency = this.transparencyLevels[this.currentTransparencyLevel];
        const percent = Math.round(transparency * 100);
        
        try {
            // Only allow transparency changes during live interview
            const currentView = document.querySelector('.view.active');
            const isLiveView = currentView && currentView.id === 'live-view';
            
            if (!isLiveView) {
                console.log('ℹ️ Transparency hotkeys only work during live interview');
                this.showTransparencyFeedback(100, 'Transparency only available in live interview');
                return;
            }
            
            // Apply Windows-level transparency
            const response = await fetch('/api/transparency', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transparency: transparency })
            });
            
            if (response.ok) {
                devLog(`🪟 Transparency set to ${percent}% via hotkey`);
                this.showTransparencyFeedback(percent);
            }
        } catch (error) {
            console.error('❌ Error setting transparency via hotkey:', error);
        }
    }

    showTransparencyHint() {
        // This hint is no longer needed as the interaction is simpler
        // The feedback on change is sufficient
    }

    hideTransparencyHint() {
        // This hint is no longer needed as the interaction is simpler
    }

    showTransparencyFeedback(percent, message = null) {
        this.removeExistingFeedback();
        
        const feedback = document.createElement('div');
        feedback.id = 'transparency-feedback';
        
        if (message) {
            feedback.innerHTML = `
                <div class="transparency-feedback">
                    ℹ️ ${message}
                </div>
            `;
        } else {
            feedback.innerHTML = `
                <div class="transparency-feedback">
                    🪟 ${percent}% Opacity
                    <div class="transparency-bar">
                        ${this.generateTransparencyBar()}
                    </div>
                </div>
            `;
        }
        
        document.body.appendChild(feedback);
        
        // Auto-hide after 2 seconds
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.remove();
            }
        }, 2000);
    }

    generateTransparencyBar() {
        let bar = '';
        for (let i = 0; i < this.transparencyLevels.length; i++) {
            const isActive = i === this.currentTransparencyLevel;
            bar += `<span class="bar-segment ${isActive ? 'active' : ''}">${isActive ? '●' : '○'}</span>`;
        }
        return bar;
    }

    removeExistingHints() {
        // This hint is no longer needed
    }

    removeExistingFeedback() {
        const existing = document.getElementById('transparency-feedback');
        if (existing) existing.remove();
    }

    // Public methods for external control
    setEnabled(enabled) {
        this.isEnabled = enabled;
        devLog(`🎹 Hotkeys ${enabled ? 'enabled' : 'disabled'}`);
    }

    getCurrentTransparency() {
        return {
            level: this.currentTransparencyLevel + 1,
            percent: Math.round(this.transparencyLevels[this.currentTransparencyLevel] * 100),
            value: this.transparencyLevels[this.currentTransparencyLevel]
        };
    }

    setTransparencyLevel(level) {
        if (level >= 1 && level <= 5) {
            this.currentTransparencyLevel = level - 1;
            this.applyTransparency();
        }
    }


    toggleMicrophoneMute() {
        if (!this.isLiveInterviewActive()) {
            this.showMuteFeedback(false, 'Microphone mute only available in live interview');
            return;
        }

        const isMuted = muteManager.toggleMicrophoneMute();
        this.showMuteFeedback(isMuted);
        devLog(`🎤 Microphone ${isMuted ? 'muted' : 'unmuted'} via hotkey`);
    }

    toggleUniversalMute() {
        if (!this.isLiveInterviewActive()) {
            this.showUniversalMuteFeedback(false, 'Universal pause only available in live interview');
            return;
        }
        
        const isPaused = muteManager.toggleUniversalMute();
        this.showUniversalMuteFeedback(isPaused);
        devLog(`⏸️ Universal mute ${isPaused ? 'enabled' : 'disabled'} via hotkey`);
    }

    isLiveInterviewActive() {
        const currentView = document.querySelector('.view.active');
        return currentView && currentView.id === 'live-view';
    }

    showMuteFeedback(isMuted, message = null) {
        this.removeExistingFeedback();
        
        const feedback = document.createElement('div');
        feedback.id = 'transparency-feedback';
        
        if (message) {
            feedback.innerHTML = `<div class="transparency-feedback">ℹ️ ${message}</div>`;
        } else {
            feedback.innerHTML = `
                <div class="transparency-feedback">
                    🎤 Microphone ${isMuted ? 'Muted' : 'Unmuted'}
                    <div class="mute-status">${isMuted ? 'App audio input disabled' : 'App audio input enabled'}</div>
                </div>`;
        }
        
        document.body.appendChild(feedback);
        this.autoHideFeedback(feedback);
    }

    showUniversalMuteFeedback(isPaused, message = null) {
        this.removeExistingFeedback();
        
        const feedback = document.createElement('div');
        feedback.id = 'transparency-feedback';
        feedback.className = isPaused ? 'universal-mute-active' : '';

        if (message) {
            feedback.innerHTML = `<div class="transparency-feedback">ℹ️ ${message}</div>`;
        } else {
            feedback.innerHTML = `
                <div class="transparency-feedback">
                    ⏸️ System ${isPaused ? 'Paused' : 'Resumed'}
                    <div class="mute-status">${isPaused ? 'All audio processing is stopped' : 'Audio processing is active'}</div>
                </div>`;
        }
        
        document.body.appendChild(feedback);
        this.autoHideFeedback(feedback);
    }

    autoHideFeedback(element) {
        setTimeout(() => {
            if (element.parentNode) {
                element.remove();
            }
        }, 2500);
    }
}

// Create global instance
const hotkeyManager = new HotkeyManager();

// Global functions for console access
window.enableHotkeys = () => hotkeyManager.setEnabled(true);
window.disableHotkeys = () => hotkeyManager.setEnabled(false);
window.getTransparencyLevel = () => hotkeyManager.getCurrentTransparency();
window.setTransparencyLevel = (level) => hotkeyManager.setTransparencyLevel(level);

export default hotkeyManager; 