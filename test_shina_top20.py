import contextlib
import io
import unittest
import urllib.error
from decimal import Decimal
from unittest.mock import patch

import shina_top20 as app


class TopRatesTests(unittest.TestCase):
    def test_numeric_sort_missing_values_and_stable_ties(self):
        text = (
            "説明行\n注記\n抽出条件,全体\n"
            "コード,銘柄名,当日品貸料率（円）\n"
            "1,九円,9.00\n2,十円,10.00\n3,同率,10.00\n"
            "4,対象外,*****\n5,空欄,\n6,ゼロ,0.00\n"
            "7,非有限,NaN\n8,無限,Infinity\n"
        )
        self.assertEqual(app.top_rates(text), [
            ("十円", Decimal("10.00")), ("同率", Decimal("10.00")),
            ("九円", Decimal("9.00")), ("ゼロ", Decimal("0.00")),
        ])

    def test_limit_twenty(self):
        text = "銘柄名,当日品貸料率（円）\n" + "\n".join(
            f"銘柄{i},{i}" for i in range(25)
        )
        rows = app.top_rates(text)
        self.assertEqual(len(rows), 20)
        self.assertEqual([rate for _, rate in rows], list(map(Decimal, range(24, 4, -1))))

    def test_missing_column(self):
        with self.assertRaisesRegex(ValueError, "必要な列"):
            app.top_rates("銘柄名,別の列\n銘柄,1\n")

    def test_download_decode_and_output(self):
        payload = "注記\n銘柄名,当日品貸料率（円）\n極洋,10.00\n".encode("cp932")
        output = io.StringIO()
        with patch.object(app.urllib.request, "urlopen", return_value=io.BytesIO(payload)) as fetch:
            with contextlib.redirect_stdout(output):
                self.assertEqual(app.main(), 0)
        fetch.assert_called_once_with(app.URL, timeout=30)
        self.assertIn("極洋", output.getvalue())
        self.assertIn("10.00", output.getvalue())

    def test_download_failure(self):
        error = io.StringIO()
        with patch.object(app.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")):
            with contextlib.redirect_stderr(error):
                self.assertEqual(app.main(), 1)
        self.assertIn("CSVを取得できませんでした", error.getvalue())


if __name__ == "__main__":
    unittest.main()
