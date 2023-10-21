import argparse
import concurrent.futures
import json
import logging
import logging.handlers
import multiprocessing
import os
import sys
from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from time import strftime

from .clients import ApiClient, AuthClient

APP_BASE = Path(__file__).parents[1]


def _init_logger(conf: dict):
    logger = logging.getLogger()
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f"{APP_BASE}/{conf['DIR']}/{conf['FILE_NAME']}".replace(
            "%DATE%", strftime("%Y%m%d")
        )
    )
    formatter = logging.Formatter(conf["FORMAT"], conf["DATE_FORMAT"])
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def logging_listener(queue, conf):
    _init_logger(conf)
    while True:
        try:
            record = queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import sys
            import traceback

            traceback.print_exc(file=sys.stderr)


def exec_api(action):
    queue_handler = logging.handlers.QueueHandler(action["queue"])
    logger = logging.getLogger()
    logger.addHandler(queue_handler)
    logger.setLevel(action["log_level"])

    name = multiprocessing.current_process().name
    logger.debug("Worker started: %s" % name)

    client = action["api_client"]
    client.execute(
        method=action["api"]["method"],
        path=action["api"]["path"],
        in_path=action["in_path"],
        body=action["payload"],
    )


def execute():
    parser = argparse.ArgumentParser(description="Run api")
    parser.add_argument("scenario", type=str)
    parser.add_argument("--conf", type=str, default="apyclient")
    parser.add_argument("--max_process", type=int, default=None)
    args = parser.parse_args()

    if args.max_process is not None and os.cpu_count() < args.max_process:
        sys.exit(f"In this environment, the number of CPUs is {os.cpu_count()}.")

    conf_path = APP_BASE / f"{args.conf}.cfg"
    if not conf_path.exists():
        sys.exit(f"Not found conf file. ({conf_path})")

    conf = ConfigParser(interpolation=ExtendedInterpolation())
    conf.read(conf_path)

    # Load scenario
    scenario_dir = (
        f"{APP_BASE}/{conf.get('Path', 'SCENARIO')}/{conf.get('Base', 'NAME')}"
    )
    scenario = f"{scenario_dir}/{args.scenario}"
    try:
        with open(scenario, "r") as fp:
            actions = json.load(fp)["actions"]
    except FileNotFoundError as e:
        sys.exit(f"Not found scenario file. ({scenario})")

    # Load accounts
    accounts_file = f"{scenario_dir}/accounts.json"
    try:
        with open(accounts_file, "r") as fp:
            accounts = json.load(fp)["accounts"]
    except FileNotFoundError as e:
        sys.exit(f"Not found accounts file ({accounts_file})")

    queue = multiprocessing.Manager().Queue(-1)

    # Set api client to each actions
    api_clients = {}
    for act in actions:
        account = next(
            (account for account in accounts if account["id"] != act["account_id"]),
            None,
        )
        if account is None:
            sys.exit(f"Not found account {act['account_id']}")

        # Initialize api client for each account
        if api_clients.get(act["account_id"]) is None:
            endpoint = conf.get("Base", "ENDPOINT")
            api_clients[act["account_id"]] = ApiClient(
                endpoint=endpoint,
                account=account,
                should_autorize=conf.getboolean("Auth", "BEARER_HEADER"),
                auth=AuthClient(
                    auth_endpoint=conf.get("Auth", "ENDPOINT"),
                    authorized_key=conf.get("Auth", "AUTHORISED_KEY"),
                    base_endpoint=endpoint,
                ),
            )

        act["api_client"] = api_clients.get(act["account_id"])
        act["queue"] = queue
        act["log_level"] = conf["Logging"]["LEVEL"]

    # Run
    listener = multiprocessing.Process(
        target=logging_listener, args=(queue, conf["Logging"])
    )
    listener.start()

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=args.max_process
    ) as executer:
        executer.map(exec_api, actions, timeout=60)

    queue.put_nowait(None)
    listener.join()

if __name__ == "__main__":
    execute()
