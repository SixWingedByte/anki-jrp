# Installing MeCab

The add-on uses [MeCab](https://taku910.github.io/mecab/) with the IPAdic
dictionary to split text into words and find their readings.

**With the `_full.ankiaddon` package you don't need to install anything.** It
includes the MeCab library for Windows (x64), macOS (Intel and Apple Silicon)
and Linux (x86-64 and ARM64) as well as the dictionary, and runs MeCab inside
Anki. This page is only needed if:

- you installed the `_no-dictionary` or `_lite` package,
- you use Windows on ARM, where the bundled Windows executable is used instead
  of the library (this works without further setup with the `_full` package),
- you turned off _Use bundled MeCab library_, or
- you want to use your own MeCab installation or dictionary.

## How the Add-on Chooses MeCab

The MeCab settings are on the _General_ tab of the add-on's preferences
(_Tools_ → _JRP Add-on Preferences..._):

1. If _Use bundled MeCab library_ is checked (the default), _Use MeCab system
   dictionary_ is unchecked, and both the library for your platform and the
   dictionary in _MeCab dictionary directory_ are present, MeCab runs inside
   Anki.
2. Otherwise, the MeCab executable is used: the one in _MeCab executable path_
   (by default the bundled `bin/mecab.exe` on Windows), or `mecab` from your
   `PATH` if _Use system-wide MeCab executable_ is checked (the default on macOS
   and Linux). With _Use MeCab system dictionary_, MeCab uses the dictionary
   configured in its own installation instead of _MeCab dictionary directory_.

If the library can't be loaded, the add-on falls back to the executable
automatically.

## Troubleshooting

### Dictionary not found

"The MeCab dictionary wasn't found", or an error like `Mecab error: invalid
line: param.cpp(69) [ifs] no such file or directory: ...\data\ipadic\dicrc`,
means there's no dictionary where the add-on expects it. Install the
`_full.ankiaddon` package (called `_ipadic.ankiaddon` up to version 0.3), or
install a MeCab dictionary yourself and either set _MeCab dictionary directory_
to it or check _Use MeCab system dictionary_.

### Executable not found

`Mecab error: executable not found` means the add-on is using the executable
(see [above](#how-the-add-on-chooses-mecab)) and can't find it. Either install
the `_full` package and keep _Use bundled MeCab library_ checked, or install
MeCab as described below and set its path.

## macOS

MeCab is available through [Homebrew](https://formulae.brew.sh/formula/mecab)
and [MacPorts](https://ports.macports.org/port/mecab/).

### Setting the Executable Path

#### Executable not found

If trying to use the add-on's syntax generator results in `Mecab error:
executable not found` you'll need to manually set the path to your MeCab
executable:

1. Determine the location of the executable by running `which mecab` in the
   terminal.  
   If that command doesn't return a path try looking for a file named `mecab`
   in `/opt/homebrew/bin/` (Homebrew) or `/opt/local/bin/` (MacPorts).
2. Enter the full path including the final `mecab` into `MeCab executable path`
   in the add-on's preferences (_Tools_ → _JRP Add-on Preferences..._) and
   uncheck `Use system-wide MeCab executable`.

#### Missing `mecabrc`

If you get an error like `Mecab error: invalid line: param.cpp(69) [ifs]
no such file or directory: /path/to/mecabrc`, run `touch /path/to/mecabrc` to
create the file in question, where the path is whatever was reported in the
error message. (If the path ends in `dicrc` instead, see
[Dictionary not found](#dictionary-not-found).)

---

Please report any macOS-related issues that aren't mentioned here.

## Linux

Your distro might have a MeCab package, for example:

- [Ubuntu](https://packages.ubuntu.com/search?keywords=mecab)
- Arch (AUR): [mecab](https://aur.archlinux.org/packages/mecab),
  [mecab-git](https://aur.archlinux.org/packages/mecab-git)

If you can't find anything, compile MeCab yourself by following the instructions
below.

### Requirements

- A C++ compiler. Ideally g++ which, if it isn't installed already, should be
  available in a package called `gcc`, `g++`, or similar on most distros. Check
  if it works by running `g++ --version`.
- `libiconv`. Probably already present as part of glibc.
- `git`, for cloning the repo. You can also skip step 1 below by using the
  source tarball linked here instead: https://taku910.github.io/mecab/#download

### Compile & Install

1. Clone the repository: `git clone https://github.com/taku910/mecab.git`
2. cd into the `mecab` directory in the repo. It should contain a file
   called `configure`.
3. Run this command:  
   ```./configure --prefix=/usr --sysconfdir=/etc --libexecdir=/usr/lib --with-charset=utf-8```  
   For some distros the prefix and directories might be different.
4. If `configure` finished without errors, run `make` (and ensure it succeeds).
5. Create a temporary target directory.
6. Run `make DESTDIR="<tgt dir>" install`, where `<tgt dir>` is the absolute
   path of the directory you just made.
7. Copy or move `<tgt dir>/usr/bin/mecab` and `<tgt dir>/usr/lib/libmecab.so.2`
   to a new directory. Create an empty file named `mecabrc` in the same
   directory.
8. In the add-on's preferences menu, uncheck _Use system-wide MeCab executable_
   and set _MeCab executable path_ to where you put the `mecab` executable in
   the previous step.

Alternative to step 5-8 you could also create and install a custom package, in
which case you can leave the add-on settings on their default values.
