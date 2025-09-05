# Colliers - Paralegal

AI-powered legal contract analysis system for construction and real estate contracts.

## Features

### Risk & Compliance Screening
- Federal regulatory compliance (OSHA, EPA, HUD)
- State-specific law analysis
- High-risk provision identification
- Data privacy compliance checks

### Clause Variance & Benchmarking
- Standard vs non-standard clause detection
- Contract comparison and outlier identification
- Gap analysis across agreements
- Risk pattern recognition

### Operational Risk Analysis
- Performance obligation assessment
- Dependency tracking
- Change management evaluation
- Scope creep potential identification

### Financial & Commercial Terms
- Payment milestone analysis
- Penalty and liquidated damages assessment
- Profitability risk evaluation
- Warranty period analysis

### Governance & Dispute Resolution
- Jurisdiction analysis
- Arbitration/mediation clause review
- Escalation process evaluation
- Notice requirement tracking

## Risk Visualization

The system provides a comprehensive risk heatmap with three levels:
- 🔴 **Red**: High risk - Potential compliance/legal exposure
- 🟡 **Amber**: Medium risk - Needs legal review
- 🟢 **Green**: Low risk - Standard provisions

## Tech Stack

- **Backend**: FastAPI with Python
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL
- **LLM Integration**: Azure OpenAI / OpenAI / Anthropic
- **Infrastructure**: Docker + Traefik (SSL handled automatically)

## Deployment

The application is deployed at: https://legal-colliers.dev.morphing.ai

### Quick Start

1. Clone the repository
2. Copy `.env.template` to `.env` and configure
3. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Architecture

- Microservices architecture with separate frontend and backend
- PostgreSQL for document and analysis storage
- Rule-based analysis engine with LLM augmentation
- RESTful API with comprehensive documentation
- Real-time contract analysis and risk assessment

## Security

- Clerk authentication integration
- SSL/TLS via Traefik
- Environment-based configuration
- Secure document handling

## License

Copyright © Morphing AI - All Rights Reserved