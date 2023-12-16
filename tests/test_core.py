"""Tests standard tap features using the built-in SDK tests library."""

import responses
from responses import POST, GET
import pytest
import subprocess
from tap_prefect.tap import Tapprefect
import json
import re

SAMPLE_CONFIG = {
    "start_date": "2023-05-18T00:00:00Z",
    "api_url": "https://api.prefect.cloud/api",
    "auth_token": "YYUUUU",
    "workspace_id": "123",
    "account_id": "456"
    }

BASE_URL = f"https://api.prefect.cloud/api/accounts/{SAMPLE_CONFIG['account_id']}/workspaces/{SAMPLE_CONFIG['workspace_id']}/"


def deployments_response():
    """Return a sample response for the accounts stream."""

    js = json.loads(open('tests/sample_responses/deployments.json', 'r').read())
    return js


def events_response():
    page1 = json.loads(open('tests/sample_responses/events_page1.json', 'r').read())
    page2 = json.loads(open('tests/sample_responses/events_page2.json', 'r').read())
    return page1, page2



def flows_response():
    """Return a sample response for the flows stream."""
    js = json.loads(open('tests/sample_responses/flows.json', 'r').read())
    return js


def flow_runs_response():
    """Return a sample response for the flow_runs stream."""
    js = json.loads(open('tests/sample_responses/flow_runs.json', 'r').read())
    return js


@responses.activate
def test_deployments(capsys):

    tap = Tapprefect(config=SAMPLE_CONFIG)

    responses.add(POST, BASE_URL + "deployments/filter", json=deployments_response(), status=200)

    _ = tap.streams['deployments'].sync(None)

    all_outs = capsys.readouterr()

    all_stdout = all_outs.out.strip()
    stdout_parts = all_stdout.split('\n')
    assert len(stdout_parts) == 4
    assert 'SCHEMA' in all_stdout
    assert 'RECORD' in all_stdout
    assert 'STATE' in all_stdout



@responses.activate
def test_flows(capsys):

    tap = Tapprefect(config=SAMPLE_CONFIG)

    responses.add(POST, BASE_URL + "flows/filter", json=flows_response(), status=200)

    _ = tap.streams['flows'].sync(None)

    all_outs = capsys.readouterr()

    all_stdout = all_outs.out.strip()
    stdout_parts = all_stdout.split('\n')
    assert len(stdout_parts) == 4
    assert 'SCHEMA' in all_stdout
    assert 'RECORD' in all_stdout
    assert 'STATE' in all_stdout



@responses.activate
def test_flow_runs(capsys):

    tap = Tapprefect(config=SAMPLE_CONFIG)

    responses.add(POST, BASE_URL + "flow_runs/filter", json=flow_runs_response(), status=200)
    responses.add(POST, BASE_URL + "flow_runs/filter", json=[], status=200)

    _ = tap.streams['flow_runs'].sync(None)

    all_outs = capsys.readouterr()

    all_stdout = all_outs.out.strip()
    stdout_parts = all_stdout.split('\n')
    assert len(stdout_parts) == 4
    assert 'SCHEMA' in all_stdout
    assert 'RECORD' in all_stdout
    assert 'STATE' in all_stdout


@responses.activate
def test_events(capsys):

    tap = Tapprefect(config=SAMPLE_CONFIG)

    events_1, events_2 = events_response()

    responses.add(POST, BASE_URL + "events/filter", json=events_1, status=200)

    responses.add_callback(
    GET,
    re.compile(r'https://api.prefect.cloud/api/accounts/123/workspaces/456/events/filter/next'),
    callback=lambda _: (200, {}, json.dumps(events_2)),
    )
    
    _ = tap.streams['events'].sync(None)

    all_outs = capsys.readouterr()

    all_stdout = all_outs.out.strip()
    stdout_parts = all_stdout.split('\n')
    assert len(stdout_parts) == 6
    assert 'SCHEMA' in all_stdout
    assert 'RECORD' in all_stdout
    assert 'STATE' in all_stdout



