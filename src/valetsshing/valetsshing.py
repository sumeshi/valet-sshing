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
    optional_settings: List[str] = field(default_factory=list)


def gen_parsed_ssh_config(config_path: Path) -> List[SshConfig]:
    text = config_path.read_text()
    split_pattern = re.compile(r'\n\s?\n+')

    configs_list: List[List[SshConfig]] = [parse_ssh_config(conf, config_path) for conf in re.split(split_pattern, text) if conf]
    return list(chain.from_iterable([config for config in configs_list]))

def match_attr(attr: str, text: str) -> Optional[str]:
    if re.match(fr'^{attr}\s', text, flags=re.IGNORECASE):
        parts = text.split(' ')
        if len(parts) == 2:
            return parts[1]
    return None


def parse_ssh_config(text: str, config_path: Path) -> List[SshConfig]:
    attr_dict: dict = {}
    optional_settings: List[str] = []

    for line in text.splitlines():
        line = line.strip()

        if line.startswith('#'):
            continue

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
            include_paths = [line for line in optional_settings if re.match(fr'^include\s', line, flags=re.IGNORECASE)]
            include_files = chain.from_iterable([resolve_include_path(include_file, config_path.parent) for include_file in include_paths])

            for include_file in include_files:
                ssh_configs.extend(gen_parsed_ssh_config(include_file))
        
        return ssh_configs


def resolve_include_path(path: str, base_path: Path) -> List[Path]:
    try:
        cleaned_path = path.split(' ')[1]
        return list(base_path.glob(cleaned_path))

    except IndexError:
        return []


def display_configs(configs: List[SshConfig]) -> None:

    def calc_column_width(configs: List[SshConfig]) -> List[int]:
        attr_width: List[int] = [
            max([
                len(getattr(config, attr)) for config in configs if hasattr(config, attr) and getattr(config, attr)
            ]) for attr in ('host', 'hostname', 'user', 'identityfile', 'port')
        ]

        attr_width.append(
            max([
                max([
                    len(optional_setting) for optional_setting in getattr(config, 'optional_settings')
                ]) for config in configs if 1 < len(getattr(config, 'optional_settings'))
            ])
        )

        return attr_width

    print(calc_column_width(configs))

@click.group()
def valetsshing():
    pass

@valetsshing.command()
def add():
    print('add valetsshing')

@valetsshing.command()
def lst():
    configs = gen_parsed_ssh_config(Path('/Users/s.nakano/.ssh/config'))
    display_configs(configs)


def run():
    valetsshing()

if __name__ == '__main__':
    run()
