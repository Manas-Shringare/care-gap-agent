# Roadmap

Status reflects actual implementation progress, updated as each phase ships.

## MVP

- [ ] Prompt execution (`/invoke`)
- [ ] Bedrock integration
- [ ] Request logging (structured JSON)
- [ ] Latency tracking
- [ ] Metadata persistence (DynamoDB)
- [ ] Request retrieval (`GET /requests/{request_id}`)
- [ ] User feedback (`POST /feedback/{request_id}`)
- [ ] Docker containerization
- [ ] AWS App Runner deployment

## Phase 2 (Post-MVP)

- CloudWatch metrics
- Prompt versioning
- Observability dashboard
- Authentication

## Phase 3 (Post-MVP)

- Evaluation framework
- Guardrails integration
- Model comparison
- Distributed tracing
- CloudWatch dashboards

## Future Vision

- Full LLMOps platform
- Governance reporting
- Production monitoring at scale