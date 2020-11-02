# coding: utf-8
import re
from pathlib import Path
from dataclasses import dataclass, field

from typing import Optional, List

import click

@dataclass
class SshConfigDir:
    path: Path


@dataclass
class SshConfig:
    name: str
    hostname: str
    user: str
    identity_file: Optional[Path] = None
    optional_settings: dict = field(default_factory=dict)


def gen_parsed_ssh_config(config_path: Path) -> List[SshConfig]:
    text = config_path.read_text()
    split_pattern = re.compile(r'\n\s?\n+')

    for conf in re.split(split_pattern, text):
        sshconfig = parse_ssh_config(conf)
        if sshconfig:
            print(sshconfig)


def match_attr(attr: str, text: str) -> Optional[str]:
    if re.match(fr'^{attr}\s', text, flags=re.IGNORECASE):
        parts = text.split(' ')
        if len(parts) == 2:
            return parts[1]
    return None


def parse_ssh_config(text: str) -> SshConfig:

    attr_dict: dict = {}

    for line in text.splitlines():
        line = line.strip()

        for attr in ('host', 'hostname', 'user', 'identityfile'):
            find_attr = match_attr(attr, line)
            if find_attr:
                attr_dict[attr] = find_attr
        
    return {key: value for key, value in attr_dict.items() if value}


@click.group()
def valetsshing():
    pass

@valetsshing.command()
def add():
    print('add valetsshing')

@valetsshing.command()
def lst():
    gen_parsed_ssh_config(Path('/Users/s.nakano/.ssh/config'))


def run():
    valetsshing()

if __name__ == '__main__':
    run()
