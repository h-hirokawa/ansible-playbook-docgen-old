from __future__ import (absolute_import, division, print_function)

import json
import os
import stat
import uuid
import ansible.playbook

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleOptionsError, AnsibleParserError
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject
from ansible.playbook import Playbook
from ansible.playbook.base import Base
from ansible.playbook.block import Block
from ansible.playbook.play import Play
from ansible.playbook.playbook_include import PlaybookInclude
from ansible.plugins import get_all_plugin_loaders
from ansible.vars import VariableManager
from .yaml.loader import PlaybokDocLoader

__metaclass__ = type


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def _json_dump_default(obj):
    if isinstance(obj, Base):
        return obj.serialize()
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    return repr(obj)


class PlaybookDocgenCLI(CLI):
    def parse(self):
        # create parser for CLI options
        parser = CLI.base_parser(
            usage="%prog playbook.yml",
            vault_opts=True,
        )

        self.options, self.args = parser.parse_args(self.args[1:])

        self.parser = parser

        if len(self.args) == 0:
            raise AnsibleOptionsError("You must specify a playbook file to run")

        display.verbosity = self.options.verbosity
        self.validate_conflicts(vault_opts=True)

    def run(self):

        super(PlaybookDocgenCLI, self).run()

        def _parse_block(block, tags):
            result = u''
            for task in block.block:
                if isinstance(task, Block):
                    result += _parse_block(task, tags)
                    continue
                if task.action == 'meta':
                    continue
                result += u'      {}'.format(task.name if task.name else task.action)
                new_tags = sorted(list(tags.union(set(task.tags))))
                result += u"\tTAGS: [{}]\n" .format(', '.join(new_tags))
                if task.name:
                    result += '        action: {}\n'.format(task.action)
            return result

        # Note: slightly wrong, this is written so that implicit localhost
        # Manage passwords
        vault_pass = None

        loader = CommentedDataLoader()

        if self.options.vault_password_file:
            # read vault_pass from a file
            vault_pass = CLI.read_vault_password_file(self.options.vault_password_file, loader=loader)
            loader.set_vault_password(vault_pass)
        elif self.options.ask_vault_pass:
            vault_pass = self.ask_vault_passwords()[0]
            loader.set_vault_password(vault_pass)

        # create the variable manager, which will be shared throughout
        # the code, ensuring a consistent view of global variables
        variable_manager = VariableManager()

        for playbook in self.args:
            # initial error check, to make sure all specified playbooks are accessible
            # before we start running anything through the playbook executor
            if not os.path.exists(playbook):
                raise AnsibleError("the playbook: %s could not be found" % playbook)
            if not (os.path.isfile(playbook) or stat.S_ISFIFO(os.stat(playbook).st_mode)):
                raise AnsibleError("the playbook: %s does not appear to be a file" % playbook)

            display.display(u'\nplaybook: {}'.format(playbook))

            pb = Playbook.load(playbook, variable_manager=variable_manager, loader=loader)
            plays = pb.get_plays()
            for i, play in enumerate(plays):
                msg = u"\n  play #{} ({}): {}".format(i + 1, ','.join(play.hosts), play.name)
                tags = set(play.tags)
                msg += u'\tTAGS: [{}]'.format(','.join(tags))

                display.display(msg)
                if play.descs:
                    display.display(u'    description:\n      {}'.format('\n      '.join(play.descs)))

                taskmsg = '    tasks:\n'

                blocks = play.compile()
                for block in blocks:
                    taskmsg += _parse_block(block, tags)
                display.display(taskmsg)

        return 0
