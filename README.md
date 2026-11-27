# Japanese Readings and Pitch Accent Add-on

This Anki add-on allows automatically generating readings (furigana) and pitch
accent information for an entire field with a single button press. It can also
convert any amount of cards in bulk, or fill in fields automatically when notes
are added.

This is a fork of [Ben Kerman's add-on](https://github.com/Ben-Kerman/anki-jrp),
updated for Anki 26.09 and extended with: MeCab that runs inside Anki on
Windows, macOS and Linux, automatic generation for new notes, output in Anki's
built-in furigana syntax, reveal-on-hover/tap options for the card front, a
Migaku style, particle pitch in the accent graph, `{{FrontSide}}` support, and
dictionary data rebuilt from current sources.

<img src="https://i.imgur.com/8NFw0HB.png">

The add-on is currently experimental and you'll probably encounter bugs or
crashes. Data corruption is extremely unlikely (probably even impossible), the
specific notes being changed aside, but you should still make backups,
especially when bulk converting notes, and enable Anki's built-in automatic
backups if you haven't already.  
[See below](#reporting-issues) for details on how to report issues.

## Getting Started

1. Use Anki 26.09 or later. Both Anki's regular editor and its experimental
   new editor are supported.
2. Download the file ending in `_full.ankiaddon` from the
   [latest release](https://github.com/SixWingedByte/anki-jrp/releases/latest)
   and install it with _Tools_ → _Add-ons_ → _Install from file..._ (or by
   double-clicking it). The version on AnkiWeb is the original add-on without
   the changes in this fork.
    - The `full` file contains everything the add-on needs out of the box:
      pitch accent data, MeCab and its dictionary. MeCab runs inside Anki on
      Windows (x64), macOS and Linux, so there's nothing else to install.
      (Up to version 0.3 this file was called `ipadic`.)
    - The `no-dictionary` file has everything except the MeCab dictionary,
      which you then need to install yourself and select in the preferences.
      (Up to version 0.3 this file was called `full`.)
    - The `lite` file contains only the add-on itself, which means you will
      need to supply your own pitch accent/variant data and install MeCab as
      well as a MeCab dictionary for it to use externally; see
      [Installing MeCab](/doc/mecab.md).
3. Restart Anki, open the _Manage Note Types_ menu (`Ctrl`+`⇧`+`N`) and set up
   your templates as described in the [note type setup](/doc/template-setup.md).
4. Open the add-on's preferences (_Tools_ → _JRP Add-on Preferences..._), go to
   the _Note Types_ tab, then select and _Add_ all note types you set up in the
   last step.  
   Click _Remove MIA/Migaku_ for any note types you previously used the Migaku
   Japanese Add-on with to remove the script and styling from that add-on,
   otherwise this add-on will not work properly.
5. Save your preferences. The add-on inserts its card script and stylesheet
   into the note types you added. You should now be able to preview or review
   any cards that contain reading/accent syntax with furigana and accent
   coloring / indicators.

When you update the add-on, the script and stylesheet in your note types are
updated automatically the next time Anki starts. Only the sections marked as
managed by the add-on are changed.

## Adding Readings and Pitch Accent Information

### Individual

To generate or remove readings and accent info for a single note, open it in
the Anki browser or the _Add_ window, focus the field you want to change and
click one of the conversion buttons at the right of the editor toolbar or press
the associated shortcut:

| Shortcut | Result |
|---|---|
| `F2` | Generate readings and accents in the [default syntax](#default) |
| `Ctrl`+`F2` | Generate readings and accents in [Migaku syntax](#migaku) |
| `Shift`+`F2` | Generate readings in [Anki's built-in furigana syntax](#ankis-built-in-furigana-syntax) |
| `F4` | Remove all reading/accent syntax and restore the plain text |

Running a conversion again on a field that already contains syntax regenerates
it.

### Anki's Built-in Furigana Syntax

Readings can also be written in Anki's own furigana syntax (`日本[にほん]の
辞書[じしょ]`), which the built-in `{{furigana:Field}}` filter displays without
this add-on, for example in shared decks. Use the button next to the other
conversion buttons (`Shift`+`F2`) or the _Anki furigana_ type in bulk
conversion. This syntax can't hold pitch accent information, and fields in it
should be shown with `{{furigana:Field}}` rather than inside a
`data-jrp-generate` element. _Remove_ (`F4`) works on it as well.

### Automatically When Adding Notes

In the add-on's preferences, on the _Note Types_ tab, enter the names of the
fields to fill in under _Auto-generate fields_ (comma-separated, e.g.
`Sentence, Word`). Whenever a note of that type is added, through Anki's Add
screen or from another add-on such as AnkiConnect (used by Yomitan), those
fields get readings and accents in the default syntax. Fields that are empty
or already contain reading/accent syntax are left alone, and a note is always
added, even if generation fails.

### Bulk Conversion

The _Notes_ entry in the browser's menu bar contains an action for converting
notes in bulk.

Select any notes you want to change, choose the bulk conversion action from the
menu bar, adjust the configuration dialog to what you want and click _Convert_.
All notes need to be of the same note type, since it wouldn't be possible to
determine the target field otherwise.

With the _Default_ and _Migaku_ conversion types, any notes that already contain
reading/accent syntax will be converted directly to the closest equivalent in
the target syntax without regenerating (unless the corresponding option is
checked), or left unchanged if the existing syntax type is the same as the
target.

If you're converting large amounts of notes, such as sentence mining decks
containing hundreds or thousands of cards, make sure to back everything up
before running the conversion. Exporting the deck(s) with scheduling information
(but without media, since the conversion only changes the notes themselves)
should be sufficient.

## Card Display

How readings and accents look on cards is set per note type in the add-on's
preferences: _Tools_ → _JRP Add-on Preferences..._ → _Note Types_ → _Edit
Style_. Save the preferences afterwards to apply changes to the note type.

- **Coloring and indicators:** every word is colored by its accent pattern
  (heiban, atamadaka, nakadaka, odaka, kifuku) and gets an indicator: bars by
  default, or diamonds with _Use diamond indicators_. The colors can be changed
  in the same dialog.
- **Accent graph:** hovering over a word shows a graph of its pitch, written in
  katakana (in hiragana with _Migaku style_). With _Show particle pitch in
  graph_ (on by default), a faded `◌` after the word shows the pitch of a
  following particle: high after heiban words, low after accented ones, which
  is how e.g. 端が (heiban) and 橋が (odaka) differ.
- **Front of the card:** with _Hide information on the front of cards_ (on by
  default), furigana, coloring, indicators and graphs are hidden in elements
  with the class `jrp-front` (see the [note type setup](/doc/template-setup.md#card-front)).
  Under _Show on hover or tap on the front_ you can choose any of these to
  appear while hovering over a word. On devices without a mouse, such as
  AnkiDroid or AnkiMobile, tapping a word shows them and tapping it again hides
  them.
- **Migaku style:** makes cards look like the Migaku Japanese add-on: diamond
  indicators, a hiragana graph with pattern labels (H, A, N3, O, K2) below it,
  and furigana only while hovering over or tapping a word. Templates made for
  the Migaku add-on also work with it as they are; see
  [migrating](#migrating-from-the-migaku-japanese-add-on).
- **Vertical writing** is supported; see the
  [note type setup](/doc/template-setup.md#vertical-writing).

## Syntax

The add-on supports its own fully-featured syntax and is also compatible with
the syntax from the old Migaku Japanese Add-on.

### Default

In the default syntax, readings are written in square brackets with kanji on the
left and furigana on the right separated by a `|`, like `[振|ふ]り[仮名|がな]`.  
Words with pitch accent information are enclosed in curly braces that contain
the word (including reading tags) itself and accent information after a
semicolon: `{[受|う]け[入|い]れる;Y4,0}`.

The accent information normally consists of a comma-separated list of numbers,
each representing the accented mora, or 0 for unaccented (平板) words. The only
special cases are unknown accents marked with a `?`, which can only occur by
converting from Migaku syntax, and split accents like 一目瞭然 (いち↓もく・りょ→うぜん)
which are composed of several parts separated by dashes. Each part consists of
the number of the accented mora, an `@` sign, and the number of moras it applies
to. For example: `{[一目瞭然|いちもくりょうぜん];2@4-0@4,0}`.

An `!` and `Y` can be placed before the actual pitch accent information.  
Exclamation marks indicate ambiguous accents, such as for many kana-only words
or certain words with multiple accents. The add-on automatically inserts
ambiguity marks if it found more than one possible set of accents with the same
reading for a word. You should then manually look up the words in question and
adjust the accent tags as necessary.  
If present, a Y (from 用 as in 活用・用言) will cause all accents other than [0]
to be displayed as the kifuku (起伏) pattern. Ys are added to all words identified
as 動詞 (verbs) or 形容詞 (i-adjectives) by MeCab.

Base readings for conjugated words can be indicated in two ways, inline
like `{[行|い][って=く];Y0}`, or after the accent(s) like `{[来|き]た;Y1|くる}`.

### Migaku

For backwards compatibility, Migaku-style syntax is also supported, but it has
some limitations compared to the new syntax:

- Only one reading per word is possible, leading to furigana frequently
  duplicating characters from the word, like <ruby>この先<rt>このさき</rt></ruby>,
  <ruby>付き合<rt>つきあ</rt></ruby>う or <ruby>変わり身<rt>かわりみ</rt></ruby>.
- The base reading of conjugable words must always be included in full, even the
  part identical to the reading of the conjugated form. This is also true if the
  base reading and actual reading are the same, so the Migaku version of what
  would be `{[陥|おとしい]れる;Y5,0}` in default syntax is `陥[おとしい,おとしいれる;k5,h]れる`.
- Since words are space-separated, regular ASCII spaces can't be represented
  properly and are replaced with en spaces (U+2002).
- Ambiguous accents can't be marked and thus won't be highlighted.
- Split accents can't be accurately represented and will be displayed as
  unknown.

## Migrating from the Migaku Japanese Add-on

Follow the guide to [getting started](#getting-started) above, including
_Remove MIA/Migaku_ for your existing note types.

To keep the look of the Migaku add-on, enable _Migaku style_ in the note type's
style settings: diamond indicators, a hiragana accent graph with pattern labels
(H, A, N3, O, K2), and furigana only while hovering over or tapping a word.
With it, Migaku templates (`class="wrapped-japanese"` with a `display-type`)
also work without changes; see the [note type setup](/doc/template-setup.md#migaku-templates).
You'll need to manually transfer your accent pattern colors to the note type
style settings if you want to keep them. The add-ons have different default
colors.

You can easily migrate existing notes to the new syntax without losing any
manual changes by selecting them in the browser and
[bulk converting](#bulk-conversion) them with the _Default_ conversion type as
long as _Regenerate contents_ is disabled. Make sure to back up all notes in
case there are bugs in the conversion algorithm.

## Data Sources and Licenses

The packages built by this repository's GitHub workflow include:

- **Word variants** (`data/variants.xz`), generated from the
  [JMdict](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project)
  dictionary file, which is the property of the
  [Electronic Dictionary Research and Development Group](https://www.edrdg.org/)
  and used in conformance with the group's
  [licence](https://www.edrdg.org/edrdg/licence.html) (CC BY-SA 4.0). It's
  rebuilt from the current JMdict for every release.
- **Pitch accents** (`data/accents.xz`) from
  [Kanjium](https://github.com/mifunetoshiro/kanjium) (CC BY-SA 4.0): "The
  pitch accent notation, verb particle data, phonetics, homonyms and other
  additions or modifications to EDICT, KANJIDIC or KRADFILE were provided by
  Uros O. through his free database." Words not in Kanjium use the pitch
  accent data from earlier releases of this add-on, which was compiled for the
  Migaku Japanese add-on from several dictionaries.
- **MeCab** with the IPAdic dictionary, and MeCab libraries for macOS and
  Linux taken from [fugashi](https://github.com/polm/fugashi) (MIT; MeCab is
  BSD-3-Clause). The license texts are included in the `lib` folder.

The data files are licensed under CC BY-SA 4.0 as adaptations of the above.

## Troubleshooting

- **"The MeCab dictionary wasn't found"**, or a MeCab error mentioning
  `param.cpp(69)` and `ipadic\dicrc`: the installed package doesn't include
  the MeCab dictionary. Install the `_full.ankiaddon` file (called
  `_ipadic.ankiaddon` up to version 0.3). Other MeCab problems are covered in
  [Installing MeCab](/doc/mecab.md#troubleshooting).
- **Cards show the raw syntax** (like `{[辞書|じしょ];1}`) instead of furigana:
  the note type hasn't been added on the _Note Types_ tab of the preferences,
  _Manage script_ is unchecked for it, or the field isn't inside an element
  with `data-jrp-generate` (see the [note type setup](/doc/template-setup.md)).
- **`⚠ Error during parsing: invalid segment`** on a card: the field's syntax
  doesn't match what the template expects. Fields in Migaku syntax
  (`辞書[じしょ;a]`) need `data-jrp-generate="migaku"` in the template, fields
  in the default syntax (`{[辞書|じしょ];1}`) a plain `data-jrp-generate`.
  Converting the field with `F2` or `Ctrl`+`F2` also fixes it.
- **"Dictionary is not (yet) loaded"**: the pitch accent data is still being
  loaded in the background after Anki started. Wait a moment and try again.

## Development

Building the add-on, running the tests, the GitHub workflow and how to make a
release are described in [Development](/doc/development.md).

## Reporting Issues

If you encounter a bug or crash while using the add-on please report it by
opening a GitHub issue in this repository.

Explain what you were doing when the issue occurred as accurately as possible,
ideally with a list of steps to reproduce it. If the problem is related to
specific cards, consider including an `.apkg` export of those cards (_Notes_
→ _Export Notes..._ in the Anki browser while having the cards in question
selected). If there was an error message include its full contents as well, if
possible as selectable text.
