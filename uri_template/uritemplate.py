"""Process URI templates per http://tools.ietf.org/html/rfc6570."""

import collections
import re
from typing import Dict, Iterable, List, Optional

from .expansions import (CommaExpansion, Expansion, ExpansionFailed,
                         FormStyleQueryContinuation, FormStyleQueryExpansion,
                         FragmentExpansion, LabelExpansion, Literal,
                         PathExpansion, PathStyleExpansion,
                         ReservedCommaExpansion, ReservedExpansion, SimpleExpansion)
from .variable import Variable


class ExpansionReserved(Exception):
    """Exception thrown for reserved but unsupported expansions."""

    expansion: str

    def __init__(self, expansion: str) -> None:
        self.expansion = expansion

    def __str__(self) -> str:
        """Convert to string."""
        return 'Unsupported expansion: ' + self.expansion


class ExpansionInvalid(Exception):
    """Exception thrown for unknown expansions."""

    expansion: str

    def __init__(self, expansion: str) -> None:
        self.expansion = expansion

    def __str__(self) -> str:
        """Convert to string."""
        return 'Bad expansion: ' + self.expansion


class URITemplate(object):
    """URI Template object."""

    expansions: List[Expansion]

    def __init__(self, template: str) -> None:
        self.expansions = []
        parts = re.split(r'(\{[^\}]*\})', template)
        for part in parts:
            if (part):
                if (('{' == part[0]) and ('}' == part[-1])):
                    expansion = part[1:-1]
                    if (re.match('^([a-zA-Z0-9_]|%[0-9a-fA-F][0-9a-fA-F]).*$', expansion)):
                        self.expansions.append(SimpleExpansion(expansion))
                    elif ('+' == part[1]):
                        self.expansions.append(ReservedExpansion(expansion))
                    elif ('#' == part[1]):
                        self.expansions.append(FragmentExpansion(expansion))
                    elif ('.' == part[1]):
                        self.expansions.append(LabelExpansion(expansion))
                    elif ('/' == part[1]):
                        self.expansions.append(PathExpansion(expansion))
                    elif (';' == part[1]):
                        self.expansions.append(PathStyleExpansion(expansion))
                    elif ('?' == part[1]):
                        self.expansions.append(FormStyleQueryExpansion(expansion))
                    elif ('&' == part[1]):
                        self.expansions.append(FormStyleQueryContinuation(expansion))
                    elif (',' == part[1]):
                        if ((1 < len(part)) and ('+' == part[2])):
                            self.expansions.append(ReservedCommaExpansion(expansion))
                        else:
                            self.expansions.append(CommaExpansion(expansion))
                    elif (part[1] in '=!@|'):
                        raise ExpansionReserved(part)
                    else:
                        raise ExpansionInvalid(part)
                else:
                    if (('{' not in part) and ('}' not in part)):
                        self.expansions.append(Literal(part))
                    else:
                        raise ExpansionInvalid(part)

    @property
    def variables(self) -> Iterable[Variable]:
        """Get all variables in template."""
        vars: Dict[str, Variable] = collections.OrderedDict()
        for expansion in self.expansions:
            for var in expansion.variables:
                vars[var.name] = var
        return vars.values()

    @property
    def variable_names(self) -> Iterable[str]:
        """Get names of all variables in template."""
        vars: Dict[str, Variable] = collections.OrderedDict()
        for expansion in self.expansions:
            for var in expansion.variables:
                vars[var.name] = var
        return [var.name for var in vars.values()]

    def expand(self, **kwargs) -> Optional[str]:
        """Expand the template."""
        try:
            expanded = [expansion.expand(kwargs) for expansion in self.expansions]
        except ExpansionFailed:
            return None
        return ''.join([expansion for expansion in expanded if (expansion is not None)])

    def partial(self, **kwargs) -> Optional['URITemplate']:
        """Expand the template, preserving expansions for missing variables."""
        try:
            expanded = [expansion.partial(kwargs) for expansion in self.expansions]
        except ExpansionFailed:
            return None
        return URITemplate(''.join(expanded))

    @property
    def expanded(self) -> bool:
        """Determine if template is fully expanded."""
        return (str(self) == self.expand())

    def __str__(self) -> str:
        """Convert to string, returns original template."""
        return ''.join([str(expansion) for expansion in self.expansions])

    def __repr__(self) -> str:
        """Convert to string, returns original template."""
        return str(self)
