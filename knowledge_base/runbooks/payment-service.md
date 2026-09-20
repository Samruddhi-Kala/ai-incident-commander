# Payment Service Runbook

**Service Name**: `payment-service`  
**Owner Team**: Payment Core  
**Tier**: Tier-0 (Critical)  

---

## Service Overview
The Payment Service processes all incoming user transactions via external payment gateways (Stripe / Adyen). It handles authorization, capture, and webhook processing.

---

## Common Failures & Diagnostic Steps

### 1. Elevated Payment Gateway Error Rate (> 15%)
* **Symptoms**: Error rate alerts triggered for `payment-service`. Logs contain `504 Gateway Timeout` or `HTTP 408` errors.
* **Diagnostic Steps**:
  1. Query metrics for `payment-service` error rate over the last 30 minutes.
  2. Check recent deployments using `get_recent_deployments(service="payment-service")`.
  3. Inspect commit diffs if a deployment occurred within the last 45 minutes.
  4. Verify RPC/HTTP timeout configuration in `payment-service` config. Default timeout MUST be \>= 5000ms.
* **Resolution / Mitigation**:
  * If a deployment set timeout below 1000ms, roll back deployment to the previous stable release version.
