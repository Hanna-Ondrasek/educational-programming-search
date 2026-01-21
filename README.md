# Children/Family Event & Program Finder (In Progress)

This project is an in-progress children/family event and program finder built on a cloud-native, serverless architecture. The system is designed to ingest event data from email/newsletter-style feeds, extract structured event metadata from unstructured text using foundation models, and serve searchable results via a REST API backed by DynamoDB.

This repository is currently private and under active development. Documentation reflects the intended completed system and may change as implementation evolves.

---

## What this will do when completed

When finished, the system will:

- Ingest event and program listings from email-based feeds (newsletters and similar sources)
- Parse and classify unstructured content into structured event records (title, date, age range, location, links, etc.)
- Store normalized event objects in a scalable, low-latency database
- Provide REST endpoints for querying and filtering events by constraints such as:
  - Age range
  - Location / city / radius
  - Date range
  - Category (library events, museum programs, camps, etc.)
  - Cost (free vs paid) when available
- Support deduplication and update behavior across recurring newsletter sends

---

## Core idea / motivation

A lot of high-quality kids/family programming is distributed through newsletters and email lists, which makes it hard to search or filter. This project focuses on converting those unstructured feeds into structured, queryable event data so families can find relevant programs quickly.

---

## Architecture (planned / in progress)

High-level flow:

1. **Ingestion**
   - Serverless functions ingest incoming newsletter content (e.g., scheduled pulls or feed-forwarding entrypoint)

2. **Extraction + classification**
   - A foundation model processes the raw text and extracts structured fields such as:
     - Event name
     - Date/time (when present)
     - Age range
     - Location
     - URL(s)
     - Category tags
   - Additional validation/cleanup normalizes fields (dates, locations, age ranges)

3. **Storage**
   - Events are stored in **DynamoDB** for scalable, low-latency reads
   - Records include keys/indices optimized for filtering by time and location (exact schema in progress)

4. **Serving**
   - RESTful endpoints provide search/filter functionality for clients

---

## Data model (intended)

Example event fields (subject to change):

- `eventId`
- `title`
- `description`
- `source`
- `startDateTime` / `endDateTime`
- `ageRangeMin` / `ageRangeMax`
- `locationName`
- `city` / `state`
- `url`
- `tags`
- `cost`
- `lastSeenAt` (for feed updates)

---

## Current status

- Serverless ingestion pipeline design in progress
- Foundation-model-based extraction pipeline implemented/iterating
- DynamoDB storage and query patterns being refined
- REST API endpoints under development

---

## Planned improvements

- Better date/time extraction and normalization across formats
- Stronger deduplication for repeated/forwarded listings
- Location normalization (geocoding, consistent city/state fields)
- Ranking and recommendation (e.g., “nearby this weekend”)
- Admin review interface for low-confidence extractions
- Observability: logging/metrics/tracing and failure handling

---

## Tech stack (current / intended)

- AWS Lambda (serverless ingestion and processing)
- DynamoDB (event storage)
- GCP services (used where appropriate during processing / model workflow)
- Foundation models for metadata extraction from unstructured newsletter content
- RESTful backend services

---

## Notes

This project is not yet released publicly. This README is written to reflect the intended final functionality and will be updated as implementation stabilizes.
