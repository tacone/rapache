## Unmantained - does not work on recent Ubuntu versions.

This repository is kept for historical record only.

Rapache
=======

An Apache GUI configurator created for Ubuntu. <br/>
*(please note: it has nothing to do with R-Apache)*

**Find the source code at: [https://github.com/tacone/rapache/](https://github.com/tacone/rapache/)** <br/>
*the [launchpad project](https://launchpad.net/rapache) is deprecated and unmantained*

To know more about (story, instructions) Rapache please visit this page and try to ignore my grammar 
mistakes: My posts about Rapache

## Purpose

The goal is to let a web developer to swiftly create virtualhosts and disable/enable apache modules without messing with text-files.

## Installation

I honestly lost track of the required dependencies. This seems to work on the latest Ubuntu version:

```bash
sudo apt-get install python-crypto python-openssl python-lxml
sudo apt-get install python-glade2 python-gnome2 python-gksu2
sudo apt-get install python-gtk2 python-gtksourceview2 gksu
```

## Screenshots

Not available.

## Notes

- the project is inactive and barely mantained, just to scratch my own itches
- works only on Ubuntu and has been made with Python-Gkt
- needs sudo to run, as in `sudo ./rapache`
- it's `localhost` only, won't work via SSH

## Aknowledgments

This tool has been co-authored by [Killerkiwi](https://github.com/killerkiwi), big thanks to him.

## License

Everything is GPL3 except where otherwise noted (some files are dual licensed LGPL3/GPL3)

