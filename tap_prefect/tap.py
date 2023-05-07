"""prefect tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_prefect import streams


class Tapprefect(Tap):
    """prefect tap class."""

    name = "tap-prefect"

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "account_id",
            th.StringType,
            required=True,
            description="Project IDs to replicate",
        ),
        th.Property(
            "workspace_id",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The earliest record date to sync",
        ),
        th.Property(
            "api_url",
            th.StringType,
            default="https://api.prefect.cloud/api/",
            description="The url for the API service",
        ),
        th.Property(
            "start_date",
            th.StringType,
            default="2019-08-24T14:15:22Z",
            description="Start date for records",
        ),
    ).to_dict()

    def discover_streams(self) -> list[streams.prefectStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.DeploymentsStream(self),
            streams.FlowsStream(self),
            # streams.FlowRunStream(self),
            # streams.TaskRunSubStream(self),
            # streams.EventStream(self),
        ]


if __name__ == "__main__":
    Tapprefect.cli()
