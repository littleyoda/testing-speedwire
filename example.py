# -*- coding: utf-8 -*-

import asyncio
import sys
import json

from sma_query_sw.protocol import SMAClientProtocol

import logging

_LOGGER = logging.getLogger(__name__)


with open("config.json", "r") as read_settings:
        settings = json.load(read_settings)


inverters = settings["inverters"]


async def collect_data(exiting):
    while not exiting.is_set():
        for address, inverter in inverters.items():
            inverter["protocol"].start_query()

            if "data" in inverter:
                output_data = json.dumps(inverter["data"])
                print(output_data)
                print(inverter)
                print("===============================")

        try:
            await asyncio.wait_for(exiting.wait(), settings.get("poll_interval", 10))
        except asyncio.TimeoutError:
            pass
        except KeyboardInterrupt:
            pass


async def shutdown(exiting):
    exiting.set()

    for address, inverter in inverters.items():
        await inverter["transport"].close()

    sys.exit(0)


async def main():
    loop = asyncio.get_running_loop()
    on_connection_lost = loop.create_future()
    exiting = asyncio.Event()

    for address, inverter in inverters.items():
        _LOGGER.info(f"Adding {address}")
        inverter["transport"], inverter["protocol"] = await loop.create_datagram_endpoint(
            lambda: SMAClientProtocol(inverter, on_connection_lost), remote_addr=(address, inverter.get("port", 9522)))

    loop.create_task(collect_data(exiting))

    try:
        await on_connection_lost
    except KeyboardInterrupt:
        pass
    finally:
        await shutdown(exiting)


if __name__ == "__main__":  
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass



#sub SMAInverter_SMAcommand($$$$$) {
 # Parameters: $hash - host - command - first - last
# ($sup_TypeLabel,$inv_TYPE,$inv_CLASS,$inv_susyid,$inv_serial) = SMAInverter_SMAcommand($hash, $hash->{HOST}, 0x58000200, 0x00821E00, 0x008220FF);

