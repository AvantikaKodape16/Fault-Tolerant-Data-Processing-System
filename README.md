# Fault Tolerant Data Processing

## Overview
This project aims to develop a fault-tolerant data processing system that ensures reliability and availability in data workloads. The architecture is designed to handle failures gracefully, ensuring that data integrity is preserved even in adverse conditions.

------
## Tech Stack

**Backend:** Python 3.8+, Flask 2.3, SQLAlchemy 2.0  
**Frontend:** HTML5, CSS3, Vanilla JavaScript  
**Database:** SQLite (dev), PostgreSQL-ready  
**Libraries:** python-dateutil, Pydantic (optional), Flask-CORS
------

## Key Sections Highlighted:

✅ **Quick start** - Get running in 3 commands

✅ **Architecture** - Visual overview of data flow

✅ **Three critical questions answered:**
   - How prevents double counting
   - What happens if DB fails
   - What breaks at scale
     
✅ **API examples** - Copy-paste ready requests

✅ **Configuration** - How to add new clients

✅ **Testing guide** - Verify deduplication works

✅ **Database schema** - What data lives where

✅ **Future improvements** - What's next

✅ **Assumptions** - What we rely on

----

## Architecture Overview

The architecture of the fault-tolerant data processing system is based on a microservices approach:

- Service A: Responsible for ingestion of data. It can process streams of events and write them to a persistent store.
- Service B: Handles business logic and transformation of data, implementing retries and fallbacks to ensure fault tolerance.
- Service C: Responsible for storing processed data and making it available for querying.
- Each service is independently deployed, allowing scaling and fault isolation. Using technologies like Kafka for messaging and PostgreSQL for storage provides robust durability and reliability.

-----

## Key Design Decisions

- Decoupled Services: Services communicate over a messaging queue, allowing for easier scaling and reduced dependency between components.
- Retries and Circuit Breakers: Implementing retry logic with exponential backoff and circuit breakers ensures that transient failures do not cascade throughout the system.
- Monitoring and Logging: Integrated monitoring solutions provide real-time visibility into system health and allow for proactive issue detection.
- Data Consistency: Using ACID-compliant databases ensures that data integrity is maintained even in the event of failures.

-----
## Conclusion

This document serves as a guide to understand the setup, architecture, and major design choices for the fault-tolerant data processing system. For further details, please explore the code and additional resources provided in this repository.
