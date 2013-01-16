from __future__ import absolute_import

import unittest
import sys

from .validator import Validator, ValidationError, TypeValidator

class ValidatorTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.validator = Validator

    def test_str(self):
        self.assertIsNone(self.validator.validate("Spam", None))

    def test_unicode(self):
        self.assertIsNone(self.validator.validate(u"Eggs", None))

    def test_raw(self):
        self.assertIsNone(self.validator.validate(r"Grail", None))

    def test_bytes(self):
        if sys.version_info[0] > 2:
            # Py3k
            with self.assertRaises(ValidationError):
                self.validator.validate(b"Beep", None)
        else:
            # Python 2
            self.assertIsNone(self.validator.validate(b"Beep", None))

    def test_int(self):
        with self.assertRaises(ValidationError):
            self.validator.validate(42, None)

    def test_float(self):
        with self.assertRaises(ValidationError):
            self.validator.validate(4.2, None)

class TypeValidatorTest(unittest.TestCase):
    def setUp(self):
        self.types = [str, int, float, bool, list, tuple, dict, set]
        self.examples = ["Foobar", 42, 3.141, True, ['a', 'b', 'c'], (1, 2, 3),
                {'foo': 'bar', 'fizz': 'buzz'}, {'animal', 'vegetable',
                'mineral'}]

    def test_types(self):
        for type_idx in range(len(self.types)):
            for ex_idx in range(len(self.examples)):
                typ = self.types[type_idx]
                ex = self.examples[ex_idx]
                validator = TypeValidator("Key", typ)
                if type_idx == ex_idx or (type_idx == 1 and ex_idx == 3):
                    self.assertIsNone(validator.validate(ex))
                else:
                    with self.assertRaises(ValidationError):
                        validator.validate(ex)

    def test_key(self):
        for type_idx in range(len(self.types)):
            typ = self.types[type_idx]
            validator = TypeValidator(typ.__name__, typ)
            for ex_idx in range(len(self.examples)):
                ex = self.examples[ex_idx]
                if type_idx == ex_idx:
                    self.assertIsNone(validator.validate(
                        ex.__class__.__name__, ex))
                else:
                    with self.assertRaises(ValidationError):
                        validator.validate(ex.__class__.__name__, ex)

