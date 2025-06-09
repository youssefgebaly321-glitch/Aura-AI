import { devLog } from './config.js';

export class ProviderManager {
    constructor(stateManager, webSocketHandler) {
        this.stateManager = stateManager;
        this.webSocketHandler = webSocketHandler;
        this.aiProviders = [];
        
        this.onboardingForm = {};
        this.checks = {};
        this.initializeElements();
    }

    initializeElements() {
        this.onboardingForm = {
            providerSelect: document.getElementById('ai-provider-select'),
            modelSelect: document.getElementById('ai-model-select'),
            secondaryProviderSelect: document.getElementById('ai-secondary-provider-select'),
            secondaryModelSelect: document.getElementById('ai-secondary-model-select'),
            visionProviderSelect: document.getElementById('vision-provider-select'),
            visionModelSelect: document.getElementById('vision-model-select'),
            visionSecondaryProviderSelect: document.getElementById('vision-secondary-provider-select'),
            visionSecondaryModelSelect: document.getElementById('vision-secondary-model-select'),
        };
        
        this.checks = {
            aiProvider: document.getElementById('check-ai-provider'),
            aiSecondaryProvider: document.getElementById('check-ai-secondary-provider'),
            visionProvider: document.getElementById('check-vision-provider'),
            visionSecondaryProvider: document.getElementById('check-vision-secondary-provider'),
        };
    }

    async loadAiProviders() {
        try {
            const response = await fetch('/api/ai-providers');
            this.aiProviders = await response.json();
            this.stateManager.updateState({ aiProviders: this.aiProviders });

            this.populateProviderDropdowns();
            
            requestAnimationFrame(() => {
                this.setDefaultAIProvider();
            });
        } catch (error) {
            console.error("Failed to load AI providers:", error);
        }
    }

    populateProviderDropdowns() {
        // Primary provider
        if (this.onboardingForm.providerSelect) {
            this.onboardingForm.providerSelect.innerHTML = '<option value="">Select AI Provider</option>';
            this.aiProviders.forEach(p => {
                const option = document.createElement('option');
                option.value = p.name;
                option.textContent = p.name;
                this.onboardingForm.providerSelect.appendChild(option);
            });
        }

        // Secondary provider
        if (this.onboardingForm.secondaryProviderSelect) {
            this.onboardingForm.secondaryProviderSelect.innerHTML = '<option value="">Select Secondary Provider (Optional)</option>';
            this.aiProviders.forEach(p => {
                const option = document.createElement('option');
                option.value = p.name;
                option.textContent = p.name;
                this.onboardingForm.secondaryProviderSelect.appendChild(option);
            });
        }

        // Vision providers
        const visionProviders = this.aiProviders.filter(p => p.supportsVision && p.visionModels?.length > 0);
        
        if (this.onboardingForm.visionProviderSelect) {
            this.onboardingForm.visionProviderSelect.innerHTML = '<option value="">Select Vision Provider (Optional)</option>';
            visionProviders.forEach(p => {
                const option = document.createElement('option');
                option.value = p.name;
                option.textContent = `${p.name} (Vision)`;
                this.onboardingForm.visionProviderSelect.appendChild(option);
            });
        }

        if (this.onboardingForm.visionSecondaryProviderSelect) {
            this.onboardingForm.visionSecondaryProviderSelect.innerHTML = '<option value="">Select Secondary Vision Provider (Optional)</option>';
            visionProviders.forEach(p => {
                const option = document.createElement('option');
                option.value = p.name;
                option.textContent = `${p.name} (Vision)`;
                this.onboardingForm.visionSecondaryProviderSelect.appendChild(option);
            });
        }
    }

    setDefaultAIProvider() {
        try {
            const defaultProvider = this.aiProviders.find(p => p.default);
            if (defaultProvider && this.onboardingForm.providerSelect) {
                this.onboardingForm.providerSelect.value = defaultProvider.name;
                this.onboardingForm.providerSelect.dispatchEvent(new Event('change'));

                setTimeout(() => {
                    if (this.onboardingForm.modelSelect && !this.onboardingForm.modelSelect.disabled) {
                        const defaultModel = defaultProvider.models.find(m => m === 'llama-3.3-70b') || defaultProvider.models[0];
                        if (defaultModel) {
                            this.onboardingForm.modelSelect.value = defaultModel;
                        }
                    }
                }, 150);
            }
        } catch (error) {
            console.error("Error setting default AI provider:", error);
        }
    }

    updateModelDropdown() {
        const providerName = this.onboardingForm.providerSelect?.value;
        const provider = this.aiProviders.find(p => p.name === providerName);
        const modelSelect = this.onboardingForm.modelSelect;

        if (!modelSelect) return;

        modelSelect.innerHTML = '<option value="">Select Model</option>';
        modelSelect.disabled = true;

        if (provider?.models) {
            provider.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
            modelSelect.disabled = false;
        }
    }

    updateSecondaryModelDropdown() {
        const providerName = this.onboardingForm.secondaryProviderSelect?.value;
        const provider = this.aiProviders.find(p => p.name === providerName);
        const modelSelect = this.onboardingForm.secondaryModelSelect;

        if (!modelSelect) return;

        modelSelect.innerHTML = '<option value="">Select Secondary Model</option>';
        modelSelect.disabled = true;

        if (provider?.models) {
            provider.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
            modelSelect.disabled = false;
        }
    }

