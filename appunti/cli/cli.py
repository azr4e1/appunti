from __future__ import annotations
from typing import Any, Optional
from collections.abc import MutableMapping

from dataclasses import dataclass, fields
from argparse import ArgumentParser, Namespace

from appunti.zettelkasten.zettelkasten import Zettelkasten
from appunti.zettelkasten import zettelkasten as zk
from appunti.zettelkasten.notes import NoteException
from appunti.wrappers.base_wrapper import WrapperException
from appunti.wrappers.editor_wrapper import EditorException
from appunti.utils import spinner, ask_for_confirmation
from appunti.zettelkasten.sql import DBManagerException
from appunti.cli.colors import color
from appunti.cli.interactive_selection import Interactive
from appunti.cli.pager import Pager

_COLORS = {
    "title": "CYAN",
    "zk_id": "YELLOW",
    "author": "WHITE",
    "tag": "GREEN",
    "link": "BLUE",
    "creation_date": "MAGENTA",
    "last_changed": "RED"
}

_TAB_LENGTH = 4
_SEPARATOR_LENGTH = 51


class SubcommandsMixin:

    @staticmethod
    def not_implemented(args: Namespace) -> None:
        print("Function not implemented.")

    @staticmethod
    def _get_zk_id(args: Namespace,
                   my_zk: Zettelkasten) -> Optional[list[str]]:
        if args.zk_id is None or not args.zk_id:
            loop = Interactive(my_zk)
            zk_id = loop.run()
        else:
            try:
                zk_id = []
                for id in args.zk_id:
                    zk_id.append(my_zk.get_last() if id == "-1" else id)
            except zk.ZettelkastenException as e:
                print(e)
                return None

        return zk_id

    @staticmethod
    def _create_zettelkasten(args: Namespace) -> Zettelkasten:
        my_zk = Zettelkasten(vault=args.vault,
                             author=args.author[0],
                             autocommit=args.autocommit,
                             autosync=args.autosync,
                             editor=args.editor[0])

        return my_zk

    @staticmethod
    def initialize(args: Namespace) -> None:
        try:
            my_zk = Zettelkasten.initialize(args.vault,
                                            args.author[0],
                                            args.git_init,
                                            args.git_origin[0],
                                            autocommit=args.autocommit,
                                            autosync=args.autosync,
                                            force=args.force)
            print(f"Vault initialized in '{args.vault}'")
            del my_zk
        except zk.ZettelkastenException:
            print(f"{args.vault} has already been initialized! Use "
                  f"`--force` to force re-initialization.")

    @staticmethod
    def new(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            _ = my_zk.new(args.title[0],
                          author=args.author[0],
                          confirmation=args.no_confirmation,
                          strict=args.strict)
        except zk.TitleClashError as e:
            print(e)
        except zk.ZettelkastenException as e:
            print(e)
        except WrapperException as e:
            print(e)
        except EditorException as e:
            print(e)
        except NoteException as e:
            print(e)

    @staticmethod
    def edit(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            zk_ids = SubcommandsMixin._get_zk_id(args, my_zk)
            if zk_ids is None or not zk_ids:
                return
            for zk_id in zk_ids:
                my_zk.update(zk_id,
                             confirmation=args.no_confirmation,
                             strict=args.strict)
        except zk.ZettelkastenException as e:
            print(e)
        except WrapperException as e:
            print(e)
        except EditorException as e:
            print(e)
        except NoteException as e:
            print(e)
        except KeyboardInterrupt:
            pass

    @staticmethod
    def open(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            zk_ids = SubcommandsMixin._get_zk_id(args, my_zk)
            if zk_ids is None or not zk_ids:
                return
            my_zk.open(zk_ids)
        except zk.ZettelkastenException as e:
            print(e)
        except WrapperException as e:
            print(e)
        except EditorException as e:
            print(e)

    @staticmethod
    def delete(args: Namespace) -> None:
        my_zk = SubcommandsMixin._create_zettelkasten(args)
        zk_ids = SubcommandsMixin._get_zk_id(args, my_zk)
        if zk_ids is None or not zk_ids:
            return

        # we need to ask for confirmation here since it would
        # interfere with the spinner
        if args.no_confirmation and not ask_for_confirmation(
                "Delete note(s)?"):
            return None

        if len(zk_ids) == 1:
            # single note deletion
            @spinner("Deleting note...", "Deleted note {}.", format=True)
            def decorated_delete() -> str:
                my_zk.delete(zk_ids[0])
                return zk_ids[0]
        else:
            # batch deletion
            @spinner("Deleting notes...", "Deleted {} notes.", format=True)
            def decorated_delete() -> int:
                no_deletions = my_zk.delete_multiple(zk_ids)
                return no_deletions

        decorated_delete()

    @staticmethod
    def print(args: Namespace) -> None:
        my_zk = SubcommandsMixin._create_zettelkasten(args)
        zk_ids = SubcommandsMixin._get_zk_id(args, my_zk)
        if zk_ids is None or not zk_ids:
            return
        for zk_id in zk_ids:
            print(my_zk.print_note(zk_id))

    @staticmethod
    def _pretty_print(header_names: list[str],
                      results: list[tuple[str, ...]],
                      no_header: bool = False,
                      no_color: bool = False) -> None:
        if not no_header:
            print()
            header_length = len(", ".join(header_names))
            header = ", ".join([
                color(col, _COLORS.get(col, "WHITE"), no_color=no_color)
                for col in header_names
            ])
            print(header)
            print("-" * header_length)
        for res in results:
            text = ", ".join([
                color(col,
                      _COLORS.get(header_names[index], "WHITE"),
                      no_color=no_color) for index, col in enumerate(res)
            ])
            print(text)

    @staticmethod
    @spinner("Reindexing vault...", "Reindexing terminated successfully.")
    def reindex(args: Namespace) -> None:
        my_zk = SubcommandsMixin._create_zettelkasten(args)
        if args.no_multi_core:
            my_zk.multiprocess_index_vault()
        else:
            my_zk.index_vault()

    @staticmethod
    def next(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            zk_ids = SubcommandsMixin._get_zk_id(args, my_zk)
            if zk_ids is None or not zk_ids:
                return
            _ = my_zk.next(args.title[0], zk_ids, args.no_confirmation,
                           args.strict)
        except zk.ZettelkastenException as e:
            print(e)
        except WrapperException as e:
            print(e)
        except EditorException as e:
            print(e)
        except NoteException as e:
            print(e)

    @staticmethod
    @spinner(
        "Syncing with remote...",
        "Syncing terminated successfully. You may need to reindex the vault.")
    def sync(args: Namespace) -> None:
        my_zk = SubcommandsMixin._create_zettelkasten(args)
        my_zk.sync()

    @staticmethod
    @spinner("Committing current changes...",
             "Commit terminated successfully.")
    def commit(args: Namespace) -> None:
        my_zk = SubcommandsMixin._create_zettelkasten(args)
        my_zk.commit()

    @staticmethod
    def _info_helper(args: Namespace, my_zk: Zettelkasten, zk_id: str) -> None:
        result = my_zk.get_metadata(zk_id)
        columns = list(result.keys())
        max_length = len(max(columns, key=len)) + _TAB_LENGTH
        for col in result:
            if col in ['tag', 'link']:
                continue
            distance = " " * (max_length - len(col))
            text = f"{col}: {distance}{result[col]}"
            colored_text = color(text,
                                 _COLORS.get(col, "WHITE"),
                                 no_color=args.no_color)
            print(colored_text)
        for col in ['tag', 'link']:
            length_text = len(col + ": ")
            elements = list(result[col])
            distance = " " * (max_length - len(col))
            text = f"{col}: {distance}{elements[0]}"
            colored_text = color(text,
                                 _COLORS.get(col, "WHITE"),
                                 no_color=args.no_color)
            print(colored_text)
            for el in elements[1:]:
                text = distance + " " * length_text + el
                colored_text = color(text,
                                     _COLORS.get(col, "WHITE"),
                                     no_color=args.no_color)
                print(colored_text)

    @staticmethod
    def info(args: Namespace) -> None:
        my_zk = SubcommandsMixin._create_zettelkasten(args)
        try:
            zk_ids = SubcommandsMixin._get_zk_id(args, my_zk)
            if zk_ids is None or not zk_ids:
                return
            for zk_id in zk_ids:
                print("-" * _SEPARATOR_LENGTH)
                SubcommandsMixin._info_helper(args, my_zk, zk_id)
                print("-" * _SEPARATOR_LENGTH)
        except TypeError as e:
            print(e)
        except zk.ZettelkastenException as e:
            print(e)

    @staticmethod
    def browse(args: Namespace) -> None:
        my_zk = SubcommandsMixin._create_zettelkasten(args)
        try:
            zk_ids = SubcommandsMixin._get_zk_id(args, my_zk)
            if zk_ids is None or not zk_ids:
                return
            loop = Pager(my_zk)
            loop.run(zk_ids)
        except TypeError as e:
            print(e)
        except zk.ZettelkastenException as e:
            print(e)

    @staticmethod
    def list(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            results = my_zk.list_notes(
                args.title,
                args.zk_id,
                args.author_name,
                args.tags,
                args.links,
                # args.creation_date,
                # args.access_date,
                args.sort_by[0],
                args.descending,
                args.show)
            SubcommandsMixin._pretty_print(args.show,
                                           results,
                                           no_header=args.no_header,
                                           no_color=args.no_color)
        except zk.ZettelkastenException as e:
            print(e)
        except DBManagerException as e:
            print(e)


@dataclass
class Cli(SubcommandsMixin):
    """
    Provide interface abstraction
    """
    prog: str
    description: str
    command_initialize: MutableMapping[str, Any]
    command_new: MutableMapping[str, Any]
    command_edit: MutableMapping[str, Any]
    command_open: MutableMapping[str, Any]
    command_delete: MutableMapping[str, Any]
    command_print: MutableMapping[str, Any]
    command_list: MutableMapping[str, Any]
    command_reindex: MutableMapping[str, Any]
    command_next: MutableMapping[str, Any]
    command_sync: MutableMapping[str, Any]
    command_commit: MutableMapping[str, Any]
    command_info: MutableMapping[str, Any]
    command_browse: MutableMapping[str, Any]
    # command_metadata: MutableMapping[str, Any]
    flag_vault: MutableMapping[str, Any]
    flag_author: MutableMapping[str, Any]
    flag_autocommit: MutableMapping[str, Any]
    flag_autosync: MutableMapping[str, Any]
    flag_editor: MutableMapping[str, Any]
    flag_version: MutableMapping[str, Any]

    def __post_init__(self) -> None:
        # define global parser
        self.global_parser = ArgumentParser(prog=self.prog,
                                            description=self.description)
        commands, flags = self._get_commands()

        # add the normal global flags
        if flags:
            for flag in flags:
                flag_config = getattr(self, "flag_" + flag)
                self.global_parser.add_argument("--" + flag, **flag_config)

        # add the subcommands
        if commands:
            self.subparsers = self.global_parser.add_subparsers()
            for command in commands:
                self._create_subparsers(command)

    def _get_commands(self) -> tuple[list[str], list[str]]:
        """
        Get subcommands and flags from the dataclass fields.

        If the field starts with `command_` it means it's
        a subcommand. If it starts with `flag_`, it is a flag.
        """
        commands: list[str] = []
        flags: list[str] = []
        for comm in fields(self):
            if comm.name.startswith("command_"):
                commands.append(comm.name.removeprefix("command_"))
            elif comm.name.startswith("flag_"):
                flags.append(comm.name.removeprefix("flag_"))

        return commands, flags

    def _create_subparsers(self, command: str) -> None:
        """
        Create a subparser given the command.

        :param command: command to create a subparser for.
        """
        # get the command configuration: help, flags, etc.
        command_config = getattr(self, "command_" + command)
        parser = self.subparsers.add_parser(command,
                                            help=command_config.get(
                                                "help", ""))

        # get the command's sub-flags
        subflags = command_config.get('flags', {})
        for flag in subflags:
            parser.add_argument(flag, **subflags[flag])

        # set the default action when invoking this sub-command.
        default_func = getattr(self, command, self.not_implemented)
        parser.set_defaults(func=default_func)

    def parse(self, *args: Any, **kwargs: Any) -> Namespace:
        cli_args: Namespace = self.global_parser.parse_args(*args, **kwargs)

        return cli_args

    def run(self, *args: Any, **kwargs: Any) -> None:
        cli_args = self.parse(*args, **kwargs)
        if hasattr(cli_args, 'func'):
            cli_args.func(cli_args)
        else:
            cli_args = self.global_parser.parse_args(['--help'])
            print(cli_args.help)

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        cli_args = self.parse(*args, **kwargs)
        if hasattr(cli_args, 'func'):
            cli_args.func(cli_args)
        else:
            cli_args = self.global_parser.parse_args(['--help'])
            print(cli_args.help)
