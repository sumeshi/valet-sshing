# coding: utf-8
import re
from pathlib import Path
from dataclasses import dataclass, field

from typing import Optional, List, Generator, Tuple
from itertools import chain

import click
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

@dataclass
class SshConfigDir:
    path: Path


@dataclass
class SshConfig:
    host: str
    hostname: Optional[str] = None
    user: Optional[str] = None
    identityfile: Optional[str] = None
    port: Optional[str] = None
    optional_settings: List[str] = field(default_factory=list)


def convert_to_object_sshconfig(config_path: Path) -> List[SshConfig]:
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
                ssh_configs.extend(convert_to_object_sshconfig(include_file))
        
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
                        max_value = max([len(s) for s in config.optional_settings])
                        max_width = max_value if max_width < max_value else max_width
                else:
                    attr = getattr(config, attr_name)
                    if attr and max_width < len(attr):
                        max_width = len(attr)
            
            attr_width_list.append(max_width)

        return attr_width_list
    
    def display_table(width_list: List[int]) -> None:
        
        def gen_width_num(width_list: List[int], margin: int = 1):
            while True:
                for width in width_list:
                    yield width + margin
        
        def build_row(start_char: str, sep_char: str, end_char: str, bg_char: str, rewrite_msgs: List[str]) -> str:
            g = gen_width_num(width_list)
            return f"{start_char}{sep_char.join([f'{msg}{bg_char * (g.__next__() - len(msg))}' for msg in rewrite_msgs])}{end_char}"

        def display_header_row(header_names: List[str], width_list: List[int], configs: List[SshConfig]) -> None:
            print(build_row('┌', '┬', '┐', '─', [''] * 6))
            print(build_row('│', '│', '│', ' ', ['Host', 'HostName', 'User', 'IdentityFile', 'Port', 'Optional Settings']))
            for config in configs:
                print(build_row('├', '┼', '┤', '─', [''] * 6))
                print(build_row('│', '│', '│', ' ', [
                    config.host,
                    config.hostname if config.hostname else '',
                    config.user if config.user else '',
                    config.identityfile if config.identityfile else '',
                    config.port if config.port else '',
                    config.optional_settings[0] if config.optional_settings else ''
                ]))
                if 1 < len(config.optional_settings):
                    for optional_settings in config.optional_settings[1:]:
                        print(build_row('│', '│', '│', ' ', ['', '', '', '', '', optional_settings]))
            else:
                print(build_row('└', '┴', '┘', '─', [''] * 6))

        header_names = ['Host', 'HostName', 'User', 'IdentityFile', 'Port', 'Optional Settings']
        display_header_row(header_names, width_list, configs)

    width_list = calc_column_width(configs)
    display_table(width_list)

@click.group()
def valetsshing():
    pass


def generate_keypairs() -> Tuple[str, str]:
    key = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048
    )

    private_key = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ).decode()
    public_key = key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    ).decode()

    return private_key, public_key

def create_config_dir(dirname: str):
    target_dir = Path(Path().home() / '.ssh' / '.valetsshing' / dirname).resolve()
    print(target_dir)

@valetsshing.command()
@click.option("--host", prompt="Host", type=str, required=True)
@click.option("--hostname", prompt="HostName", type=str, required=True)
@click.option("--user", type=str, default=None)
@click.option("--identityfile", type=str, default=None)
@click.option("--port", type=str, default=None)
@click.option("--optional", type=str, multiple=True, default=list())
@click.option("--quiet", "-q", is_flag=True)
@click.option("--generate-keys", is_flag=True)
def add(host: str, hostname: str, user: Optional[str], identityfile: Optional[str], port: Optional[str], optional: List[str], quiet: bool, generate_keys: bool):
    optional_settings: List[str] = list()

    if not quiet:

        user_input = input('User: ')
        user = user_input if user_input else None

        identityfile_input = input('IdentityFile: ')
        identityfile = identityfile_input if identityfile_input else None

        port_input = input('Port: ')
        port = port_input if port_input else None

        if optional:
            optional_settings = list(optional)
        else:
            count = 1
            while True:
                user_input = input(f"Optional Settings #{count}: ")
                if user_input:
                    optional_settings.append(user_input)
                    count += 1
                else:
                    break

    config: SshConfig = SshConfig(host, hostname, user, identityfile, port, optional_settings)

    click.echo(click.style('\nRegister with the following information?', fg='cyan', blink=True, bold=True))
    display_configs([config])

    create_config_dir(config.host)

    if generate_keys:
        click.echo(click.style('\nGenerating Keys...', fg='cyan', blink=True))
        private_key, public_key = generate_keypairs()
        print(private_key)
        print(public_key)
        click.echo(click.style('Succeeded!', fg='green', blink=True))

@valetsshing.command()
def lst():
    configs = convert_to_object_sshconfig(Path('/Users/s.nakano/.ssh/config'))
    # configs = gen_parsed_ssh_config(Path('/Users/s.nakano/.ssh/test.conf'))
    display_configs(configs)


def run():
    valetsshing()

if __name__ == '__main__':
    run()
