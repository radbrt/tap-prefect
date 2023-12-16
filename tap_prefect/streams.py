"""Stream type classes for tap-prefect."""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, TypeVar
import requests
from singer_sdk import metrics
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseHATEOASPaginator, SinglePagePaginator
from tap_prefect.client import prefectStream

LOGGER = logging.getLogger(__name__)

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

_TToken = TypeVar("_TToken")


class MyHATEOASPaginator(BaseHATEOASPaginator):
    """Custom paginator."""

    def get_next_url(self, response):
        next_page = response.json().get("next_page")

        # Incredibly ugly hack to aviod what has to be a bug in the API: It seems the final page returns a
        # next_page URL that is invalid and returns a 500. This URL is much shorter than the normal ones, so we are
        # checking for this here.
        if len(next_page) < 400:
            return None
        return next_page


class MySinglePagePaginator(SinglePagePaginator):
    """Custom paginator."""

    def get_next(self, response):
        """Return next page link or None.

        Args:
            response: The HTTP response object.

        Returns:
            The next page link or None.
        """
        return None


class FlowRunStream(prefectStream):
    """Define custom stream."""

    name = "flow_runs"
    rest_method = "POST"

    @property
    def path(self):
        """Return the API endpoint path.

        Returns:
            The API endpoint path.
        """
        return f"/accounts/{self.config['account_id']}/workspaces/{self.config['workspace_id']}/flow_runs/filter"

    primary_keys = ["id"]
    # replication_key = "expected_start_time"
    schema_filepath = SCHEMAS_DIR / "flow_runs.json"

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
        starting_date = (
            self.config.get("start_date") or "2021-01-01T00:00:00.000000+00:00"
        )

        params = {
            "sort": "EXPECTED_START_TIME_ASC",
            "offset": next_page_token,
            "limit": self.PAGE_SIZE,
            "flow_runs": {"expected_start_time": {"after_": starting_date}},
        }

        return params

    # def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
    #     """Return a context dictionary for child streams."""
    #     return {
    #         "flow_id": record["id"]
    #     }


# class TaskRunSubStream(prefectStream):

#     name = "task_runs"

#     rest_method = "POST"
#     parent_stream_type = FlowRunStream
#     ignore_parent_replication_key = True
#     primary_keys = ["id"]
#     schema_filepath = SCHEMAS_DIR / "task_runs.json"
#     state_partitioning_keys = []
#     replication_key = None

#     @property
#     def partitions(self) -> dict | None:
#         """Return the partition for the stream."""
#         return []

#     @property
#     def path(self):
#         return f"/accounts/{self.config['account_id']}/workspaces/{self.config['workspace_id']}/task_runs/filter"

#     def prepare_request_payload(
#         self, context: dict | None, next_page_token: _TToken | None
#     ) -> dict | None:
#         """Prepare the data payload for the REST API request.

#         Args:
#             context: Stream partition or context dictionary.
#             next_page_token: Token, page number or any request argument to request the
#                 next page of data.

#         Returns:
#             Dictionary with the body to use for the request.
#         """
#         flow_id = context.get("flow_id")

#         params = {
#             "sort": "EXPECTED_START_TIME_ASC",
#             "offset": next_page_token,
#             "limit": self.PAGE_SIZE,
#             "flow_runs": {
#                 "id": {
#                     "any_": [flow_id]
#                 }
#             },
#         }

#         return params


class FlowsStream(prefectStream):
    name = "flows"
    rest_method = "POST"
    records_jsonpath = "$.[*]"
    primary_keys = ["id"]

    schema_filepath = SCHEMAS_DIR / "flows.json"

    def get_new_paginator(self):
        """Return a new paginator object.

        Returns:
            A new paginator object.
        """
        return MySinglePagePaginator()

    @property
    def path(self):
        """Return the API endpoint path.

        Returns:
            The API endpoint path.
        """
        return f"/accounts/{self.config['account_id']}/workspaces/{self.config['workspace_id']}/flows/filter"

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
        return None


class DeploymentsStream(prefectStream):
    name = "deployments"
    rest_method = "POST"
    primary_keys = ["id"]
    records_jsonpath = "$.[*]"
    schema_filepath = SCHEMAS_DIR / "deployments.json"

    def get_new_paginator(self):
        """Return a new paginator object.

        Returns:
            A new paginator object.
        """
        return MySinglePagePaginator()

    @property
    def path(self):
        """Return the API endpoint path.

        Returns:
            The API endpoint path.
        """
        return f"/accounts/{self.config['account_id']}/workspaces/{self.config['workspace_id']}/deployments/filter"

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

        return None


class EventStream(prefectStream):
    """Define custom stream."""

    name = "events"
    rest_method = "POST"
    records_jsonpath = "$.events[*]"

    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "events.json"

    @property
    def path(self):
        """Return the API endpoint path.

        Returns:
            The API endpoint path.
        """
        return f"/accounts/{self.config['account_id']}/workspaces/{self.config['workspace_id']}/events/filter"

    primary_keys = ["id"]
    replication_key = "occurred"
    schema_filepath = SCHEMAS_DIR / "events.json"
    next_page_token_jsonpath = None  # "$.next_page"get

    def get_new_paginator(self):
        """Return a new paginator object.

        Returns:
            A new paginator object.
        """
        return MyHATEOASPaginator()

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return next page link or None.

        Args:
            context: Comtext.
            next_page_token: The HTTP response object.

        Returns:
            The next page link or None.
        """

        return {}

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

        starting_date = self.get_starting_replication_key_value(
            context
        ) or self.config.get(
            "start_date"
        )  # "2019-08-24T14:15:22Z"

        params = {
            "limit": 50,
            "filter": {
                "occurred": {"since": starting_date},
                "event": {"exclude_name": ["prefect.log.write"]},
                "order": "ASC",
            },
        }

        if next_page_token:
            return None

        return params

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result records.

        Args:
            response: The HTTP response object.

        Yields:
            A stream record.
        """

        yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    def request_records(self, context: dict | None) -> Iterable[dict]:
        """Request records from REST endpoint(s), returning response records.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            A stream record.
        """
        paginator = self.get_new_paginator()
        decorated_request = self.request_decorator(self._request)

        with metrics.http_request_counter(self.name, self.path) as request_counter:
            request_counter.context = context

            while not paginator.finished:
                prepared_request = self.prepare_request(
                    context, next_page_token=paginator.current_value
                )

                resp = decorated_request(prepared_request, context)
                request_counter.increment()
                self.update_sync_costs(prepared_request, resp, context)
                yield from self.parse_response(resp)

                paginator.advance(resp)

    def prepare_request(
        self, context: dict | None, next_page_token
    ) -> requests.PreparedRequest:
        """Prepare a request object for this stream.

        Args:
            context: Stream partition or context dictionary.
            next_page_token: Token, page number or any request argument to request the
                next page of data.

        Returns:
            A prepared request object.
        """
        if next_page_token:
            http_method = "GET"
            url = next_page_token.geturl()
        else:
            http_method = self.rest_method
            url = self.get_url(context)

        params: dict | str = self.get_url_params(context, next_page_token)
        request_data = self.prepare_request_payload(context, next_page_token)
        headers = self.http_headers

        return self.build_prepared_request(
            method=http_method,
            url=url,
            params=params,
            headers=headers,
            json=request_data,
        )
