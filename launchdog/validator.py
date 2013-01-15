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

    def validate(self, key, value):
        if not isinstance(key, basestring):
            raise ValidationError("'{}' is not a string".format(key))


def _create_type_validator(typ, name=None):
    """Create a Validator for a specific type

    Creates a Validator subclass that checks that the value is of the given
    class."""

    def validate(cls, key, value):
        super(cls).validate(key, value)
        if not isinstance(value, cls.typ):
            raise ValidationError("type of '{}' ({}) is not '{}'".format(
                key, value, cls.typ.__name__))

    name = name if name is not None else typ.__name__.title()+"TypeValidator"
    return type(name, (Validator,), {'validate': classmethod(validate),
        'typ': typ})

# Create validators for types found in plists.
# This could be rewritten to operate on a sequence of types, but this form is
# more readable/discoverable, especially for subclassing.
IntTypeValidator = _create_type_validator(int)
StrTypeValidator = _create_type_validator(basestring, 'StrTypeValidator')
BoolTypeValidator = _create_type_validator(bool)
ContainerTypeValidator = _create_type_validator(Container)
SequenceTypeValidator = _create_type_validator(Sequence)
MappingTypeValidator = _create_type_validator(Mapping)

class MappingValidator(MappingTypeValidator):
    """Validate the types of the values in a Mapping
    """

    def __init__(self, types, required=[]):
        """Create a MappingValidator.

        `types` is a mapping with the keys being the names of keys and
        the values being a single type or a tuple of types that are valid
        for that key.

        'required' is a sequence of keys that are required to be present in
        the mapping."""

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


