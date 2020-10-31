# coding: utf-8
import click

@click.group()
def valetsshing():
    pass

@valetsshing.command()
def add():
    print('add valetsshing')

@valetsshing.command()
def lst():
    print('list valetsshing')


def run():
    valetsshing()

if __name__ == '__main__':
    run()
