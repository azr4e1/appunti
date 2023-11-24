import curses
from notepy.zettelkasten import Note, Zettelkasten
from notepy.zettelkasten.notes import sluggify
from typing import Optional
from pathlib import Path
from dataclasses import fields
import textwrap


LINKS_RATIO = 4


zk = Zettelkasten("/home/lorenzo/Desktop/Knowledge", "Lorenzo Drumond")


def get_id_from_link(link, zk: Zettelkasten) -> Optional[str]:
    results = zk.list_notes(show=['title', 'zk_id'])
    titles = [sluggify(title) for title, _ in results]
    with open("/home/lorenzo/log2", "a") as f:
        f.write(str(titles)+"\n")
        f.write(link + "\n")

    try:
        position = titles.index(link)
        return results[position][1]
    except ValueError:
        return None


def main(screen):
    try:
        curses.noecho()
        curses.cbreak()
        screen.keypad(True)
        curses.curs_set(False)

        screen.refresh()
        win_width = curses.COLS // LINKS_RATIO
        win = curses.newwin(curses.LINES, win_width, 0, curses.COLS-win_width)
        win.border("|", " ", " ", " ", "|", " ", "|", " ")
        win.refresh()
        links_pos = 0
        links = []
        root = Path("/home/lorenzo/Desktop/Knowledge")
        file = "4c8579262e8f19ddd7b3ee404821b236.md"
        filename = root / file
        parsing_objs = [note_obj.name for note_obj in fields(Note) if note_obj not in ['link', 'body']]
        note = Note.read(filename, parsing_objs)
        actual_links = list(note.links)
        for index, link in enumerate(actual_links):
            link = f"[{index+1}] " + link
            wrapped_links = textwrap.wrap(link, win_width-2)
            for wl in wrapped_links:
                links.append(wl)
        links_pad = curses.newpad(len(links)+1, win_width-1)
        for index, link in enumerate(links):
            links_pad.addstr(index, 1, link+"\n")
        links_pad.refresh(links_pos, 0, 0, curses.COLS-win_width+1, curses.LINES, curses.COLS)

        pos = 0
        lines = []
        simple_line = note.materialize().split("\n")
        for line in simple_line:
            if line == "":
                lines.append("\n")
            else:
                for wrapped_line in textwrap.wrap(line, curses.COLS-win_width-1):
                    lines.append(wrapped_line)
        # lines = note.body.split("\n")
        pad = curses.newpad(len(lines)+1, curses.COLS-win_width)
        for index, line in enumerate(lines):
            pad.addstr(index, 0, line)

        pad.refresh(pos, 0, 0, 0, curses.LINES, curses.COLS-win_width-1)
        # curses.doupdate()
        # screen.refresh()
        # win = curses.newwin(len(lines), curses.COLS)
        # for index, line in enumerate(lines):
        #     win.addstr(index, 0, line)
        # win.refresh()
        while (c := screen.getch()) != ord('q'):
            if c == ord('j'):
                pos += 1
            elif c == ord('k'):
                pos -= 1
            elif c == ord('g'):
                pos = 0
            elif c == ord('G'):
                pos = len(lines) - curses.LINES
                # screen.clear()
                # screen.refresh()
            elif c == ord('J'):
                links_pos += 1
            elif c == ord('K'):
                links_pos -= 1
            elif c == curses.KEY_UP:
                pos -= 1
            elif c == curses.KEY_DOWN:
                pos += 1
            elif c == curses.KEY_RESIZE:
                curses.resize_term(*screen.getmaxyx())
                screen.refresh()
                win_width = curses.COLS // LINKS_RATIO
                win = curses.newwin(curses.LINES, win_width, 0, curses.COLS-win_width)
                win.border("|", " ", " ", " ", "|", " ", "|", " ")
                links = []
                for index, link in enumerate(actual_links):
                    link = f"[{index+1}] " + link
                    wrapped_links = textwrap.wrap(link, win_width-2)
                    for wl in wrapped_links:
                        links.append(wl)
                links_pad = curses.newpad(len(links)+1, win_width-1)
                # links_pad.border("|", " ", " ", " ", " ", " ", " ", " ")
                for index, link in enumerate(links):
                    links_pad.addstr(index, 1, link+"\n")
                lines = []
                for line in simple_line:
                    if line == "":
                        lines.append("\n")
                    else:
                        for wrapped_line in textwrap.wrap(line, curses.COLS-win_width-1):
                            lines.append(wrapped_line)
                pad = curses.newpad(len(lines)+1, curses.COLS-win_width-1)
                for index, line in enumerate(lines):
                    pad.addstr(index, 0, line)
                screen.clear()
                screen.refresh()

            else:
                for index, link in enumerate(links):
                    if index+1 >= 10:
                        continue
                    if c == ord(str(index+1)):
                        new_id = get_id_from_link(actual_links[index], zk)
                        if new_id is None:
                            continue
                        pos = 0
                        links_pos = 0
                        filename = root / Path(new_id).with_suffix(".md")
                        note = Note.read(filename, parsing_objs)
                        screen.clear()
                        screen.refresh()
                        win_width = curses.COLS // LINKS_RATIO
                        win = curses.newwin(curses.LINES, win_width, 0, curses.COLS-win_width)
                        win.border("|", " ", " ", " ", "|", " ", "|", " ")
                        win.refresh()
                        links_pos = 0
                        links = []
                        actual_links = list(note.links)
                        for index, link in enumerate(actual_links):
                            link = f"[{index+1}] " + link
                            wrapped_links = textwrap.wrap(link, win_width-2)
                            for wl in wrapped_links:
                                links.append(wl)
                        links_pad = curses.newpad(len(links)+1, win_width-1)
                        for index, link in enumerate(links):
                            links_pad.addstr(index, 1, link+"\n")
                        # links_pad.refresh(links_pos, 0, 0, curses.COLS-win_width+1, curses.LINES, curses.COLS)

                        pos = 0
                        lines = []
                        simple_line = note.materialize().split("\n")
                        for line in simple_line:
                            if line == "":
                                lines.append("\n")
                            else:
                                for wrapped_line in textwrap.wrap(line, curses.COLS-win_width-1):
                                    lines.append(wrapped_line)
                        # lines = note.body.split("\n")
                        pad = curses.newpad(len(lines)+1, curses.COLS-win_width)
                        for index, line in enumerate(lines):
                            pad.addstr(index, 0, line)

                        # pad.refresh(pos, 0, 0, 0, curses.LINES, curses.COLS-win_width-1)
                        break

            if pos < 0:
                pos = 0
            elif pos >= len(lines)-1:
                pos = len(lines)-2
            if links_pos < 0:
                links_pos = 0
            elif links_pos >= len(links):
                links_pos = len(links)-1
            win.refresh()
            pad.refresh(pos, 0, 0, 0, curses.LINES-1, curses.COLS-win_width-1)
            links_pad.refresh(links_pos, 0, 0, curses.COLS-win_width+1, curses.LINES, curses.COLS)
    except KeyboardInterrupt:
        pass
    finally:
        curses.nocbreak()
        screen.keypad(False)
        curses.echo()
        curses.endwin()


screen = curses.initscr()
main(screen)
