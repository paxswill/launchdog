from __future__ import absolute_import

import unittest
import sys

from .validator import *


class MatchingKeyTest(unittest.TestCase):
    def test_matching_keys(self):
        self.assertIsNone(MatchingKeyValidator(key="Fizz").validate("Fizz",
            None))
        self.assertIsNone(MatchingKeyValidator(42).validate(42, None))

    def test_mismatched_keys(self):
        with self.assertRaises(ValidationError):
            MatchingKeyValidator("Fizz").validate(42)
        with self.assertRaises(ValidationError):
            MatchingKeyValidator(key=42).validate("Fizz")


class PlistTest (unittest.TestCase):
    def test_str(self):
        self.assertIsNone(PlistValidator("Spam").validate("Spam"))

    def test_unicode(self):
        self.assertIsNone(PlistValidator(u"Eggs").validate(u"Eggs"))

    def test_raw(self):
        self.assertIsNone(PlistValidator(r"Grail").validate(r"Grail"))

    def test_bytes(self):
        if sys.version_info[0] > 2:
            # Py3k
            with self.assertRaises(ValidationError):
                PlistValidator(b"Beep").validate(b"Beep")
        else:
            # Python 2
            PlistValidator(b"Beep").validate(b"Beep")

    def test_int(self):
        with self.assertRaises(ValidationError):
            PlistValidator(42).validate(42)

    def test_float(self):
        with self.assertRaises(ValidationError):
            PlistValidator(4.2).validate(4.2)


class TypeTest(unittest.TestCase):
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
                validator = TypeValidator(typ)
                if type_idx == ex_idx or (type_idx == 1 and ex_idx == 3):
                    self.assertIsNone(validator.validate(ex))
                else:
                    with self.assertRaises(ValidationError):
                        validator.validate(ex)


class RangeTest(unittest.TestCase):
    def test_infinity(self):
        self.assertIsNone(RangeValidator(0, float('inf')).validate(0))
        self.assertIsNone(RangeValidator(0, float('inf')).validate(10))
        self.assertIsNone(RangeValidator(0, float('inf')).validate(
            float('inf')))

    def test_inside_range(self):
        self.assertIsNone(RangeValidator(-20, 20).validate(0))

    def test_minimum_only(self):
        validator = RangeValidator(minimum=-10)
        self.assertIsNone(validator.validate(0))
        with self.assertRaises(ValidationError):
            validator.validate(-20)

class MappingTest(unittest.TestCase):
    def setUp(self):
        inet_validator = MappingValidator({'Wait': bool})
        self.types = {'Label': str, 'Disabled': bool, 'OnDemand': bool,
                'inetdCompatibility':inet_validator}
        self.validator = MappingValidator(self.types)

    def test_simple(self):
        test_map = {'Label': 'com.paxswill.launchdog', 'Disabled': True}
        self.assertIsNone(self.validator.validate(value=test_map))
        with self.assertRaises(ValidationError):
            self.validator.validate(value={'Label': True})

    def test_nested(self):
        test_map = {'Label': 'com.paxswill.launchdog', 'Disabled': False,
                'inetdCompatibility': {'Wait': True}}
        self.assertIsNone(self.validator.validate(value=test_map))
        # modify map
        test_map['inetdCompatibility'] = True
        with self.assertRaises(ValidationError):
            self.validator.validate(value=test_map)
