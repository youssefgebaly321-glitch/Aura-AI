// Hotkeys Module for Aura
// Provides keyboard shortcuts for transparency and other controls

import { devLog } from './config.js';

class HotkeyManager {
    constructor() {
        this.isAltLPressed = false;
        this.transparencyLevels = [0.2, 0.4, 0.6, 0.8, 1.0]; // 5 levels: 20%, 40%, 60%, 80%, 100%
        this.currentTransparencyLevel = 2; // Default to 60% (index 2)
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
            if (e.altKey && e.key.toLowerCase() === 'l') {
                e.preventDefault();
            }
        });
    }

    handleKeyDown(event) {
        if (!this.isEnabled) return;

        // Check for Alt+L combination
        if (event.altKey && event.key.toLowerCase() === 'l') {
            this.isAltLPressed = true;
            this.showTransparencyHint();
            event.preventDefault();
            return;
        }

        // Handle transparency controls when Alt+L is held
        if (this.isAltLPressed) {
            switch (event.key) {
                case '[':
                    this.decreaseTransparency();
                    event.preventDefault();
                    break;
                case ']':
                    this.increaseTransparency();
                    event.preventDefault();
                    break;
                case 'Escape':
                    this.hideTransparencyHint();
                    break;
                case 't':
                case 'T':
                    this.toggleAlwaysOnTop();
                    event.preventDefault();
                    break;
            }
        }
    }

    handleKeyUp(event) {
        if (event.key === 'Alt' || event.key.toLowerCase() === 'l') {
            this.isAltLPressed = false;
            this.hideTransparencyHint();
        }
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
        this.removeExistingHints();
        
        const hint = document.createElement('div');
        hint.id = 'transparency-hint';
        hint.innerHTML = `
            <div class="hotkey-hint">
                <div class="hint-title">🎹 Transparency Control</div>
                <div class="hint-controls">
                    <span class="hint-key">Alt+L + [</span> Less Transparent
                    <span class="hint-key">Alt+L + ]</span> More Transparent
                    <span class="hint-key">Alt+L + T</span> Toggle Always On Top
                </div>
                <div class="hint-level">Level: ${this.currentTransparencyLevel + 1}/5 (${Math.round(this.transparencyLevels[this.currentTransparencyLevel] * 100)}%)</div>
            </div>
        `;
        
        document.body.appendChild(hint);
    }

    hideTransparencyHint() {
        const hint = document.getElementById('transparency-hint');
        if (hint) {
            hint.remove();
        }
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
        const existing = document.getElementById('transparency-hint');
        if (existing) existing.remove();
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

    async toggleAlwaysOnTop() {
        this.isAlwaysOnTop = !this.isAlwaysOnTop;
        
        try {
            const response = await fetch('/api/window/always-on-top', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ on_top: this.isAlwaysOnTop })
            });
            
            if (response.ok) {
                const status = this.isAlwaysOnTop ? "enabled" : "disabled";
                devLog(`📌 Always on top ${status} via hotkey`);
                this.showAlwaysOnTopFeedback(this.isAlwaysOnTop);
            }
        } catch (error) {
            console.error('❌ Error toggling always on top via hotkey:', error);
        }
    }

    showAlwaysOnTopFeedback(isOnTop) {
        this.removeExistingFeedback();
        
        const feedback = document.createElement('div');
        feedback.id = 'transparency-feedback';
        feedback.innerHTML = `
            <div class="transparency-feedback">
                📌 Always On Top ${isOnTop ? 'Enabled' : 'Disabled'}
            </div>
        `;
        
        document.body.appendChild(feedback);
        
        // Auto-hide after 2 seconds
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.remove();
            }
        }, 2000);
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