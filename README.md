<!--toc:start-->
- [Description](#description)
- [Roadmap](#roadmap)
  - [Core](#core)
  - [Plugins](#plugins)
<!--toc:end-->

# Description

CLI note manager for Zettelkasten-like note-taking.


# Roadmap

## Core
- [x] Add `last_changed_time` in sqlite database
- [x] Support for tags
- [x] Support for backlinks
- [x] Search for tags, links, words, title, date
- [x] SQLite caching of indexed notes
- [x] Support for reindexing
  - [ ] support strict mode for reindexing. Perform thorough check of notes validity.
- [x] pager to navigate between notes by following links
  - [ ] Better note highlighting
  - [ ] refactor of pager
- [x] interactive search
  - [ ] refactor of interactive selector
- [ ] Find broken links
- [ ] Knowledge graph creation
- [ ] REPL
- [ ] Support for using external or internal tool for fuzzy finding/searching
- [ ] Support for TOML configuration
- [ ] Plugin system?

## Plugins
- [ ] AI for categorisation and grouping of notes
- [ ] AI for tag creation
- [ ] AI for summarisation of notes
- [ ] Select multiple notes and summarise them into one
- [ ] PDF summarizer
- [ ] flashcards
- [ ] Daily/Weekly/Monthly knowledge summarization (using git/langchain)
