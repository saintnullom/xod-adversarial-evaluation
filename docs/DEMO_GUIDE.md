# Demo Guide

## Purpose

This guide demonstrates the local prototype's reasoning workflow. It is not a scientific demonstration, benchmark result, or production readiness test.

## Setup

1. From the repository root, create the virtual environment and install backend requirements as shown in [README.md](../README.md).
2. Create a private `.env.local` from `.env.example` and configure a provider only if live model-backed SPAR/Tribunal output is desired.
3. Start the backend from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000 --env-file .\.env.local
   ```

4. In a second terminal, start the frontend:

   ```powershell
   cd frontend
   npm.cmd run dev
   ```

5. Open the local frontend URL reported by Vite, normally `http://127.0.0.1:5173`.

## Synthetic prototype walkthrough

Screenshots show a synthetic demonstration of the current local prototype. They are not benchmark results or scientific validation.

The demonstrated sequence is user-triggered: synthetic proposition → SPAR → Tribunal → structured adversarial evaluation → optional **Save as Belief** → persistent Belief Ledger → deterministic self-critique evaluation.

XOD does not autonomously initiate a second SPAR question, change user confidence, add evidence, add predictions, retrieve external literature, or scientifically verify the synthetic dark-chocolate proposition. The Tribunal's recommended confidence range remains distinct from the user-recorded confidence in the Belief Ledger.

See [PROTOTYPE_WALKTHROUGH.md](PROTOTYPE_WALKTHROUGH.md) for all supplied screenshots and their capability boundaries.

## Synthetic reference

Use [examples/sample_evaluation.md](../examples/sample_evaluation.md) as a safe fictional walkthrough. It separates claim, evidence, assumption, objection, contradictory information, evaluation status, uncertainty, and human review.

## Screenshot review boundary

The supplied screenshots are synthetic and show no credentials, tokens, personal information, private URLs, or development errors. `localhost:5173` is acceptable local-demo context. Before a future publication, review all images again for browser tabs, account details, local paths, and accidental private data.
