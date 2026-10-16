# 38. Point-in-time retrieval

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime

## Status

Accepted

Amended by [44. Minimum technology stack](0044-minimum-technology-stack.md)

## Decision

Point-in-time retrieval (MLE 1.2) needs no change to the dataset model. Event time is carried by event-time metadata on datasets ([D12](0012-streaming-readiness.md) Seam 6). Knowledge time — when the platform learned of a value — comes from a dataset's publication history, since every snapshot has a commit time ([D15](0015-atomic-publication.md)), or from a row-level ingestion timestamp written at extraction, which is standard practice.

- **Point-in-time join.** A palette node matches each label to the feature values whose event time and knowledge time both precede the label time.
- **Limit.** As-of accuracy at version level reaches back only as far as retained snapshot history ([D36](0036-data-engineering-practice-first-reproducibility-by-choice.md)); a row-level ingestion timestamp avoids that limit. As-of queries are answered only for times older than the commit watermark ([D42](0042-catalog-persistence.md)).
- **Ingestion column.** Added by [D44](0044-minimum-technology-stack.md): a dataset partitioned by ingestion time has the ingestion time written as a column at extraction, since partition keys are stored as columns. Whether extraction stamps one on other datasets by default remains open.

## Follow-ups

- The point-in-time join node, designed with the palette; whether extraction stamps a row-level ingestion timestamp by default on datasets not partitioned by ingestion time, where [D44](0044-minimum-technology-stack.md) already requires one.
