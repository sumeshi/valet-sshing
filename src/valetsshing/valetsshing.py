# coding: utf-8
import re
from pathlib import Path
from dataclasses import dataclass, field

from typing import Optional, List
from itertools import chain

import click

@dataclass
class SshConfigDir:
    path: Path


@dataclass
class SshConfig:
    host: str
    hostname: Optional[str] = None
    user: Optional[str] = None
    identityfile: Optional[Path] = None
    port: Optional[int] = None
    optional_settings: dict = field(default_factory=dict)


def gen_parsed_ssh_config(config_path: Path) -> List[SshConfig]:
    text = config_path.read_text()
    split_pattern = re.compile(r'\n\s?\n+')

    configs_list: List[List[SshConfig]] = [parse_ssh_config(conf) for conf in re.split(split_pattern, text) if conf]
    return [config for configs in configs_list for config in configs]

def match_attr(attr: str, text: str) -> Optional[str]:
    if re.match(fr'^{attr}\s', text, flags=re.IGNORECASE):
        parts = text.split(' ')
        if len(parts) == 2:
            return parts[1]
    return None


def parse_ssh_config(text: str) -> List[SshConfig]:
    attr_dict: dict = {}
    optional_settings: List[str] = []

    for line in text.splitlines():
        line = line.strip()

        for attr in ('host', 'hostname', 'user', 'identityfile', 'port'):
            find_attr = match_attr(attr, line)
            if find_attr:
                attr_dict[attr] = find_attr
                break
        else:
            cleaned_line = line.strip()
            if cleaned_line:
                optional_settings.append(cleaned_line)
        
    attr_dict['optional_settings'] = optional_settings

    try:
        ssh_config = SshConfig(**{key: value for key, value in attr_dict.items() if value})
        return [ssh_config]

    except TypeError:

        ssh_configs: List[SshConfig] = list()

        # failed to parse
        if optional_settings:
            include_files = [line for line in optional_settings if re.match(fr'^include\s', line, flags=re.IGNORECASE)]

            include_files
        
        return ssh_configs



@click.group()
def valetsshing():
    pass

@valetsshing.command()
def add():
    print('add valetsshing')

@valetsshing.command()
def lst():
    configs = gen_parsed_ssh_config(Path('/Users/s.nakano/.ssh/config'))

    print('-=-=-=-=-=-=-=-=-=-=')
    print(configs)


def run():
    valetsshing()

if __name__ == '__main__':
    run()
