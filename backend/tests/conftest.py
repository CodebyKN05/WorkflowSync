import os
import pytest

# Inject test database URL before any application components are imported
test_db_url = os.environ.get("TEST_DATABASE_URL")
if not test_db_url:
    # Use default URL pattern to determine test URL
    default_url = "postgresql://user:password@localhost:5432/workflowsync"
    test_db_url = default_url.replace("workflowsync", "workflowsync_test")

os.environ["DATABASE_URL"] = test_db_url
