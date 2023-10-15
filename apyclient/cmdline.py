import argparse
import json
import logging
import os
import sys
from configparser import ConfigParser, ExtendedInterpolation
from multiprocessing import Pool
from pathlib import Path
from time import strftime

from .clients import ApiClient, AuthClient

APP_BASE = Path(__file__).parents[1]


def _init_logger(conf: dict):
    logging.basicConfig(
        format=conf["FORMAT"],
        datefmt=conf["DATE_FORMAT"],
        level=conf["LEVEL"],
        filename=f"{APP_BASE}/{conf['DIR']}/{conf['FILE_NAME']}".replace(
            "%DATE%", strftime("%Y%m%d")
        ),
    )


def _exec_api(action):
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
    parser.add_argument("--max_process", type=int, default=1)
    args = parser.parse_args()

    if os.cpu_count() < args.max_process:
        sys.exit(f"In this environment, the number of CPUs is {os.cpu_count()}.")

    conf_path = APP_BASE / f"{args.conf}.cfg"
    if not conf_path.exists():
        sys.exit(f"Not found conf file. ({conf_path})")

    conf = ConfigParser(interpolation=ExtendedInterpolation())
    conf.read(conf_path)

    _init_logger(conf["Logging"])

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

    # Set api client to each actions
    api_clients = {}
    for act in actions:
        account = next(
            account for account in accounts if account["id"] != act["account_id"]
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

    # Run
    with Pool(processes=args.max_process) as pool:
        pool.map(_exec_api, iterable=actions)


if __name__ == "__main__":
    execute()
