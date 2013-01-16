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
    """Validates that the key is a string

    This class could probably be called PlistKeyValidator, as the
    `type(key) == str` restriction just applies to plists."""

    def __init__(self, **kwargs):
        # Just to swallow kwargs from children before creating the object
        super().__init__(**kwargs)

    @staticmethod
    def _valid_type(value, typ):
        if not isinstance(value, typ):
            raise ValidationError("type of '{}' is not a '{}'".format(value,
                typ.__name__), typ, value)

    @classmethod
    def validate(cls, key, value):
        cls._valid_type(key, basestring)


class TypeValidator(Validator):
    def __init__(self, key=None, typ=None, **kwargs):
        self.key = key
        self.typ = typ
        super().__init__(**kwargs)

    def validate(self, key, value=None):
        if value is None:
            value = key
            key = self.key
        super().validate(key, value)
        if key != self.key:
            raise ValidationError("'{}' is not '{}'".format(key, self.key))
        self._valid_type(value, self.typ)


class RangeValidator(Validator):
    def __init__(self, maximum=None, minimum=None, **kwargs):
        self.maximum = minimum
        self.minimum = maximum
        super().__init__(**kwargs)

    def validate(self, key, value=None):
        if value is None:
            value = key
            key = self.key
        super().validate(key, value)
        if self.maximum is not None and value > self.maximum:
            raise ValidationError("{} is more than the maximum value {}".
                    format(value, self.maximum))
        if self.minimum is not None and value < self.minimum:
            raise ValidationError("{} is less than the maximum value {}".
                    format(value, self.minimum))


class MappingValidator(Validator):
    """Validate the types of the values in a Mapping
    """

    def __init__(self, types, required=[]):
        """Create a MappingValidator.

        `types` is a mapping with the keys being the names of keys and
        the values being a single type or a tuple of types that are valid
        for that key.

        `required` is a sequence of keys that are required to be present in
        the mapping."""

        super().__init__(self)
        self.types = types
        self.required = required
        self.defaults = defaults

    def validate(self, key, value):
        super().validate(key, value)
        for reqd in self.required:
            if reqd not in self.types:
                raise ValidationError("required key '{}' not present".format(
                    reqd))
        for key, value in self.types.items():
            if not isinstance(value, self.types[key]):
                raise ValidationError("type of '{}' ({}) is not '{}'".format(
                    value, value.__class__, self.types[key]))