    updateVisionModelDropdown() {
        const providerName = this.onboardingForm.visionProviderSelect?.value;
        const provider = this.aiProviders.find(p => p.name === providerName);
        const modelSelect = this.onboardingForm.visionModelSelect;

        if (!modelSelect) return;

        modelSelect.innerHTML = '<option value="">Select Vision Model</option>';
        modelSelect.disabled = true;

        if (provider?.visionModels?.length > 0) {
            provider.visionModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
            modelSelect.disabled = false;
        }
    }

    updateSecondaryVisionModelDropdown() {
        const providerName = this.onboardingForm.visionSecondaryProviderSelect?.value;
        const provider = this.aiProviders.find(p => p.name === providerName);
        const modelSelect = this.onboardingForm.visionSecondaryModelSelect;

        if (!modelSelect) return;

        modelSelect.innerHTML = '<option value="">Select Secondary Vision Model</option>';
        modelSelect.disabled = true;

        if (provider?.visionModels?.length > 0) {
            provider.visionModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
            modelSelect.disabled = false;
        }
    }

    async runPreFlightChecks() {
        const state = this.stateManager.getState();

        // Show/hide secondary checks based on selection
        if (state.selectedSecondaryProvider.name && state.selectedSecondaryProvider.model) {
            this.checks.aiSecondaryProvider.style.display = 'flex';
            devLog('Secondary provider selected, will verify during preflight');
        } else {
            this.checks.aiSecondaryProvider.style.display = 'none';
            devLog('No secondary provider selected, skipping verification');
        }

        if (state.selectedVisionProvider.name && state.selectedVisionProvider.model) {
            this.checks.visionProvider.style.display = 'flex';
            devLog('Primary vision provider selected, will verify during preflight');
        } else {
            this.checks.visionProvider.style.display = 'none';
            devLog('No primary vision provider selected, skipping verification');
        }

        if (state.selectedSecondaryVisionProvider.name && state.selectedSecondaryVisionProvider.model) {
            this.checks.visionSecondaryProvider.style.display = 'flex';
            devLog('Secondary vision provider selected, will verify during preflight');
        } else {
            this.checks.visionSecondaryProvider.style.display = 'none';
            devLog('No secondary vision provider selected, skipping verification');
        }

        await this.verifyAiProviders();
    }

    async verifyAiProviders() {
        const state = this.stateManager.getState();

        // Verify primary provider (required)
        await this.verifyProvider(state.selectedProvider, this.checks.aiProvider, 'Primary');
        
        // Verify secondary provider if selected (optional)
        if (state.selectedSecondaryProvider.name && state.selectedSecondaryProvider.model) {
            await this.verifyProvider(state.selectedSecondaryProvider, this.checks.aiSecondaryProvider, 'Secondary');
        }
        
        // Verify vision provider if selected (optional)
        if (state.selectedVisionProvider.name && state.selectedVisionProvider.model) {
            await this.verifyVisionProvider(state.selectedVisionProvider, this.checks.visionProvider, 'Primary Vision');
        }
        
        // Verify secondary vision provider if selected (optional)
        if (state.selectedSecondaryVisionProvider.name && state.selectedSecondaryVisionProvider.model) {
            await this.verifyVisionProvider(state.selectedSecondaryVisionProvider, this.checks.visionSecondaryProvider, 'Secondary Vision');
        }
        
        this.webSocketHandler.checkAllSystemsGo();
    }

    async verifyProvider(providerConfig, checkElement, providerType) {
        const { name, model } = providerConfig;
        this.webSocketHandler.updateCheckStatus(checkElement, 'pending', `Checking ${providerType} ${name}...`);
        
        try {
            const response = await fetch('/api/verify-provider', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, model }),
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.webSocketHandler.updateCheckStatus(checkElement, 'success', `${providerType} ${name} (${model}) OK`);
                devLog(`✅ ${providerType} provider verification successful:`, { name, model });
            } else {
                this.webSocketHandler.updateCheckStatus(checkElement, 'error', `${providerType} ${name} Connection Failed`);
                console.error(`❌ ${providerType} provider verification failed:`, { name, model });
            }
        } catch (error) {
            this.webSocketHandler.updateCheckStatus(checkElement, 'error', `${providerType} Provider Check Failed`);
            console.error(`❌ ${providerType} provider check error:`, error);
        }
    }

    async verifyVisionProvider(providerConfig, checkElement, providerType) {
        const { name, model } = providerConfig;
        this.webSocketHandler.updateCheckStatus(checkElement, 'pending', `Checking ${providerType} ${name}...`);
        
        try {
            const response = await fetch('/api/verify-vision-provider', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, model }),
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.webSocketHandler.updateCheckStatus(checkElement, 'success', `${providerType} ${name} (${model}) OK`);
                devLog(`✅ ${providerType} provider verification successful:`, { name, model });
            } else {
                this.webSocketHandler.updateCheckStatus(checkElement, 'error', `${providerType} ${name} Connection Failed`);
                console.error(`❌ ${providerType} provider verification failed:`, { name, model });
            }
        } catch (error) {
            this.webSocketHandler.updateCheckStatus(checkElement, 'error', `${providerType} Provider Check Failed`);
            console.error(`❌ ${providerType} provider check error:`, error);
        }
    }
} 