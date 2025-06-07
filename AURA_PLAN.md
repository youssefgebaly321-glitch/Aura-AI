# Proposed Development Plan: Project Aura

This document outlines the strategic plan for developing "Aura," a real-time AI interview coach.

### **User Flow & Application Stages**

The application will proceed through three distinct stages:

1.  **Stage 1: Onboarding:** The first screen the user sees. Its purpose is to gather essential context for the AI.
    *   **UI Components:**
        *   **Profile Input:** Text fields for Name, Company, Target Role.
        *   **Resume Input:** A large `textarea` for the user's resume text.
        *   **Interview Focus:** Checkboxes (e.g., Behavioral, System Design).
        *   **Objectives:** A `textarea` for the user's personal goals.
    *   **Action:** A "Proceed to Device Setup" button.

2.  **Stage 2: Pre-Flight Check:** The second screen. Its purpose is to verify all technical requirements.
    *   **UI Components:** A dashboard with status indicators (🟢/🔴) for:
        *   System Audio & Microphone Permissions
        *   Device Selection
        *   Backend Connection
        *   Deepgram & Groq API Key validation.
    *   **Action:** An enabled "Start Interview" button once all checks pass.

3.  **Stage 3: Live Interview:** The main application interface.
    *   **UI Components:**
        *   A pane to display the live, diarized transcript.
        *   A pane to display the real-time AI-generated answers.
        *   A pane for code snippets.
        *   A "Hold to Speak" button for the candidate.
    *   **Action:** The core audio-to-answer loop runs continuously.

### **High-Level Architecture**

This diagram visualizes the modular architecture.

```mermaid
graph TD
    subgraph User's Desktop
        A[User's Physical Monitor]
        B[Screen Sharing Software e.g., Teams, Zoom]
    end

    subgraph Aura Application
        subgraph Frontend (pywebview - HTML/JS/CSS)
            C(UI: Onboarding, Transcript, AI Answer)
            D(Media: System Audio Capture)
            E(Comms: WebSocket Client)
        end

        subgraph Backend (Python/FastAPI)
            F(API: WebSocket Server)
            G[Service: STT - Deepgram]
            H[Service: LLM - Groq]
            I[Core: Config, Prompts]
            J[Desktop: Window Manager]
        end
    end

    A -- "Sees App Normally" --> C
    B -- "Sees a Black Window" --> C
    C <-->|User Input| E
    D -- "Audio Chunks" --> E
    E <-->|WebSocket Protocol| F
    F -- "Transcribe" --> G
    F -- "Generate Answer" --> H
    F -- "Get Config/Prompts" --> I
    J -- "SetWindowDisplayAffinity" --> C
```

### **Development Phases**

**Phase 0: Core Risk Validation (Proof of Concept)**
*   **Goal:** To confirm the most critical and platform-dependent feature works before we write any other code.
*   **Tasks:** Create a minimal Python script using `pywebview` and `win32gui` to create a window and apply `SetWindowDisplayAffinity`. Manually test if screen sharing software sees a black window.
*   **Rationale:** This de-risks the entire project.

**Phase 1: Foundational Structure**
*   **Goal:** Build the skeleton of the application based on the modular design.
*   **Tasks:** Set up the Python backend project structure (`api/`, `services/`, `core/`, `desktop/`), the FastAPI server, the basic WebSocket endpoint, and the `web/` directory with a basic HTML/JS frontend capable of a simple WebSocket connection.

**Phase 2: Live Interview Implementation**
*   **Goal:** Implement the core real-time functionality of the application in a modular and scalable way. This phase is broken down into four sub-phases to manage complexity.

---
**Phase 2a: Core Audio Pipeline & Diarization**
*   **Objective:** Establish a robust, modular pipeline for capturing and processing dual audio streams (candidate microphone + interviewer system audio) with speaker diarization. This is the most technically complex part and is tackled first.
*   **Key Tasks:**
    *   **Frontend Audio Module (`web/js/audio_handler.js`):** Create a new module to handle all audio capture logic (mic and system).
    *   **Backend WebSocket Refactor (`api/websocket.py`):** Refactor the WebSocket handler to support dual audio streams.
    *   **Deepgram Diarization (`services/stt_service.py`):** Enable and configure Deepgram's Diarization feature to distinguish between speakers.

**Phase 2b: AI Response Generation & Prompt Engineering**
*   **Objective:** Generate AI responses based on the interviewer's speech, using a clean and maintainable prompt management system.
*   **Key Tasks:**
    *   **Prompt Engineering Module (`core/prompts.py`):** Create a new, dedicated module to store and construct all AI prompts, keeping them separate from application logic.
    *   **Modular LLM Service (`services/llm_service.py`):** Refactor the LLM service to be more generic, receiving fully-formed prompts.
    *   **Transcript Processing:** Implement logic to identify the interviewer's speech from the diarized transcript.

**Phase 2c: Modular Live Interview UI**
*   **Objective:** Build a modular and reusable UI for the live interview view.
*   **Key Tasks:**
    *   **Live UI Component (`web/js/live_ui.js`):** Create a new module responsible for all DOM manipulations on the live screen (displaying transcripts, suggestions, etc.).
    *   **Main Controller (`web/js/main.js`):** Use the main JS file as a controller to orchestrate WebSocket events and UI updates.
    *   **HTML & CSS:** Update HTML and add scoped, modular CSS for the new UI elements.

**Phase 2d: Contextual Enhancement & Finalization**
*   **Objective:** Enhance the AI with full context and add final touches like error handling and performance tuning.
*   **Key Tasks:**
    *   **Context Aggregation:** Implement logic to gather all context (resume, job desc, conversation history) to create rich prompts for the LLM.
    *   **System Hardening:** Implement comprehensive error handling, add UI status indicators, and perform latency testing and optimization.

---
**Phase 3: Advanced Features & Polishing**
*   **Goal:** Build out secondary features that enhance the user experience.
*   **Tasks:**
    *   Code snippet display with syntax highlighting.
    *   Session summary and export feature.
    *   Settings panel for user configuration.

**Phase 4: Production & Deployment**
*   **Goal:** Prepare the application for distribution.
*   **Tasks:**
    *   Add comprehensive unit and integration tests.
    *   Use PyInstaller to package the application into a single `.exe` file.
    *   Create a simple installer and documentation.

---
### **Important Considerations**

*   **Cross-Platform Compatibility**: The core `SetWindowDisplayAffinity` API is **Windows-specific**. Achieving the same "stealth" functionality on macOS and Linux is a significant challenge. Development will focus exclusively on **Windows first**.