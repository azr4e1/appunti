import curses
from pathlib import Path
import textwrap
from enum import Enum, IntEnum, auto

from typing import Optional

from notepy.zettelkasten.zettelkasten import Zettelkasten, ZettelkastenException
from notepy.zettelkasten.notes import Note
from notepy.zettelkasten.notes import sluggify
from notepy.cli.interactive_selection import Interactive


LINKS_RATIO = 4


class Context(Enum):
    OUT = auto()
    FRONTMATTER_IN = auto()
    CODEBLOCK_IN = auto()
    LINK_IN = auto()
    BOLD_IN = auto()
    ITALIC_IN = auto()
    CODE_IN = auto()


class Keybindings(IntEnum):
    J = ord('j')
    S_J = ord('J')
    K = ord('k')
    S_K = ord('K')
    C_D = 4
    C_U = 21
    G = ord('g')
    S_G = ord('G')
    L = ord('l')
    H = ord('h')
    S_L = ord('L')
    S_H = ord('H')
    SHARP = ord('#')
    S = ord('s')
    D = ord('d')
    S_D = ord('D')


class NumberInput:
    pass


class MainWindow:
    def __init__(self, width: int, content: str):
        self.width = width
        self.content = content
        self.pos = 0

        self.lines = self._wrap_content()
        self.limit = len(self.lines) + 1
        self.page = curses.LINES // 2
        self.pad = curses.newpad(self.limit, self.width)
        self._draw_content()
        self.refresh()

    def _wrap_content(self) -> list[str]:
        lines = []
        unwrapped_lines = self.content.split("\n")
        for line in unwrapped_lines:
            if line == "":
                lines.append("\n")
            else:
                for wrapped_line in textwrap.wrap(line, self.width):
                    lines.append(wrapped_line)

        return lines

    def _correct_pos(self, pos: int) -> int:
        if pos < 0:
            pos = 0
        elif pos > self.limit - curses.LINES:
            pos = self.limit - curses.LINES

        return pos

    def scroll_down(self) -> None:
        self.pos = self._correct_pos(self.pos+1)
        self.refresh()

    def scroll_up(self) -> None:
        self.pos = self._correct_pos(self.pos-1)
        self.refresh()

    def go_to_start(self) -> None:
        self.pos = 0
        self.refresh()

    def go_to_end(self) -> None:
        self.pos = self._correct_pos(self.limit-curses.LINES)
        self.refresh()

    def page_down(self) -> None:
        self.pos = self._correct_pos(self.pos + self.page)
        self.refresh()

    def page_up(self) -> None:
        self.pos = self._correct_pos(self.pos - self.page)
        self.refresh()

    def _draw_content(self) -> None:

        context = Context.OUT

        for index, line in enumerate(self.lines):
            if line == "---" and context is Context.OUT:
                context = Context.FRONTMATTER_IN
            elif line == "---" and context is Context.FRONTMATTER_IN:
                context = Context.OUT

            if line.startswith("```") and context is Context.OUT:
                context = Context.CODEBLOCK_IN
            elif line.startswith('```') and context is Context.CODEBLOCK_IN:
                context = Context.OUT

            if context is Context.FRONTMATTER_IN and line != "---":
                self.pad.addstr(index, 0, line, curses.color_pair(1))
            elif context is Context.CODEBLOCK_IN and not line.startswith("```"):
                self.pad.addstr(index, 0, line, curses.color_pair(3))
            elif line.startswith('#'):
                self.pad.addstr(index, 0, line, curses.color_pair(2))
            else:
                self.pad.addstr(index, 0, line)

    def refresh(self) -> None:
        self.pad.refresh(self.pos, 0, 0, 0, curses.LINES-1, self.width)


class LinksWindow:

    def __init__(self, width: int, links: list[str]) -> None:
        self.width = width
        self.links = links
        self.pos = 0

        self.wrapped_links = self._wrap_links()
        self.limit = len(self.wrapped_links) + 1
        self.pad = curses.newpad(self.limit, self.width)
        self._draw_content()
        self.refresh()

    def _wrap_links(self) -> list[str]:
        lines = []
        for index, line in enumerate(self.links):
            line_nr = f"[{index+1}] {line}"
            for wrapped_line in textwrap.wrap(line_nr, self.width):
                lines.append(wrapped_line)

        return lines

    def _correct_pos(self, pos: int) -> int:
        if pos < 0:
            pos = 0
        elif pos > self.limit - curses.LINES:
            pos = self.limit - curses.LINES

        return pos

    def scroll_down(self) -> None:
        self.pos = self._correct_pos(self.pos+1)
        self.refresh()

    def scroll_up(self) -> None:
        self.pos = self._correct_pos(self.pos-1)
        self.refresh()

    def _draw_content(self) -> None:
        for index, line in enumerate(self.wrapped_links):
            self.pad.addstr(index, 0, line, curses.color_pair(4))

    def refresh(self) -> None:
        self.pad.refresh(self.pos, 0, 0, curses.COLS -
                         self.width, curses.LINES-1, curses.COLS)


