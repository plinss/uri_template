"""Variable class for URITemplate."""

from typing import Optional

from .charset import Charset


class VariableInvalid(Exception):
    """Exception thrown for invalid variables."""

    variable: str

    def __init__(self, variable: str) -> None:
        self.variable = variable

    def __str__(self) -> str:
        """Convert to string."""
        return 'Bad variable: ' + self.variable


class Variable(object):
    """
    A template variable.

    https://tools.ietf.org/html/rfc6570#section-2.3
    """

    name: str
    max_length: int
    explode: bool
    array: bool
    default: Optional[str]

    def __init__(self, var_spec: str) -> None:
        self.name = ''
        self.max_length = 0
        self.explode = False
        self.array = False
        self.default = None

        if (var_spec[0:1] not in Charset.VAR_START):
            raise VariableInvalid(var_spec)

        if ('=' in var_spec):
            var_spec, self.default = var_spec.split('=', 1)

        if (':' in var_spec):
            var_spec, max_length = var_spec.split(':', 1)
            if ((0 < len(max_length)) and (len(max_length) < 4)):
                for digit in max_length:
                    if (digit not in Charset.DIGIT):
                        raise VariableInvalid(var_spec + ':' + max_length)
                self.max_length = int(max_length)
                if (not self.max_length):
                    raise VariableInvalid(var_spec + ':' + max_length)
            else:
                raise VariableInvalid(var_spec + ':' + max_length)
        elif ('*' == var_spec[-1]):
            var_spec = var_spec[:-1]
            self.explode = True
        elif ('[]' == var_spec[-2:]):
            var_spec = var_spec[:-2]
            self.array = True
            self.explode = True

        index = 0
        while (index < len(var_spec)):
            codepoint = var_spec[index]
            if (('%' == codepoint)
                    and ((index + 2) < len(var_spec))
                    and (var_spec[index + 1] in Charset.HEX_DIGIT)
                    and (var_spec[index + 2] in Charset.HEX_DIGIT)):
                self.name += var_spec[index:index + 3]
                index += 2
            elif (codepoint in Charset.VAR_CHAR):
                self.name += codepoint
            else:
                raise VariableInvalid(var_spec + ((':' + str(self.max_length)) if (self.max_length) else '')
                                      + ('[]' if (self.array) else ('*' if (self.explode) else '')))
            index += 1

    def __str__(self) -> str:
        """Convert to string."""
        return (self.name + ((':' + str(self.max_length)) if (self.max_length) else '')
                + ('*' if (self.explode and not self.array) else '') + ('[]' if (self.array) else '')
                + (('=' + self.default) if (self.default is not None) else ''))
