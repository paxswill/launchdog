from collections import UserDict

# In Python 3.3, the abstract base classes were moved from `collections` to
# `collections.abc`.
try:
    from collections.abc import Container, Sequence, Mapping
except ImportError:
    from collections import Container, Sequence, Mapping

# This is for Py2/Py3 compatibility.
# `basestring` is the parent class to both `unicode` and `str` in Py2, while
# Py3 just has `str`.
try:
    type(basestring)
except NameError:
    basestring=str


class ValidationError(KeyError):
    """Exception for errors when validating
    """
    pass


class Validator(object):
    """Base class for Validators.
    """

    @staticmethod
    def _valid_type(value, typ):
        """Check that a value is an instance of typ.

        This is a convenience wrapper around issinstance(), raising a
        ValidationError exception in the case of failure."""
        if not isinstance(value, typ):
            raise ValidationError("type of '{}' is not a '{}'".format(value,
                typ.__name__), typ, value)

    def validate(self, key=None, value=None):
        """Validate the key and/or value.

        Implementing classes _must_ call super()'s implementation of this
        method. Most methods in this module are designed to be chained
        together, and using super() ensures that they are all called in
        order."""
        pass

class MatchingKeyValidator(Validator):
    def __init__(self, key=None, **kwargs):
        self.key = key
        super().__init__(**kwargs)

    def validate(self, key=None, value=None):
        super().validate(key, value)
        if key != self.key:
            raise ValidationError("key '{}' is not '{}'".format(key, self.key))


class PlistValidator(MatchingKeyValidator):
    """Validates that the key is a string
    """

    def validate(cls, key=None, value=None):
        super().validate(key, value)
        cls._valid_type(key, basestring)


class TypeValidator(Validator):
    def __init__(self, typ=None, **kwargs):
        self.typ = typ
        super().__init__(**kwargs)

    def validate(self, key=None, value=None):
        if value is None:
            value = key
            key = None
        super().validate(key, value)
        self._valid_type(value, self.typ)


class RangeValidator(Validator):
    def __init__(self, minimum=None, maximum=None, **kwargs):
        self.maximum = maximum
        self.minimum = minimum
        if self.minimum is not None and self.maximum is not None:
            assert self.minimum < self.maximum
        super().__init__(**kwargs)

    def validate(self, key=None, value=None):
        if value is None:
            value = key
        super().validate(key, value)
        if self.maximum is not None and value > self.maximum:
            raise ValidationError("{} is more than the maximum value {}".
                    format(value, self.maximum))
        if self.minimum is not None and value < self.minimum:
            raise ValidationError("{} is less than the maximum value {}".
                    format(value, self.minimum))


class MappingValidator(TypeValidator):
    """Validate the types of the values in a Mapping
    """

    def __init__(self, types, required=[], **kwargs):
        """Create a MappingValidator.

        `types` is a mapping with the keys being the names of keys and
        the values being a single type or a tuple of types that are valid
        for that key.

        `required` is a sequence of keys that are required to be present in
        the mapping."""

        self.types = types
        self.required = required
        self.children = children
        super().__init__(typ=Mapping, **kwargs)

    def validate(self, key=None, value=None):
        """Validate the given map.

        `value` is a map of strings to values. This values must match the
        types given in `self.types`."""

        super().validate(key, value)
        # Check that all required keys are present
        for reqd in self.required:
            if reqd not in value:
                raise ValidationError("required key '{}' not present".format(
                    reqd))

        for sub_key, sub_value in value.items():
            if sub_key not in self.types:
                raise ValidationError("'{}' is not in the allowed set of keys"
                        .format(sub_key))
            else:
                type_or_validator = self.types[sub_key]
                if isinstance(type_or_validator, (type, tuple)):
                    self._valid_type(sub_value, type_or_validator)
                elif isinstance(type_or_validator, Validator):
                    type_or_validator.validate(sub_key, sub_value)

