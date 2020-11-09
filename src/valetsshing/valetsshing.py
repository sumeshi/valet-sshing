# coding: utf-8
import re
from pathlib import Path
from dataclasses import dataclass, field

from typing import Optional, List, Generator
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
        attr_width_list: List[int] = list()
        for attr_name in ('host', 'hostname', 'user', 'identityfile', 'port', 'optional_settings'):
            max_width: int = len(attr_name)

            for config in configs:
                
                if attr_name == 'optional_settings':
                    if config.optional_settings:
                        max_width = max([len(s) for s in config.optional_settings])
                else:
                    attr = getattr(config, attr_name)
                    if attr and max_width < len(attr):
                        max_width = len(attr)
            
            attr_width_list.append(max_width)

        return attr_width_list
    
    def display_table(width_list: List[int]) -> None:
        
        def gen_width_num(width_list: List[int], margin: int = 2):
            while True:
                for width in width_list:
                    yield width + margin
        
        def build_row(width_list: List[int], start_char: str, sep_char: str, end_char: str, bg_char: str, rewrite_msgs: List[str]) -> str:
            g = gen_width_num(width_list)
            return f"{start_char}{sep_char.join([bg_char * g.__next__() for _ in range(len(width_list))])}{end_char}"

        def display_header_row(header_names: List[str], width_list: List[int]) -> None:
            print(build_row(width_list, '┌', '┬', '┐', '─', [''] * 6))
            print(build_row(width_list, '│', '│', '│', ' ', ['Host', 'HostName', 'User', 'IdentityFile', 'Port', 'Optional Settings']))
            print(build_row(width_list, '├', '┼', '┤', '─', [''] * 6))

        header_names = ['Host', 'HostName', 'User', 'IdentityFile', 'Port', 'Optional Settings']
        display_header_row(header_names, width_list)

    width_list = calc_column_width(configs)
    display_table(width_list)

@click.group()
def valetsshing():
    pass

@valetsshing.command()
def add():
    print('add valetsshing')

@valetsshing.command()
def lst():
    configs = gen_parsed_ssh_config(Path('/Users/s.nakano/.ssh/config'))
    # configs = gen_parsed_ssh_config(Path('/Users/s.nakano/.ssh/test.conf'))
    display_configs(configs)


def run():
    valetsshing()

if __name__ == '__main__':
    run()
