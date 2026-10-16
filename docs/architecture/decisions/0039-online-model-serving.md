# 39. Online model serving

Date: 2026-10-11
Applies to: platform

## Status

Accepted

## Decision

Low-latency online model endpoints are out of scope. Models are served by external serving systems; the platform covers packaging for deployment ([MLE 3.5]({workspace}/documentation#6)), batch and scheduled scoring ([MLE 4.1]({workspace}/documentation#6)), and the registry, lineage and approvals around them.
