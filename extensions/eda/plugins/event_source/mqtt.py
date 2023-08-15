"""
mqtt.py
An ansible-rulebook event source plugin for receiving events via a mqtt topic.
Arguments:
    host:               The host where the mqtt topic is hosted
    port:               The port where the mqtt server is listening
    username:           The username to connect to the broker
    password:           The password to connect to the broker
    cert_path:          The directory containing certificate files.
                        Can be in root of repo or under rulebooks.
    ca_certs:           The filename of optional certificate authority file containing
                        certificate used to sign mqtt broker certificates
    validate_certs:     Disable certificate validation - true/false
    certfile:           The optional client certificate file name containing
                        the client certificate, as well as CA certificates needed
                        to establish the certificate's authenticity
    keyfile:            The optional client key file name containing the client
                        private key
    keyfile_password:   The optional password to be used when loading the
                        certificate chain
    topic:              The mqtt topic to subscribe to

"""

import asyncio
import json
import logging
import os
from typing import Any, Dict

import aiomqtt


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    logger = logging.getLogger()

    topic = args.get("topic")

    host = args.get("host")
    port = args.get("port")
    username = args.get("username")
    password = args.get("password")

    cert_path = args.get("cert_path")
    ca_certs = args.get("ca_certs")
    validate_certs = bool(args.get("validate_certs"))
    certfile = args.get("certfile")
    keyfile = args.get("keyfile")
    keyfile_password = args.get("keyfile_password")

    # Path management for certificate files
    # This solves an issue when using EDA server and finding file paths
    path_to_certs = None
    ca_certs_path = None
    certfile_path = None
    keyfile_path = None

    if cert_path:
        # Find the absolute path to the ca_certs filename
        for root, dirs, _ in os.walk('./', topdown=True):
            for dirname in dirs:
                if cert_path in dirname:
                    path_to_certs = os.path.join(root, dirname)
                    logger.info("Cert path found at %s", path_to_certs)

    # Build out cert file absolute paths
    if ca_certs and path_to_certs:
        ca_certs_path = f'{path_to_certs}/{ca_certs}'
        logger.info("ca_certs path found at %s", ca_certs_path)

    if certfile and path_to_certs:
        certfile_path = f'{path_to_certs}/{certfile}'
        logger.info("certfile path found at %s", certfile_path)

    if keyfile and path_to_certs:
        keyfile_path = f'{path_to_certs}/{keyfile}'
        logger.info("keyfile path found at %s", keyfile_path)

    if ca_certs_path or certfile_path or keyfile_path:
        logger.info("Certificates provided, setting tls_params...")
        tls_params = aiomqtt.TLSParameters(
            ca_certs=ca_certs_path,
            certfile=certfile_path,
            keyfile=keyfile_path,
            keyfile_password=keyfile_password,
            cert_reqs=validate_certs if validate_certs is not None else True
        )
    else:
        logger.info("Certificates not provided, setting tls_params to None...")
        tls_params = None

    mqtt_consumer = aiomqtt.Client(
        hostname=host,
        port=port,
        username=username,
        password=password,
        tls_params=tls_params
    )

    await mqtt_consumer.connect()

    try:
        async with mqtt_consumer.messages() as messages:
            await mqtt_consumer.subscribe(topic)
            async for message in messages:
                try:
                    data = json.loads(message.payload.decode())
                    await queue.put(data)
                except json.decoder.JSONDecodeError as json_exception:
                    logger.error(json_exception)
    finally:
        logger.info("Disconneccting from broker")
        mqtt_consumer.disconnect()

if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(
        main(
            MockQueue(),
            {"topic": "eda", "host": "localhost", "port": "1883"},
        )
    )
