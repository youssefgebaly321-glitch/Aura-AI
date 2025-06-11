# Backend Refactoring Plan: Achieving a Fully Asynchronous Architecture

## Objective: Transition to a Fully Asynchronous, High-Performance Backend

The goal is to eliminate all blocking I/O operations from the application's event loop. This will make the server highly responsive, especially under real-time loads, by allowing it to handle concurrent tasks (like new user speech or API calls) without getting stuck.

---

## The Plan: A Phased Approach

The implementation will be done in a series of focused phases to ensure stability and proper error handling at each step.

### Phase 1: Foundational Library Upgrades

This phase lays the groundwork by introducing the necessary asynchronous libraries.

1.  **Introduce High-Performance JSON (`orjson`):**
    *   **What:** Replace the standard `json` library with `orjson` for faster serialization/deserialization.
    *   **Where:** Modify `api/utils.py` to use `orjson.dumps()` and `websocket.send_bytes`. Update `main.py` and other service files that use the `json` library.
    *   **Why:** This is a simple, low-risk change that provides an immediate performance boost for all WebSocket communication.

2.  **Introduce Asynchronous HTTP Client (`httpx`):**
    *   **What:** Add `httpx` to the project as the primary library for making asynchronous HTTP requests to external APIs.
    *   **Where:** This library will be used in `services/llm_service.py` and `services/vision_service.py` to replace the blocking `openai` library calls.
    *   **Why:** `httpx` is a modern, fully-featured async HTTP client that is a direct replacement for `requests` and is compatible with the `async/await` syntax we need.

3.  **Introduce Asynchronous File I/O (`aiofiles`):**
    *   **What:** Add `aiofiles` to handle file system operations without blocking the event loop.
    *   **Where:** This will be used in the `GlobalCommandMonitor` class in `main.py` to replace `os.path.exists`, `os.path.getmtime`, and `os.remove`.
    *   **Why:** This ensures that even file system checks for global commands do not introduce latency into the application.

---

### Phase 2: Refactoring the Service Layer

This is the most critical phase, where we will convert the core application logic to be fully asynchronous.

1.  **Convert `LLMService` to be Fully Asynchronous:**
    *   **What:** Refactor the `get_ai_answer` method and its helpers in `services/llm_service.py` to use `httpx` for all API calls.
    *   **How:**
        *   Create a single, reusable `httpx.AsyncClient` instance for the application to manage connections efficiently.
        *   Convert the API call logic to use `async with client.stream(...)` for streaming responses.
        *   Ensure all methods in the call chain are `async def`.
        *   Implement robust error handling for network issues, timeouts, and API errors.

2.  **Convert `VisionService` to be Fully Asynchronous:**
    *   **What:** Refactor the `analyze_screenshots` method in `services/vision_service.py` to use the same `httpx.AsyncClient`.
    *   **How:** This will follow the same pattern as the `LLMService` refactoring, ensuring that vision analysis calls are also non-blocking.

---

### Phase 3: Refactoring the Application Core

This phase focuses on the application's entry point and top-level concurrency model.

1.  **Refactor `GlobalCommandMonitor` in `main.py`:**
    *   **What:** Convert the `_monitor_loop` in `main.py` from a thread-based loop to a native `asyncio` task.
    *   **How:**
        *   Replace `time.sleep()` with `await asyncio.sleep()`.
        *   Use `aiofiles` for all file operations.
        *   The monitoring loop will become an `async def` method.

2.  **Convert Top-Level Concurrency to `asyncio`:**
    *   **What:** Refactor the application startup in `main.py` to use a unified `asyncio` event loop instead of a separate `threading.Thread` for the Uvicorn server.
    *   **How:**
        *   Create a main `async def main()` function.
        *   Use `asyncio.create_task()` to run the Uvicorn server, the `GlobalCommandMonitor`, and the `pywebview` event loop as concurrent tasks.
        *   This creates a more modern, efficient, and easier-to-manage concurrency model.

---

### Diagram of Proposed Architecture

This diagram illustrates the "after" state, where all I/O operations are non-blocking.

```mermaid
graph TD
    subgraph "Main Application (asyncio Event Loop)"
        A[Uvicorn Server]
        B[Global Command Monitor]
        C[pywebview UI]
    end

    subgraph "WebSocket Endpoint (api/websocket.py)"
        D[on_receive]
    end
    
    subgraph "Service Layer (Non-Blocking)"
        E[LLM Service]
        F[Vision Service]
    end

    subgraph "External I/O"
        G[LLM/Vision APIs]
        H[File System]
    end

    A <--> D
    B -- Non-Blocking Check --> H
    D -- await --> E
    D -- await --> F
    E -- Non-Blocking Request --> G
    F -- Non-Blocking Request --> G