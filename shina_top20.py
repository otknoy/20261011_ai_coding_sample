"""日本証券金融の品貸料率CSVから、料率の高い20件を表示する。"""

import csv
import io
import sys
import unicodedata
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation


URL = "https://www.taisyaku.jp/data/shina.csv"
NAME_COLUMN = "銘柄名"
RATE_COLUMN = "当日品貸料率（円）"


def top_rates(text: str) -> list[tuple[str, Decimal]]:
    reader = csv.reader(io.StringIO(text))
    for header in reader:
        if NAME_COLUMN in header and RATE_COLUMN in header:
            break
    else:
        raise ValueError("CSVに必要な列（銘柄名・当日品貸料率（円））がありません。")

    name_index = header.index(NAME_COLUMN)
    rate_index = header.index(RATE_COLUMN)
    rows = []
    for row in reader:
        if not row or not any(field.strip() for field in row):
            continue
        if len(row) <= max(name_index, rate_index):
            raise ValueError("CSVに列数が不足している行があります。")
        try:
            rate = Decimal(row[rate_index].strip())
        except InvalidOperation:
            continue
        if rate.is_finite():
            rows.append((row[name_index].strip(), rate))
    return sorted(rows, key=lambda item: item[1], reverse=True)[:20]


def display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in text)


def print_table(rows: list[tuple[str, Decimal]]) -> None:
    width = max(display_width(name) for name, _ in [(NAME_COLUMN, Decimal(0)), *rows])
    print(NAME_COLUMN + " " * (width - display_width(NAME_COLUMN) + 2) + RATE_COLUMN)
    for name, rate in rows:
        print(name + " " * (width - display_width(name) + 2) + format(rate, "f"))


def main() -> int:
    try:
        with urllib.request.urlopen(URL, timeout=30) as response:
            text = response.read().decode("cp932")
        rows = top_rates(text)
    except (urllib.error.URLError, OSError) as exc:
        print(f"エラー: CSVを取得できませんでした: {exc}", file=sys.stderr)
        return 1
    except UnicodeError:
        print("エラー: CSVをCP932で読み取れませんでした。", file=sys.stderr)
        return 1
    except (csv.Error, ValueError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    print_table(rows)
    if not rows:
        print("数値の品貸料率を持つ銘柄がありません。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
