import unittest

import main


class TestTokenize(unittest.TestCase):
    def test_tokenize(self):
        expressions = [
            "(define r 10)",
            "(+ 1 1)",
            "(* 10 (+ 8 8))",
            "(* (+ 3 (* 7 9) (/ 4 (+ 8 1))))",
        ]
        self.assertEqual(main.tokenize(expressions[0]), ["(", "define", "r", "10", ")"])


if __name__ == "__main__":
    unittest.main()
