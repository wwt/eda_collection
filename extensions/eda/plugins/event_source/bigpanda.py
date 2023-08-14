"""
bigpanda.py

Event-Driven Ansible Source Plugin for Big Panda Incidents

Written By:

Nick Thompson <github.com/nsthompson>
Principal Solutions Architect
World Wide Technology <https://www.wwt.com/>

Arguments:
    api_token: Big Panda API Token
    environment: Big Panda Environment Name
    delay: Delay in Seconds between API Calls
"""

import sys
import asyncio
import logging
from typing import Any, Dict
from datetime import datetime, timezone

import aiohttp


BASE_URL="https://api.bigpanda.io/resources"


async def get_environment_id(session, environment):
    try:
        env_url = f'{BASE_URL}/v2.0/environments'
        async with session.get(env_url) as response:
            environments = await response.json()
    except aiohttp.ClientError as client_err:
        print(f'Client error occurred: {client_err}')
        sys.exit(1)

    for env in environments:
        if env.get("name") == environment:
            environment_id = env.get("id")

    return environment_id

async def get_incidents(session, environment_id):
    try:
        incident_url = (
            f'{BASE_URL}/v2.0/environments/{environment_id}'
            f'/incidents?folder=active&expand=alerts'
        )
        logging.debug("URL is %s", incident_url)
        async with session.get(incident_url) as response:
            incidents = await response.json()
    except aiohttp.ClientError as client_err:
        logging.error("Client error occurred: %s", client_err)
        sys.exit(1)

    return incidents.get('items')

async def main(queue: asyncio.Queue(), args: Dict[str, Any]):
    # Configure Logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()

    # Parse Arguments
    api_token = args.get('api_token')
    environment = args.get('environment')
    delay = int(args.get('delay'))
    mock = bool(args.get('mock'))

    if mock:
        logger.debug("Please update mock_arguments for testing...")
        sys.exit(0)

    # Set Request Headers
    headers = {
        "Authorization": f'Bearer {api_token}',
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession(
        headers=headers,
        raise_for_status=True
    ) as session:
        # Get Environment ID by Name
        environment_id = await get_environment_id(session, environment)

        while True:
            current_ts = datetime.now(timezone.utc).timestamp()
            logger.debug("Request Time: %s", int(current_ts))
            incidents = await get_incidents(session, environment_id)

            post_ts = datetime.now(timezone.utc).timestamp()
            logger.debug("Total Request Time: %s", post_ts-current_ts)
            for incident in incidents:
                # Parse Incident Alerts
                # Each Active Alert is a new EDA Event
                for alert in incident.get('alerts'):
                    if alert.get('active'):
                        # Build Event Data Structure
                        event_data = {
                            "environment": {
                                "id": environment_id
                            },
                            "incident": {
                                "id": incident.get('id'),
                                "active": incident.get('active'),
                                "severity": incident.get('severity'),
                                "status": incident.get('status'),
                                "environments": incident.get('environments')
                            },
                            "alert": {
                                "status": alert.get('status'),
                                "description": alert.get('description'),
                                "source_system": alert.get('source_system'),
                                "tags": {}
                            }
                        }
                        # Parse Tags
                        for tag in alert.get('tags'):
                            name = tag.get('name')
                            value = tag.get('value')
                            event_data["alert"]["tags"][name] = value

                        await queue.put(event_data)
            logger.debug("Sleeping for %s seconds...", delay)
            await asyncio.sleep(delay)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    # Configure the following mock arguments if testing via the CLI
    mock_arguments = {
        "api_token": "bigpanda-api-token",
        "environment": "bigpanda-environment-name",
        "delay": "10",
        # Set to false if you want to test via CLI after updating values above.
        "mock": True
    }

    asyncio.run(main(MockQueue(), mock_arguments))
