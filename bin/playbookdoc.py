from __future__ import print_function

import optparse
import os
import re
import sys

from ansible.playbook import Playbook
from ansible.vars import VariableManager
from ansible.errors import AnsibleParserError
from jinja2 import Environment, PackageLoader
from pathlib import Path
from playbook_docgen import CommentedDataLoader

j2_env = Environment(loader=PackageLoader('playbook_docgen', 'templates'),
                     trim_blocks=True, lstrip_blocks=True)
j2_env.filters['basename'] = os.path.basename


def load_playbooks(pb_dir):
    YAML_EXTENSIONS = ['.yaml', '.yml']

    yamls = []
    for ext in YAML_EXTENSIONS:
        yamls.extend(Path(pb_dir).glob('*{}'.format(ext)))
    loader = CommentedDataLoader()
    var_manager = VariableManager()
    for y in yamls:
        try:
            yield Playbook.load(y.as_posix(), variable_manager=var_manager, loader=loader)
        except AnsibleParserError:
            print('{} is not a valid playbook.'.format(y.as_posix()), file=sys.stderr)


def main():
    parser = optparse.OptionParser(
        usage="""usage: %prog -o <output_dir> <playbook_dir>""")

    parser.add_option('-o', '--output-dir', action='store', dest='destdir',
                      help='Directory to place all output', default='')

    (opts, args) = parser.parse_args(sys.argv[1:])

    if not args:
        parser.error('A playbook directory is required.')

    pb_dir = args[0]
    if not opts.destdir:
        parser.error('An output directory is required.')

    pb_dir = os.path.abspath(pb_dir)
    if not os.path.isdir(pb_dir):
        print('{} is not a directory.'.format(pb_dir), file=sys.stderr)
        sys.exit(1)

    playbooks = list(load_playbooks(pb_dir))

    if not playbooks:
        print('no playbooks found.', file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(opts.destdir):
        os.makedirs(opts.destdir)

    with open(os.path.join(opts.destdir, 'index.md'), 'w') as index_md:
        index_md.write(j2_env.get_template('index.md.j2').render(
            project=os.path.basename(pb_dir), playbooks=playbooks,
        ))
    generate_playbook_docs(playbooks, opts.destdir)


def generate_playbook_docs(playbooks, destdir):
    def filter_attrs(play, key, value):
        default = getattr(getattr(play, '_{}'.format(key)), 'default', None)
        return key not in ('uuid', 'name', 'hosts', 'pre_tasks', 'tasks', 'post_tasks', 'roles') and default != value and (default or value)

    docdir = os.path.join(destdir, 'playbooks')
    if not os.path.isdir(docdir):
        os.makedirs(docdir)
    tmpl = j2_env.get_template('playbook.md.j2')
    for pb in playbooks:
        pb_name = os.path.basename(pb._file_name)
        plays = pb.get_plays()
        for p in plays:
            p.attrs = {k: v for k, v in p.serialize().items() if filter_attrs(p, k, v)}
        with open(os.path.join(docdir, '{}.md'.format(pb_name)), 'w') as f:
            f.write(re.sub('\n\n+', '\n\n', tmpl.render(playbook=pb, plays=plays)))


if __name__ == "__main__":
    main()
