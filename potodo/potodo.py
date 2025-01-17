#!/usr/bin/env python3

import sys
import argparse
import statistics

from pathlib import Path

try:
    import polib
    import requests
except ImportError:
    # TODO: Have the content of requirements.txt dumped in this error message
    print("You need to install polib and requests to be able to run potodo.")
    sys.exit(1)

from potodo._github import get_reservation_list


def get_po_files_from_path(path: str):
    """
    TODO: Try except if path unvalid

    Will get all po files from given path

    :param path: The path to search `po` files for

    :return: Returns a dict will the folder and the po files in it
    """

    po_files = [file for file in Path(path).glob("**/*.po") if ".git/" not in str(file)]

    po_files_per_directory = {
        path.parent.name: set(path.parent.glob("*.po")) for path in po_files
    }
    return po_files_per_directory


def exec_potodo(
    path: str,
    above: int,
    below: int,
    matching_files: bool,
    fuzzy: bool,
    offline: bool,
    hide_reserved: bool,
):
    """
    Will run everything based on the given parameters

    :param path: The path to search into
    :param above: The above threshold
    :param below: The below threshold
    :param matching_files: Should the file paths be printed instead of normal output
    :param fuzzy: Should only fuzzys be printed
    :param offline: Will not connect to internet
    :param hide_reserved: Will not show the reserved files
    """

    if not above:
        above = 0
    if not below:
        below = 100

    if above and below:
        if below < above:
            raise ValueError("Below must be inferior to above")

    if not matching_files and not offline and not hide_reserved:
        issue_reservations = get_reservation_list()
    else:
        issue_reservations = []

    po_files_per_directory = get_po_files_from_path(path)

    for directory, po_files in sorted(po_files_per_directory.items()):
        buffer = []
        folder_stats = []
        printed_list = []
        for po_file in sorted(po_files):
            po_file_stats = polib.pofile(po_file)
            po_file_stat_percent = po_file_stats.percent_translated()
            if po_file_stat_percent == 100:
                folder_stats.append(po_file_stat_percent)
                printed_list.append(False)
                continue
            if int(po_file_stat_percent) < above:
                folder_stats.append(po_file_stat_percent)
                printed_list.append(False)
                continue
            if int(po_file_stat_percent) > below:
                folder_stats.append(po_file_stat_percent)
                printed_list.append(False)
                continue

            if matching_files:
                if fuzzy:
                    if len(po_file_stats.fuzzy_entries()) > 0:
                        print(str(po_file))
                    else:
                        continue
                else:
                    print(str(po_file))
            else:
                if fuzzy:
                    if len(po_file_stats.fuzzy_entries()) > 0:
                        if str(po_file).count("/") > 1:
                            t = str(po_file).split("/")[-2:]
                            po_file_name = t[0] + "/" + t[1]
                        else:
                            po_file_name = str(po_file)

                        buffer.append(
                            f"- {po_file.name:<30} "
                            + f"{len(po_file_stats.translated_entries()):3d} / {len(po_file_stats):3d} "
                            + f"({po_file_stat_percent:5.1f}% translated)"
                            + (
                                f", {len(po_file_stats.fuzzy_entries())} fuzzy"
                                if po_file_stats.fuzzy_entries()
                                else ""
                            )
                            + (
                                f", réservé par {issue_reservations[po_file_name.lower()]}"
                                if po_file_name.lower() in issue_reservations
                                else ""
                            )
                        )
                        folder_stats.append(po_file_stat_percent)
                        printed_list.append(True)
                    else:
                        continue
                else:
                    if str(po_file).count("/") > 1:
                        t = str(po_file).split("/")[-2:]
                        po_file_name = t[0] + "/" + t[1]
                    else:
                        po_file_name = str(po_file)

                    buffer.append(
                        f"- {po_file.name:<30} "
                        + f"{len(po_file_stats.translated_entries()):3d} / {len(po_file_stats):3d} "
                        + f"({po_file_stat_percent:5.1f}% translated)"
                        + (
                            f", {len(po_file_stats.fuzzy_entries())} fuzzy"
                            if po_file_stats.fuzzy_entries()
                            else ""
                        )
                        + (
                            f", réservé par {issue_reservations[po_file_name.lower()]}"
                            if po_file_name.lower() in issue_reservations
                            else ""
                        )
                    )
                    folder_stats.append(po_file_stat_percent)
                    printed_list.append(True)
        if True in printed_list and not matching_files:
            print(f"\n\n# {directory} ({statistics.mean(folder_stats):.2f}% done)\n")
            print("\n".join(buffer))


def main():
    parser = argparse.ArgumentParser(
        prog="potodo", description="List and prettify the po files left to translate"
    )

    parser.add_argument(
        "-p", "--path", type=Path, help="Execute Potodo in the given path"
    )

    parser.add_argument(
        "-l",
        "--matching-files",
        action="store_true",
        help="Suppress normal output; instead print the name of each matching po file from which output would normally "
        "have been printed.",
    )

    parser.add_argument(
        "-f",
        "--fuzzy",
        action="store_true",
        help="Will only print files marked as fuzzys",
    )

    parser.add_argument(
        "-o",
        "--offline",
        action="store_true",
        help="Will not do any fetch to GitHub/online if given",
    )

    parser.add_argument(
        "-n",
        "--no-reserved",
        action="store_true",
        help="Will not print the info about reserved files",
    )

    parser.add_argument(
        "-a",
        "--above",
        type=int,
        help="Will list all TODOs ABOVE given INT%% completion",
    )
    parser.add_argument(
        "-b",
        "--below",
        type=int,
        help="Will list all TODOs BELOW given INT%% completion",
    )

    args = parser.parse_args()
    if not args.path:
        path = "."
    else:
        path = str(args.path)

    exec_potodo(
        path,
        args.above,
        args.below,
        args.matching_files,
        args.fuzzy,
        args.offline,
        args.no_reserved,
    )
