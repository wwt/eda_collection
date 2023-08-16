"""
mqtt.py
An ansible-rulebook event source plugin for receiving events via a mqtt topic.
Arguments:
    host:               The host where the mqtt topic is hosted
    port:               The port where the mqtt server is listening
    username:           The username to connect to the broker
    password:           The password to connect to the broker
    ca_certs:           Multi-line string containing
                        certificate used to sign mqtt broker certificates
    validate_certs:     Disable certificate validation - true/false
    certfile:           The optional multi-line string containing
                        the client certificate, as well as CA certificates needed
                        to establish the certificate's authenticity
    keyfile:            Multi-line string containing the client
                        private key
    keyfile_password:   The optional password to be used when loading the
                        certificate chain
    topic:              The mqtt topic to subscribe to

"""

import asyncio
import json
import logging
from typing import Any, Dict

import aiomqtt


async def write_certfile(path, content, logger):
    """
    Function to write certificate data to a temporary file.

    Args:
        path (str): Path to temporary file
        content (str): Certificate data
        logger (object): Logger object
    """
    with open(path, "w+", encoding='utf-8') as certfile:
        certfile.writelines(content)
    logger.info("Cert data written to %s", path)

async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    logger = logging.getLogger()

    topic = args.get("topic")

    host = args.get("host")
    port = args.get("port")
    username = args.get("username")
    password = args.get("password")

    ca_certs = args.get("ca_certs")
    validate_certs = bool(args.get("validate_certs"))
    certfile = args.get("certfile")
    keyfile = args.get("keyfile")
    keyfile_password = args.get("keyfile_password")

    # Path management for certificate files
    # EDA Server does not support file handling with decision environments
    # We will accept the cert data as strings and write out temporary files
    # to pass when configuring TLS.
    path_to_certs = "/tmp"
    ca_certs_path = None
    certfile_path = None
    keyfile_path = None

    # Build out cert file and absolute paths
    if ca_certs and path_to_certs:
        # Write Certificate to file
        ca_certs_path = f'{path_to_certs}/ca_certs.crt'
        await write_certfile(ca_certs_path, ca_certs, logger)

    if certfile and path_to_certs:
        # Write Certificate to file
        certfile_path = f'{path_to_certs}/certfile.crt'
        await write_certfile(certfile_path, certfile, logger)

    if keyfile and path_to_certs:
        # Write Certificate to file
        keyfile_path = f'{path_to_certs}/keyfile.crt'
        await write_certfile(keyfile_path, keyfile, logger)

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
