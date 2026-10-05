"""
Git Tool Adapter (Simulated V1)

Provides simulated diagnostic tools for querying recent commits,
commit details, and searching code changes.
Tools: get_recent_commits, get_commit_details, search_code_changes
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.tools.base import BaseToolAdapter


# ---------------------------------------------------------------------------
# Simulated git data — deterministic per service_name
# ---------------------------------------------------------------------------

_COMMITS = {
    "payment-service": [
        {
            "sha": "a1b2c3d4e5f6",
            "short_sha": "a1b2c3d",
            "author": "alice@company.com",
            "author_name": "Alice Chen",
            "message": "feat: integrate new payment processor gateway",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            "files_changed": [
                "src/handlers/payment_handler.py",
                "src/clients/payment_gateway.py",
                "config/payment-gateway.yml",
                "tests/test_payment_handler.py",
            ],
            "insertions": 98,
            "deletions": 12,
            "branch": "main",
        },
        {
            "sha": "b2c3d4e5f6a1",
            "short_sha": "b2c3d4e",
            "author": "alice@company.com",
            "author_name": "Alice Chen",
            "message": "fix: increase connection pool size to handle peak load",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=35)).isoformat(),
            "files_changed": [
                "config/database.yml",
                "src/db/connection_pool.py",
            ],
            "insertions": 15,
            "deletions": 3,
            "branch": "main",
        },
        {
            "sha": "c3d4e5f6a1b2",
            "short_sha": "c3d4e5f",
            "author": "bob@company.com",
            "author_name": "Bob Kumar",
            "message": "chore: upgrade payment-sdk from v3.2.0 to v4.0.0",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=40)).isoformat(),
            "files_changed": [
                "requirements.txt",
                "src/clients/payment_sdk_wrapper.py",
            ],
            "insertions": 29,
            "deletions": 22,
            "branch": "main",
        },
        {
            "sha": "d4e5f6a1b2c3",
            "short_sha": "d4e5f6a",
            "author": "carol@company.com",
            "author_name": "Carol Zhang",
            "message": "docs: update runbook for payment service troubleshooting",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
            "files_changed": [
                "docs/runbooks/payment-service.md",
            ],
            "insertions": 45,
            "deletions": 8,
            "branch": "main",
        },
        {
            "sha": "e5f6a1b2c3d4",
            "short_sha": "e5f6a1b",
            "author": "alice@company.com",
            "author_name": "Alice Chen",
            "message": "test: add integration tests for payment flow timeout scenarios",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
            "files_changed": [
                "tests/integration/test_payment_flow.py",
                "tests/fixtures/payment_fixtures.py",
            ],
            "insertions": 120,
            "deletions": 0,
            "branch": "main",
        },
    ],
    "auth-service": [
        {
            "sha": "abc123def456",
            "short_sha": "abc123d",
            "author": "dave@company.com",
            "author_name": "Dave Park",
            "message": "feat: implement OAuth2 PKCE flow",
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "files_changed": [
                "src/auth/oauth2_pkce.py",
                "src/auth/token_handler.py",
                "tests/test_oauth2.py",
            ],
            "insertions": 250,
            "deletions": 30,
            "branch": "main",
        },
    ],
    "gateway-service": [
        {
            "sha": "789abc012def",
            "short_sha": "789abc0",
            "author": "carol@company.com",
            "author_name": "Carol Zhang",
            "message": "fix: update rate limiting configuration for API gateway",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
            "files_changed": [
                "src/middleware/rate_limiter.py",
                "config/rate-limits.yml",
            ],
            "insertions": 18,
            "deletions": 5,
            "branch": "main",
        },
    ],
}


def _get_default_commits(service_name: str) -> List[Dict[str, Any]]:
    """Return default commit history for unknown services."""
    return [{
        "sha": "000aaa111bbb",
        "short_sha": "000aaa1",
        "author": "dev@company.com",
        "author_name": "Developer",
        "message": "initial commit",
        "timestamp": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        "files_changed": ["README.md"],
        "insertions": 10,
        "deletions": 0,
        "branch": "main",
    }]


# Simulated diff content for key commits
_DIFFS = {
    "a1b2c3d4e5f6": {
        "src/handlers/payment_handler.py": (
            "--- a/src/handlers/payment_handler.py\n"
            "+++ b/src/handlers/payment_handler.py\n"
            "@@ -140,6 +140,15 @@ class PaymentHandler:\n"
            "     def process_transaction(self, transaction):\n"
            "-        result = self.legacy_gateway.charge(transaction)\n"
            "+        # Route to new payment processor\n"
            "+        if self.config.use_new_processor:\n"
            "+            result = self.new_gateway.charge(transaction)\n"
            "+        else:\n"
            "+            result = self.legacy_gateway.charge(transaction)\n"
            "+        if result is None:\n"
            "+            raise PaymentProcessingError(\n"
            "+                f'Null response from payment processor for txn {transaction.id}'\n"
            "+            )\n"
            "         return result\n"
        ),
        "config/payment-gateway.yml": (
            "--- a/config/payment-gateway.yml\n"
            "+++ b/config/payment-gateway.yml\n"
            "@@ -1,4 +1,8 @@\n"
            " payment_gateway:\n"
            "-  provider: legacy-gateway\n"
            "-  timeout_ms: 5000\n"
            "+  provider: new-payment-processor\n"
            "+  timeout_ms: 30000\n"
            "+  use_new_processor: true\n"
            "+  new_processor_url: https://api.newprocessor.com/v2\n"
            "+  retry_count: 3\n"
            "+  circuit_breaker_threshold: 5\n"
        ),
    },
    "b2c3d4e5f6a1": {
        "config/database.yml": (
            "--- a/config/database.yml\n"
            "+++ b/config/database.yml\n"
            "@@ -3,3 +3,5 @@\n"
            " database:\n"
            "   host: db.internal.company.com\n"
            "-  connection_pool_size: 20\n"
            "+  connection_pool_size: 50\n"
            "+  connection_pool_overflow: 10\n"
            "+  pool_timeout: 30\n"
        ),
    },
}


class GitAdapter(BaseToolAdapter):
    """
    Simulated Git adapter providing commit history queries,
    commit detail lookups, and code change searches.
    """

    @property
    def domain(self) -> str:
        return "git"

    @property
    def tools(self) -> List[str]:
        return ["get_recent_commits", "get_commit_details", "search_code_changes"]

    def get_recent_commits(
        self,
        service_name: str,
        limit: int = 10,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Retrieve recent git commits for a service repository.

        Args:
            service_name: Target service name.
            limit: Maximum number of commits to return.
            branch: Branch to query.

        Returns:
            Dict with commit records, count, and repository info.
        """
        commits = _COMMITS.get(service_name, _get_default_commits(service_name))
        filtered = [c for c in commits if c.get("branch") == branch][:limit]
        return {
            "service_name": service_name,
            "branch": branch,
            "total_commits": len(filtered),
            "commits": filtered,
        }

    def get_commit_details(
        self,
        sha: str,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific commit including diffs.

        Args:
            sha: Full or short commit SHA hash.

        Returns:
            Dict with commit details, files changed, and diff content.
        """
        # Search across all services
        for service_commits in _COMMITS.values():
            for commit in service_commits:
                if commit["sha"] == sha or commit["short_sha"] == sha:
                    diff = _DIFFS.get(commit["sha"], {})
                    return {
                        **commit,
                        "diff": diff,
                        "diff_available": bool(diff),
                    }

        return {
            "error": f"Commit '{sha}' not found",
            "sha": sha,
        }

    def search_code_changes(
        self,
        service_name: str,
        query: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Search code changes (commit messages and file paths) for matching patterns.

        Args:
            service_name: Target service name.
            query: Search query to match against commit messages and file paths.
            limit: Maximum number of results.

        Returns:
            Dict with matching commits and relevance context.
        """
        commits = _COMMITS.get(service_name, _get_default_commits(service_name))
        results = []
        query_lower = query.lower()

        for commit in commits:
            match_in_message = query_lower in commit["message"].lower()
            matching_files = [
                f for f in commit["files_changed"]
                if query_lower in f.lower()
            ]
            if match_in_message or matching_files:
                results.append({
                    **commit,
                    "match_reason": "message" if match_in_message else "file_path",
                    "matching_files": matching_files if matching_files else [],
                })

        return {
            "service_name": service_name,
            "query": query,
            "total_results": len(results[:limit]),
            "results": results[:limit],
        }
