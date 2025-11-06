# TenderIQ Real-Time Analysis Roadmap

This document outlines the development plan for implementing the real-time, SSE-based tender analysis feature.

**Status Legend:**
- `[ ] To Do`
- `[x] Done`
- `[-] Rejected / Won't Do`

---

## Part 1: Infrastructure Setup (Global)

These tasks involve setting up the core infrastructure that the real-time analysis will depend on.

-   **[x] Integrate Redis**
    -   **Goal:** Add Redis configuration and a shared client for the application.
    -   **Tasks:**
        -   `[x]` Add Redis connection settings (`REDIS_HOST`, `REDIS_PORT`) to `app/config.py`.
        -   `[x]` Create a Redis client utility (e.g., `app/db/redis_client.py`) to provide a reusable connection pool.
        -   `[x]` Add the `redis` and `hiredis` packages to your project dependencies.

-   **[x] Integrate Celery**
    -   **Goal:** Set up an application-wide task queue for background processing.
    -   **Tasks:**
        -   `[x]` Add Celery broker and result backend URLs (using Redis) to `app/config.py`.
        -   `[x]` Create a global Celery app instance (e.g., `app/celery_app.py`) that discovers tasks from all modules.
        -   `[x]` Add `celery` and `redis` (as a broker) to your project dependencies.

---

## Part 2: TenderIQ Analysis Backend

This part focuses on building the background task that performs the analysis and publishes updates.

-   **[ ] Create the Main Analysis Task**
    -   **Goal:** Create a Celery task that orchestrates the entire analysis process.
    -   **Tasks:**
        -   `[ ]` Create `app/modules/tenderiq/analyze/tasks.py`.
        -   `[ ]` Define a Celery task `run_tender_analysis(analysis_id)` that will serve as the main entry point.
        -   `[ ]` This task will be responsible for calling all the sub-services (parsing, one-pager, etc.) in the correct order.

-   **[ ] Implement Progress Publishing**
    -   **Goal:** Enable the Celery task to broadcast real-time updates.
    -   **Tasks:**
        -   `[ ]` Create a utility function that takes an `analysis_id` and a data payload, and publishes it to a Redis Pub/Sub channel (e.g., `analysis:{analysis_id}`).
        -   `[ ]` The Celery task will call this function at the beginning and end of each step (e.g., publish a "pending" status, then the final result for the one-pager).

-   **[ ] Build Analysis Sub-Services**
    -   **Goal:** Create modular services for each part of the analysis.
    -   **Tasks:**
        -   `[ ]` **Document Parsing Service:** A service that reuses `askai`'s `PDFProcessor` to extract text and save it to the vector store.
        -   `[ ]` **One-Pager Service:** A service that queries the LLM to generate the one-pager data and saves it to the `TenderAnalysis` table.
        -   `[ ]` **Scope of Work Service:** A service that queries the LLM for scope of work data.
        -   `[ ]` **RFP Section Service:** A service that queries the LLM for RFP section data.
        -   `[ ]` **Data Sheet Service:** A service that queries the LLM for data sheet information.

---

## Part 3: TenderIQ Analysis API Endpoint

This part involves creating the user-facing endpoint that streams the analysis results.

-   **[ ] Create the SSE Endpoint**
    -   **Goal:** Develop the `GET /tenderiq/analyze/{tender_id}` endpoint.
    -   **Tasks:**
        -   `[ ]` Create `app/modules/tenderiq/analyze/endpoints/endpoints.py` and define the route.
        -   `[ ]` Implement the endpoint logic:
            1.  On a new connection, check the database for an existing `TenderAnalysis` record.
            2.  If the record doesn't exist, create one and trigger the `run_tender_analysis` Celery task.
            3.  Immediately stream any data already in the database record to the client.
            4.  Subscribe to the Redis Pub/Sub channel for the analysis.
            5.  Listen for new messages and stream them to the client as SSE events.

-   **[ ] Define SSE Event Models**
    -   **Goal:** Standardize the format of the messages sent over the stream.
    -   **Tasks:**
        -   `[ ]` Create Pydantic models in `app/modules/tenderiq/analyze/models/pydantic_models.py` to define the structure of the SSE events (e.g., `{ "event": "update", "field": "one_pager.project_overview", "data": "..." }`).
