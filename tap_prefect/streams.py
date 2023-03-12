"""Stream type classes for tap-prefect."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar
from typing import Optional

from tap_prefect.client import prefectStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

_TToken = TypeVar("_TToken")


class FlowRunStream(prefectStream):
    """Define custom stream."""

    name = "flow_runs"
    rest_method = "POST"

    @property
    def path(self):
        return f"/accounts/{self.config['account_id']}/workspaces/{self.config['workspace_id']}/flow_runs/filter"

    primary_keys = ["id"]
    replication_key = "expected_start_time"
    schema_filepath = SCHEMAS_DIR / "flow_runs.json"

    def prepare_request_payload(
        self, context: dict | None, next_page_token: _TToken | None
    ) -> dict | None:
        """Prepare the data payload for the REST API request.
        By default, no payload will be sent (return None).
        Developers may override this method if the API requires a custom payload along
        with the request. (This is generally not required for APIs which use the
        HTTP 'GET' method.)

        Args:
            context: Stream partition or context dictionary.
            next_page_token: Token, page number or any request argument to request the
                next page of data.

        Returns:
            Dictionary with the body to use for the request.
        """

        starting_date = self.get_starting_replication_key_value(context)

        params = {
            "sort": "EXPECTED_START_TIME_ASC",
            "offset": next_page_token,
            "limit": 5,
            "flow_runs": {"expected_start_time": {"after_": starting_date}},
        }

        return params

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "flow_id": record["id"]
        }


class TaskRunSubStream(prefectStream):
    name = "task_runs"

    rest_method = "POST"
    parent_stream_type = FlowRunStream
    ignore_parent_replication_key = True
    primary_keys = ["id"]
    schema_filepath = SCHEMAS_DIR / "task_runs.json"

    @property
    def path(self):
        return f"/accounts/{self.config['account_id']}/workspaces/{self.config['workspace_id']}/task_runs/filter"

    def prepare_request_payload(
        self, context: dict | None, next_page_token: _TToken | None
    ) -> dict | None:
        """Prepare the data payload for the REST API request.

        Args:
            context: Stream partition or context dictionary.
            next_page_token: Token, page number or any request argument to request the
                next page of data.

        Returns:
            Dictionary with the body to use for the request.
        """
        flow_id = context.get("flow_id")

        params = {
            "sort": "EXPECTED_START_TIME_ASC",
            "offset": next_page_token,
            "limit": 5,
            "flow_runs": {
                "id": {
                    "any_": [flow_id]
                }
            },
        }

        return params

