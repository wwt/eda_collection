"""
mqtt.py
An ansible-rulebook event source plugin for receiving events via a mqtt topic.
Arguments:
    host:               The host where the mqtt topic is hosted
    port:               The port where the mqtt server is listening
    username:           The username to connect to the broker
    password:           The password to connect to the broker
    ca_certs            The optional certificate authority file path containing
                        certificate used to sign mqtt broker certificates
    validate_certs      Disable certificate validation - true/false
    certfile            The optional client certificate file path containing
                        the client certificate, as well as CA certificates needed
                        to establish the certificate's authenticity
    keyfile             The optional client key file path containing the client
                        private key
    keyfile_password    The optional password to be used when loading the
                        certificate chain
    topic:              The mqtt topic to subscribe to

"""

import asyncio
import json
import logging
from typing import Optional

from pydantic import BaseModel
import aiomqtt


class ArgSpec(BaseModel):
    host: str
    port: str
    username: Optional[str] = None
    password: Optional[str] = None
    topic: str
    # Certificate Requirements
    ca_certs: Optional[str] = None
    validate_certs: Optional[bool] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    keyfile_password: Optional[str] = None


async def main(queue: asyncio.Queue, args: ArgSpec):
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

    if ca_certs:
        tls_params = aiomqtt.TLSParameters(
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
            keyfile_password=keyfile_password,
            cert_reqs=validate_certs if validate_certs is not None else True
        )

    mqtt_consumer = aiomqtt.Client(
        hostname=host,
        port=port,
        username=username,
        password=password,
        tls_params=tls_params if ca_certs else None
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
