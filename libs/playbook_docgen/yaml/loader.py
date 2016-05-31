from __future__ import (absolute_import, division, print_function)

from ruamel.yaml.reader import Reader
from ruamel.yaml.scanner import RoundTripScanner
from ruamel.yaml.composer import Composer
from ruamel.yaml.parser import RoundTripParser
from ruamel.yaml.resolver import VersionedResolver
from .constructor import PlaybokDocConstructor

__metaclass__ = type


class PlaybokDocLoader(Reader, RoundTripScanner, RoundTripParser, Composer,
                       PlaybokDocConstructor, VersionedResolver):
    def __init__(self, stream, file_name=None, version="1.1"):
        Reader.__init__(self, stream)
        RoundTripScanner.__init__(self)
        RoundTripParser.__init__(self)
        Composer.__init__(self)
        PlaybokDocConstructor.__init__(self, file_name=file_name)
        VersionedResolver.__init__(self, version)
