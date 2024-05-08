<!--toc:start-->
- [Description](#description)
- [Commands](#commands)
- [Interactive selection](#interactive-selection)
- [Pager](#pager)
  - [Keybindings](#keybindings)
- [Roadmap](#roadmap)
  - [Core](#core)
  - [Plugins](#plugins)
<!--toc:end-->

# Description

CLI note manager for Zettelkasten-like note-taking.

This tool allows you to keep track of your notes and of the links between them. You can easily create, delete, list and filter and browse your notes. You can also set up a git repository to keep track of changes and setup a remote repository.

You'll need an editor of your choice to edit the notes. You can set this by modifying the `EDITOR` or `VISUAL` environment variable, or by setting the `---editor flag`.

Future versions will support a configuration TOML file.

This is also a library that you can import with `import appunti`. The main packages are `appunti.zettelkasten.notes` and `appunti.zettelkasten.zettelkasten`

# Commands
You can see all the flags and commands available by typing

```bash
appunti --help
```

    usage: appunti [-h] [--vault VAULT] [--author AUTHOR] [--autocommit]
                  [--autosync] [--editor EDITOR] [--version]
                  {initialize,new,edit,open,delete,print,list,reindex,next,sync,commit,info,browse}
                ...

    Zettelkasten manager

    positional arguments:
      {initialize,new,edit,open,delete,print,list,reindex,next,sync,commit,info,browse}
        initialize          Initialize the vault.
        new                 Create a new note.
        edit                Open an existing note by ID to edit.
        open                Open the selected notes without affecting index and
                          .last
        delete              Delete a note by ID.
        print               Print the note by ID.
        list                List all the notes.
        reindex             Reindex the vault.
        next                Create new note continuing from last one.
        sync                Commit and sync with remote repository if available.
        commit              Commit current changes to repo.
        info                Show metadata for a note.
        browse              Browse the Zettelkasten.

    options:
      -h, --help            show this help message and exit
      --vault VAULT         Location of the vault.
      --author AUTHOR       Author name.
      --autocommit          Whether to commit the git repo at every action.
      --autosync            Whether to push to remote origin at every action.
      --editor EDITOR       Editor to use.
      --version             show program's version number and exit


To drill down and see the flags and use of a single command, you can call for help directly on that command:

```bash
appunti browse --help
```

    usage: appunti browse [-h] [zk_id ...]

    positional arguments:
      zk_id       ID of the note to show.

    options:
      -h, --help  show this help message and exit


Each note is attributed with a hash which represents it uniquely. This means that notes don't need to have unique titles (but that helps).

A newly created note will look like this:

```markdown
---
title: Hello World
author: Lorenzo Drumond
date: 2023-11-29T01:16:21
last: 2023-11-29T01:16:21
zk_id: 56681eea01d3435a3349cf3ee659c20a
tags:
---


# Hello World

# References
```

Links are surrounded by double square brackets. They are parsed independently on where they are inserted inside the note (as long as it's after the frontmatter)

Tags are identified by a leading `#` and can only contain `_` as special character.

Notes are indexed in a sqlite database. If you make changes to notes without using `appunti`, you'll have to reindex the database in order to make sure it reflects the most recent changes.

# Interactive selection

This selection is supported by almost all commands if you don't provide them with their argument.

- You can filter the selection by title by just typing normally, or you can exclude titles by preprending `!` in front of what you're typing.
- You can filter by tag by prepending `#`, or exclude tags by prepending `#!`
- You can filter by link by surrounding the text inside double brackets, or you can exclude links by surrounding with double brackets and prepending with `!`

You can select multiple notes by pressing `*`. You can select/deselect all notes by pressing CTRL-A.

Pressing ENTER will select the note under the cursor if multi-selection is activated, or the notes marked with `*`, and trigger the command with the notes selected.

# Pager

The pager is activated with the command `appunti browse`. This is an easy way to scroll through your notes and follow links as you read.

## Keybindings

| Key | Action | Description |
|-----|--------|-------------|
| s | Launch interactive selection | Select notes and append them to the current note stack |
| r | Reload note | Reload current note, showing any pending change |
| d | Delete note | Delete note from current stack (not from zettelkasten) |
| D | Delete stack | Delete everything except current note |
| 1 - 9 | Follow link | Follow link denoted by number, replacing the stack ahead with new note |
| # | Select link | Prompts you to select link by number higher than 9 |
| n | Next note | Create a new note using same links and tags as current note, and edit it |
| N | New note | Create a new note and edit it |
| j | Scroll Down ||
| J | Scroll links list down ||
| k | Scroll up ||
| K | Scroll links list up ||
| g | Top of note ||
| G | End of note ||
| CTRL-D | Half-page down ||
| CTRL_U | Half-page up ||
| h | move to left of note stack ||
| l | move to right of note stack ||
| H | move to start of stack ||
| L | move to end of stack ||

N.B. Links supported for now are only sluggified versions of link title. Future versions will support full title and file name as well.


# Roadmap

## Core
- [x] Support for tags
- [x] Support for backlinks
- [x] Search for tags, links, words, title, date
- [x] SQLite caching of indexed notes
- [x] Support for reindexing
- [x] pager to navigate between notes by following links
- [x] interactive search
- [ ] support filename reference and full title reference for links
- [ ] Find broken links
- [ ] Knowledge graph creation
- [ ] Support for using external or internal tool for fuzzy finding/searching
- [ ] Support for TOML configuration
- [ ] Plugin system

## Plugins
- [ ] AI for categorisation and grouping of notes
- [ ] AI for tag creation
- [ ] AI for summarisation of notes
- [ ] Select multiple notes and summarise them into one
- [ ] PDF summarizer
- [ ] flashcards
- [ ] Daily/Weekly/Monthly knowledge summarization (using git/langchain)
