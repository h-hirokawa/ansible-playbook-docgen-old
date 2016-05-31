from __future__ import (absolute_import, division, print_function)

from ansible.parsing.yaml.objects import AnsibleUnicode
from ansible.vars.unsafe_proxy import wrap_var
from ruamel.yaml.constructor import RoundTripConstructor

from .objects import PlaybokDocMapping, PlaybokDocSequence

__metaclass__ = type


class PlaybokDocConstructor(RoundTripConstructor):
    def __init__(self, file_name=None):
        self._ansible_file_name = file_name
        super(PlaybokDocConstructor, self).__init__()

    def construct_yaml_map(self, node):
        data = PlaybokDocMapping()
        data._yaml_set_line_col(node.start_mark.line, node.start_mark.column)
        if node.flow_style is True:
            data.fa.set_flow_style()
        elif node.flow_style is False:
            data.fa.set_block_style()
        yield data
        self.construct_mapping(node, data)
        data.ansible_pos = self._node_position_info(node)

    def construct_yaml_str(self, node, unsafe=False):
        # Override the default string handling function
        # to always return unicode objects
        value = self.construct_scalar(node)
        ret = AnsibleUnicode(value)

        ret.ansible_pos = self._node_position_info(node)

        if unsafe:
            ret = wrap_var(ret)

        return ret

    def construct_yaml_seq(self, node):
        data = PlaybokDocSequence()
        data._yaml_set_line_col(node.start_mark.line, node.start_mark.column)
        if node.flow_style is True:
            data.fa.set_flow_style()
        elif node.flow_style is False:
            data.fa.set_block_style()
        if node.comment:
            data._yaml_add_comment(node.comment)
        yield data
        data.extend(self.construct_sequence(node, data))
        data.ansible_pos = self._node_position_info(node)

    def construct_yaml_unsafe(self, node):
        return self.construct_yaml_str(node, unsafe=True)

    def _node_position_info(self, node):
        # the line number where the previous token has ended (plus empty lines)
        # Add one so that the first line is line 1 rather than line 0
        column = node.start_mark.column + 1
        line = node.start_mark.line + 1

        # in some cases, we may have pre-read the data and then
        # passed it to the load() call for YAML, in which case we
        # want to override the default datasource (which would be
        # '<string>') to the actual filename we read in
        datasource = self._ansible_file_name or node.start_mark.name

        return (datasource, line, column)

PlaybokDocConstructor.add_constructor(
    u'tag:yaml.org,2002:map',
    PlaybokDocConstructor.construct_yaml_map)

PlaybokDocConstructor.add_constructor(
    u'tag:yaml.org,2002:python/dict',
    PlaybokDocConstructor.construct_yaml_map)

PlaybokDocConstructor.add_constructor(
    u'tag:yaml.org,2002:str',
    PlaybokDocConstructor.construct_yaml_str)

PlaybokDocConstructor.add_constructor(
    u'tag:yaml.org,2002:python/unicode',
    PlaybokDocConstructor.construct_yaml_str)

PlaybokDocConstructor.add_constructor(
    u'tag:yaml.org,2002:seq',
    PlaybokDocConstructor.construct_yaml_seq)

PlaybokDocConstructor.add_constructor(
    u'!unsafe',
    PlaybokDocConstructor.construct_yaml_unsafe)
