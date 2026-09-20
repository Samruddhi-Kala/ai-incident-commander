# Incident Postmortem: INC-2025-08-01

**Incident ID**: `INC-2025-08-01`  
**Affected Service**: `payment-service`  
**Severity**: `SEV-1`  
**Duration**: 24 minutes  

---

## Root Cause
Deployment `v2.1.0` reduced the HTTP client timeout for downstream gateway calls from `5000ms` to `500ms`. Under normal load, network jitter caused gateway responses taking ~600ms to be cancelled as timeouts, causing payment failure rates to jump to 18%.

## Mitigation Action
Rolled back `payment-service` deployment from `v2.1.0` to `v2.0.9`. Error rates returned to normal baseline (< 0.2%) within 2 minutes.