class Pager:
    def __init__(self, zk: Zettelkasten):
        self.w = curses.initscr()
        self.zk = zk
        self.stack: list[str] = []
        self.head = -1

    def _check_head(self, head: int) -> int:
        if head < -1 * len(self.stack):
            head = -1 * len(self.stack)
        elif head >= 0:
            head = -1

        return head

    def _read_note(self, zk_id: str) -> Note:
        # check that the note exists
        if not self.zk._note_exists(zk_id):
            raise ZettelkastenException(f"Note '{zk_id}' does not exist.")

        filename = self.zk.vault / Path(zk_id).with_suffix(".md")
        note = Note.read(filename)

        return note

    def get_id_from_link(self, link: str) -> Optional[str]:
        results = self.zk.list_notes(show=['title', 'zk_id'])
        titles = [sluggify(title) for title, _ in results]

        try:
            position = titles.index(link)
            return results[position][1]
        except ValueError:
            return None

    def next_note(self, zk_id: str,
                  main_window_width: int,
                  ratio: int) -> tuple[MainWindow, LinksWindow, list[int]]:
        self.w.clear()
        self.w.refresh()
        note = self._read_note(zk_id)
        main_window = MainWindow(main_window_width, note.materialize())
        links_window = LinksWindow(ratio, list(note.links))
        link_nr = [ord(str(i)) for i in range(1, min(len(links_window.links)+1, 9))]

        return main_window, links_window, link_nr

    def _setup(self) -> None:
        # frontmatter
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        # headers
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        # code blocks
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        # links
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)

        curses.curs_set(False)
        curses.noecho()
        curses.cbreak()
        self.w.keypad(True)

        self.w.refresh()

    def _main(self) -> None:
        ratio = curses.COLS // LINKS_RATIO
        main_window_width = curses.COLS - ratio - 1
        if len(self.stack) == 0:
            raise ValueError
        note = self._read_note(self.stack[self.head])
        zk_id: str = self.stack[self.head]
        main_window, links_window, link_nr = self.next_note(zk_id,
                                                            main_window_width,
                                                            ratio)
        while (c := self.w.getch()) != ord('q'):
            match c:
                case Keybindings.J | curses.KEY_DOWN:
                    main_window.scroll_down()
                case Keybindings.K | curses.KEY_UP:
                    main_window.scroll_up()
                case Keybindings.G | curses.KEY_HOME:
                    main_window.go_to_start()
                case Keybindings.S_G | curses.KEY_END:
                    main_window.go_to_end()
                case Keybindings.C_D | curses.KEY_PPAGE:
                    main_window.page_down()
                case Keybindings.C_U | curses.KEY_NPAGE:
                    main_window.page_up()
                case Keybindings.S_J:
                    links_window.scroll_down()
                case Keybindings.S_K:
                    links_window.scroll_up()
                case Keybindings.H | curses.KEY_LEFT:
                    prev_head = self.head
                    self.head = self._check_head(self.head-1)
                    if prev_head == self.head:
                        continue
                    zk_id = self.stack[self.head]
                    main_window, links_window, link_nr = self.next_note(zk_id,
                                                                        main_window_width,
                                                                        ratio)
                case Keybindings.L | curses.KEY_RIGHT:
                    prev_head = self.head
                    self.head = self._check_head(self.head+1)
                    if prev_head == self.head:
                        continue
                    zk_id = self.stack[self.head]
                    main_window, links_window, link_nr = self.next_note(zk_id,
                                                                        main_window_width,
                                                                        ratio)
                case Keybindings.S_H:
                    prev_head = self.head
                    self.head = -1 * len(self.stack)
                    if prev_head == self.head:
                        continue
                    zk_id = self.stack[self.head]
                    main_window, links_window, link_nr = self.next_note(zk_id,
                                                                        main_window_width,
                                                                        ratio)
                case Keybindings.S_L:
                    prev_head = self.head
                    self.head = -1
                    if prev_head == self.head:
                        continue
                    zk_id = self.stack[self.head]
                    main_window, links_window, link_nr = self.next_note(zk_id,
                                                                        main_window_width,
                                                                        ratio)
                case curses.KEY_RESIZE:
                    curses.resize_term(*self.w.getmaxyx())
                    self.w.refresh()
                    ratio = curses.COLS // 4
                    main_window_width = curses.COLS - ratio - 1
                    main_window = MainWindow(main_window_width, note.materialize())
                    links_window = LinksWindow(ratio, list(note.links))
                case c if c in link_nr:
                    link = links_window.links[int(chr(c))-1]
                    tmp_res = self.get_id_from_link(link)
                    if tmp_res is None:
                        continue
                    zk_id = tmp_res
                    main_window, links_window, link_nr = self.next_note(zk_id,
                                                                        main_window_width,
                                                                        ratio)

                    self.stack = self.stack[:self.head+1] if self.head < -1 else self.stack
                    self.stack.append(zk_id)
                    self.head = -1
                case Keybindings.S:
                    curses.endwin()
                    loop = Interactive(self.zk)
                    zk_ids = loop.run()
                    self._setup()
                    if zk_ids is not None:
                        self.stack.extend(zk_ids)
                        self.head = -1
                        zk_id = self.stack[self.head]
                        main_window, links_window, link_nr = self.next_note(zk_id,
                                                                            main_window_width,
                                                                            ratio)
                case Keybindings.SHARP:
                    pass
                case Keybindings.D:
                    if len(self.stack) <= 1:
                        break
                    if self.head != -1:
                        self.stack = self.stack[:self.head] + \
                            self.stack[self.head+1:]
                        self.head = self._check_head(self.head+1)
                    else:
                        self.stack = self.stack[:self.head]
                    zk_id = self.stack[self.head]
                    main_window, links_window, link_nr = self.next_note(zk_id,
                                                                        main_window_width,
                                                                        ratio)

                case Keybindings.S_D:
                    current_zk_id = self.stack[self.head]
                    self.stack = [current_zk_id]
                    self.head = -1
                case _:
                    pass

            # screen.clear()
            main_window.refresh()
            links_window.refresh()
            self.w.refresh()

    def run(self, zk_ids: list[str]) -> None:
        try:
            self._setup()

            self.stack = zk_ids
            return self._main()

        except KeyboardInterrupt:
            return None
        finally:
            curses.nocbreak()
            self.w.keypad(False)
            curses.echo()
            curses.endwin()
