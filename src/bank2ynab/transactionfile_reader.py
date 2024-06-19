"""
Transaction file reader
"""

from __future__ import annotations

import codecs
import logging
import os
import platform
import re
from os import path
from pathlib import Path
from typing import List

import chardet


def get_files(
    name: str,
    file_pattern: str,
    try_path: str,
    regex_active: bool,
    ext: str,
    prefix: str,
) -> List[str]:
    """
    Returns list of files matching the specified search parameters.

    :param name: Bank format name
    :type name: str
    :param file_pattern: filename or regex pattern to match
    :type file_pattern: str
    :param try_path: provided path to search initially
    :type try_path: str
    :param regex_active: whether or not to use regex in file name check
    :type regex_active: bool
    :param ext: file extension
    :type ext: str
    :param prefix: prefix attached to processed files
    :type prefix: str
    :return: list of matching files
    :rtype: list
    """

    files: List[str] = []
    missing_dir = False
    fpath = find_directory("")
    if file_pattern:
        try:
            fpath = find_directory(try_path)
        except FileNotFoundError:
            missing_dir = True
            fpath = find_directory("")

        fpath = fpath.absolute()
        try:
            directory_list = os.listdir(fpath)
        except FileNotFoundError:
            directory_list = os.listdir(".")

        if regex_active:
            files = [
                path.join(fpath, f)
                for f in directory_list
                if f.endswith(ext)
                if re.match(file_pattern + r".*\.", f)
                if prefix not in f
            ]
        else:
            files = [
                path.join(fpath, f)
                for f in directory_list
                if f.endswith(ext)
                if f.startswith(file_pattern)
                if prefix not in f
            ]

        if not files and missing_dir:
            logging.error(
                "Format: %s\n\n"
                "Error: Can't find download path:"
                "%s\nTrying default path instead:\t %s",
                name,
                try_path,
                fpath,
            )

    return files


def find_directory(filepath: str) -> Path:
    """
    Finds the downloads directory for active user if filepath is not set.

    :param filepath: Filepath specified by the configuration file.
    :raises FileNotFoundError: Error raised if the filepath is invalid.
    :return: The desired directory to use.
    """
    if filepath:
        proper_file_path = Path(filepath)
        try:
            proper_file_path = proper_file_path.expanduser()
        except RuntimeError:
            proper_file_path = Path(filepath)

        if not proper_file_path.exists():
            s = "Error: Input directory not found: {filepath}"
            raise FileNotFoundError(s)

        return proper_file_path

    if platform.system() == "Windows":
        # Windows
        winreg = __import__("winreg")

        shell_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        dl_key = "{374DE290-123F-4565-9164-39C4925E467B}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, shell_path) as key:
            input_dir = Path(winreg.QueryValueEx(key, dl_key)[0]).resolve()
    else:
        # Linux, OSX
        input_dir = Path.home() / "Downloads"

    return input_dir


# TODO add check of config to see if we have encoding specified
def detect_encoding(filepath: str) -> str:
    """
    Utility to detect file encoding. This is imperfect, but
    should work for the most common cases.
    :param filepath: string path to a given file
    :return: encoding alias that can be used with open()
    """
    # First try to guess the encoding with chardet. Take it if the
    # confidence is >60% (randomly chosen)
    # pylint: disable=invalid-name
    with open(filepath, "rb") as f:
        file_content = f.read()
        rslt = chardet.detect(file_content)
        conf, enc = rslt["confidence"], rslt["encoding"]
        if conf > 0.6:
            logging.info("\tOpening file using encoding %s (confidence %s)", enc, conf)
            return enc

    # because some encodings will happily encode anything even if wrong,
    # keeping the most common near the top should make it more likely that
    # we're doing the right thing.
    encodings = [
        "ascii",
        "utf-8",
        "utf-16",
        "cp1251",
        "utf_32",
        "utf_32_be",
        "utf_32_le",
        "utf_16",
        "utf_16_be",
        "utf_16_le",
        "utf_7",
        "utf_8_sig",
        "cp850",
        "cp852",
        "latin_1",
        "big5",
        "big5hkscs",
        "cp037",
        "cp424",
        "cp437",
        "cp500",
        "cp720",
        "cp737",
        "cp775",
        "cp855",
        "cp856",
        "cp857",
        "cp858",
        "cp860",
        "cp861",
        "cp862",
        "cp863",
        "cp864",
        "cp865",
        "cp866",
        "cp869",
        "cp874",
        "cp875",
        "cp932",
        "cp949",
        "cp950",
        "cp1006",
        "cp1026",
        "cp1140",
        "cp1250",
        "cp1252",
        "cp1253",
        "cp1254",
        "cp1255",
        "cp1256",
        "cp1257",
        "cp1258",
        "euc_jp",
        "euc_jis_2004",
        "euc_jisx0213",
        "euc_kr",
        "gb2312",
        "gbk",
        "gb18030",
        "hz",
        "iso2022_jp",
        "iso2022_jp_1",
        "iso2022_jp_2",
        "iso2022_jp_2004",
        "iso2022_jp_3",
        "iso2022_jp_ext",
        "iso2022_kr",
        "latin_1",
        "iso8859_2",
        "iso8859_3",
        "iso8859_4",
        "iso8859_5",
        "iso8859_6",
        "iso8859_7",
        "iso8859_8",
        "iso8859_9",
        "iso8859_10",
        "iso8859_11",
        "iso8859_13",
        "iso8859_14",
        "iso8859_15",
        "iso8859_16",
        "johab",
        "koi8_r",
        "koi8_u",
        "mac_cyrillic",
        "mac_greek",
        "mac_iceland",
        "mac_latin2",
        "mac_roman",
        "mac_turkish",
        "ptcp154",
        "shift_jis",
        "shift_jis_2004",
        "shift_jisx0213",
    ]
    result = ""
    error = (
        ValueError,
        UnicodeError,
        UnicodeDecodeError,
        UnicodeEncodeError,
    )
    for enc in encodings:
        try:
            logging.info("\tAttempting to open file using %s encoding...", enc)
            with codecs.open(filepath, "r", encoding=enc) as f:
                for line in f:
                    line.encode("utf-8")
                return enc
        except error:
            continue

    return result