# System Architecture Overview

## Service Topology
The platform consists of microservices handling e-commerce order workflows:

```
[ API Gateway ] ──► [ Auth Service ]
       │
       ├──► [ Order Service ] ──► [ Payment Service ] ──► [ Stripe API ]
       │                                  │
       │                                  ▼
       └────────────────────────► [ Database Cluster ]
```

## Critical Dependencies
* `payment-service` depends on `database-cluster` (PostgreSQL) and `auth-service` (JWT validation).
* `order-service` calls `payment-service` via gRPC / HTTP REST endpoints.
