"""Komenda `ia5`. Na razie szkielet (E0); logika w E2."""
import argparse
import sys

from . import ENGINE_VERSION
from .config import PAIRS


def cmd_status(_args) -> int:
    print(f"IA5 runner · silnik {ENGINE_VERSION}")
    print("Pary:", ", ".join(PAIRS))
    return 0


def cmd_start(_args) -> int:
    print("ia5 start: sync Dukascopy/Firestore, heartbeat i kolejka — etap E2.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ia5")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("start").set_defaults(func=cmd_start)
    sub.add_parser("status").set_defaults(func=cmd_status)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
