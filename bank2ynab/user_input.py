from __future__ import annotations

import logging

logger = logging.getLogger("bank2ynab")


def get_user_input(options: list, msg: str) -> str:
    """
    Used to select from a list of options.
    If only one item in list, selects that by default.
    Otherwise displays "msg" asking for input selection (integer only).

    :param options: list of [name, option] pairs to select from
    :param msg: the message to display on the input line

    :return option_selected: the selected item from the list
    """

    selection = 1
    count = len(options)
    if count > 1:
        display_options(options)
        selection = get_int_input(1, count, msg)
    option_selected = options[selection - 1][1]
    return option_selected


def display_options(options: list):
    logging.info("\n")
    for index, option in enumerate(options):
        logging.info("| %s | %s", index + 1, option[0])


def get_int_input(min_val: int, max_val: int, msg: str) -> int:
    """
    Makes a user select an integer between min & max stated values
    :param  min_val: the minimum acceptable integer value
    :param  max_val: the maximum acceptable integer value
    :param  msg: the message to display on the input line

    :return user_input: sanitised integer input in acceptable range
    """
    while True:
        try:
            user_input = int(input(f"{msg} (range {min_val} - {max_val}): "))
            if user_input not in range(min_val, max_val + 1):
                raise ValueError
            break
        except ValueError:
            logger.error(
                """
            %s is not a number within the accepted range %s - %s
            please try again
            """,
                user_input,
                min_val,
                max_val,
            )
            print(
                "The value entered is not an integer in the acceptable"
                " range, please enter a different value!"
            )
            continue
        except TypeError:
            logger.error("%s was not a number, please try again", user_input)
            continue

    return user_input
