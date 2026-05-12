# Architecture Decision Record

## Decision

The project will use EXTENDED conversational domain model.

The canonical source of truth is:

* Prisma schema
* aligned with conversational workflow architecture

The system is NOT a CRUD salon backend.

The system IS:

* conversational orchestration platform
* AI-assisted consultation system
* CRM communication platform

---

# Canonical Entities

## Core

* Client
* Dialog
* Message
* Booking

## Conversational Workflow

* Scenario
* DialogState

## Future Extensions

* AIContext
* RetentionEvent
* ClientProfile
* ReminderJob

---

# Why Scenario is required

Scenario represents:

* consultation flow
* communication strategy
* workflow type

Examples:

* hair_coloring
* haircut
* retention
* consultation
* upsell
* reactivation

AI orchestration depends on Scenario.

Scenario is mandatory.

---

# Why DialogState is required

Dialog.currentStage stores ONLY current state.

DialogState stores:

* workflow transition history
* analytics
* debugging
* AI memory
* quality control

Examples:
DISCOVERY
→ PRESENTATION
→ OBJECTION
→ BOOKING

DialogState is mandatory.

---

# Architecture Principle

Business workflow MUST NOT depend on AI.

Backend controls:

* workflow
* transitions
* validation
* orchestration

AI only:

* personalizes communication
* adapts tone
* humanizes responses

---

# Final Decision

We DO NOT reduce architecture
to 4 entities.

We RESTORE and STABILIZE:

* Scenario
* DialogState

as first-class domain entities.
