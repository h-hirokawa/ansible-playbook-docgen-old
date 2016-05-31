from ansible.parsing.yaml.objects import AnsibleMapping, AnsibleSequence
from ruamel.yaml.comments import CommentedSeq, CommentedMap


class PlaybokDocMapping(CommentedMap, AnsibleMapping):
    def __init__(self, *args, **kwargs):
        if len(args) >= 2:
            args = list(args)
            args[1] = 1
        super(PlaybokDocMapping, self).__init__(*args, **kwargs)


class PlaybokDocSequence(CommentedSeq, AnsibleSequence):
    pass
