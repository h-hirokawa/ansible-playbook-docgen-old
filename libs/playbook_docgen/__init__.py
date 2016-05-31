from __future__ import (absolute_import, division, print_function)

import ansible
import os
import re

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.playbook.playbook_include import PlaybookInclude
from ansible.plugins import get_all_plugin_loaders

from .yaml.loader import PlaybokDocLoader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__metaclass__ = type


class CommentedDataLoader(DataLoader):
    def _safe_load(self, stream, file_name=None):
        ''' Implements yaml.safe_load(), except using our custom loader class. '''

        loader = PlaybokDocLoader(stream, file_name)
        try:
            return loader.get_single_data()
        finally:
            try:
                loader.dispose()
            except AttributeError:
                pass  # older versions of yaml don't have dispose function, ignore


def _parse_comment_descriptions(comments, maxsplit=-1):
    if not comments or len(comments) < 2:
        return ['']
    comment_tokens = comments[1]
    if not isinstance(comment_tokens, list):
        return ['']
    comments = ''.join(token.value for token in comment_tokens)
    results = comments.split('\n\n', maxsplit)
    results = [re.sub(r'^#+ ?', '', part.strip(), flags=re.MULTILINE) for part in results]
    return results


# monkey patching
def _load_playbook_data(self, file_name, variable_manager):
    if os.path.isabs(file_name):
        self._basedir = os.path.dirname(file_name)
    else:
        self._basedir = os.path.normpath(
            os.path.join(self._basedir, os.path.dirname(file_name))
        )

    # set the loaders basedir
    self._loader.set_basedir(self._basedir)

    self._file_name = file_name

    # dynamically load any plugins from the playbook directory
    for name, obj in get_all_plugin_loaders():
        if obj.subdir:
            plugin_path = os.path.join(self._basedir, obj.subdir)
            if os.path.isdir(plugin_path):
                obj.add_directory(plugin_path)

    ds = self._loader.load_from_file(os.path.basename(file_name))
    if not isinstance(ds, list):
        raise AnsibleParserError("playbooks must be a list of plays", obj=ds)

    pb_desc_list = _parse_comment_descriptions(ds.ca.comment)
    self.descs = '\n'.join(pb_desc_list[:-1])
    remaining_desc_list = pb_desc_list[-1:]

    # Parse the playbook entries. For plays, we simply parse them
    # using the Play() object, and includes are parsed using the
    # PlaybookInclude() object
    for i, entry in enumerate(ds):
        if not isinstance(entry, dict):
            raise AnsibleParserError("playbook entries must be either a valid play or an include statement", obj=entry)
        if 'include' in entry:
            pb = PlaybookInclude.load(entry, basedir=self._basedir, variable_manager=variable_manager, loader=self._loader)
            if pb is not None:
                self._entries.extend(pb._entries)
            else:
                display.display("skipping playbook include '%s' due to conditional test failure" % entry.get('include', entry), color=C.COLOR_SKIP)
        else:
            entry_obj = Play.load(entry, variable_manager=variable_manager, loader=self._loader)
            desc_list = remaining_desc_list if i == 0 else []
            desc_list += _parse_comment_descriptions(ds.ca.items.get(i))
            entry_obj.descs = '\n'.join(desc_list)
            entry_obj.file_name = os.path.basename(file_name)
            self._entries.append(entry_obj)
_default_load_playbook_data = ansible.playbook.Playbook._load_playbook_data
ansible.playbook.Playbook._load_playbook_data = _load_playbook_data


def _always_return_true(func):
    def wrapped(*args, **kwargs):
        func(*args, **kwargs)
        return True
    return wrapped
ansible.playbook.conditional.Conditional.evaluate_conditional = _always_return_true(ansible.playbook.conditional.Conditional.evaluate_conditional)
ansible.playbook.block.Block.evaluate_conditional = _always_return_true(ansible.playbook.block.Block.evaluate_conditional)
