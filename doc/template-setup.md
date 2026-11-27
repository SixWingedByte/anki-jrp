# Note Type Setup

You'll have to make some adjustments to your card templates for the add-on to
work properly. After changing the templates, add the note type on the _Note
Types_ tab of the add-on's preferences (_Tools_ → _JRP Add-on Preferences..._)
and save, so the add-on inserts its card script and stylesheet.

## Example

For a note type with the fields _Front_ and _Back_, the front template could be:

```html
<div class="jrp-front" data-jrp-generate>{{Front}}</div>
```

And the back template:

```html
{{FrontSide}}

<hr id=answer>

<div data-jrp-generate>{{Back}}</div>
```

On the front, furigana, coloring and graphs are hidden by default (see
[Card Front](#card-front)); on the back, both fields are shown in full. The
add-on adds its script below your templates and its styles to the note type's
styling, in sections marked as managed by the add-on. Don't edit those
sections, since the add-on replaces them when it's updated.

## Fields

Every field that furigana and accent highlighting should be generated for needs
to be enclosed in an HTML element with the attribute `data-jrp-generate`.

If you previously used the Migaku Japanese Add-on you'll likely have lines like
this somewhere in your templates:

```html
<div display-type="kanji" class="wrapped-japanese">{{Sentence}}</div>
```

Those can be replaced with this:

```html
<div data-jrp-generate>{{Sentence}}</div>
```

If you didn't use the Migaku Add-on before, all you need to do is find the tag
(in `{{`/`}}`) for the field you want to generate from, and place HTML tags
around it like in the line above.

`{{FrontSide}}` works in back templates. Content from the front is shown in
full on the back, even if it's inside an element with the class `jrp-front`.

Fields shown with Anki's `{{furigana:Field}}` filter (for
[Anki's built-in furigana syntax](/README.md#ankis-built-in-furigana-syntax))
must not be inside a `data-jrp-generate` element.

### Options

The attribute's value can hold options, separated by `;`:

- `migaku`: interpret the field as [Migaku syntax](#migaku-syntax).
- `enclose-empty-units`: wrap words without accent information in the same
  elements as words with accents, for example to style all words alike.

For example: `<div data-jrp-generate="migaku;enclose-empty-units">{{Sentence}}</div>`.
The options are read when a card is shown, so changing them doesn't require
regenerating anything.

## Migaku Templates

If you enable _Migaku style_ in the note type's style settings, templates made
for the Migaku Japanese add-on also work as they are: elements like
`<div display-type="coloredhover" class="wrapped-japanese">{{Expression}}</div>`
are treated as Migaku syntax, and their display type decides how furigana and
coloring are shown (`hover` types: furigana on hover; `kanjireading` and
`reading` types: always; `kanji` types: never; types without `colored`: no
coloring). Remove the Migaku add-on's own script first with the
_Remove MIA/Migaku_ button on the _Note Types_ tab.

## Migaku Syntax

If you have existing notes with Migaku syntax and don't want to upgrade to the
improved syntax you can tell the card script to interpret your fields in Migaku
mode by setting the attribute's value to `migaku`:

```html
<div data-jrp-generate="migaku">{{Sentence}}</div>
```

## Card Front

Any fields on the front of the card also need to be children of an element with
the class `jrp-front`. This can be the element with the generate attribute:

```html
<div class="jrp-front" data-jrp-generate>{{Sentence}}</div>
```

Or any enclosing element:

```html
<div class="jrp-front">
	<div data-jrp-generate>{{Sentence}}</div>
</div>
```

By default, furigana, coloring, indicators and graphs are hidden inside
`jrp-front` elements, so the front doesn't give away the reading. This can be
turned off with _Hide information on the front of cards_ in the note type's
style settings (_Tools_ → _JRP Add-on Preferences..._ → _Note Types_ → _Edit
Style_). In the same dialog, under _Show on hover or tap on the front_, you can
choose what to reveal while hovering over a word. On devices without a mouse,
such as AnkiDroid or AnkiMobile, tapping a word reveals the same things and
tapping it again hides them.

## Vertical Writing

Vertical writing (縦書き) is fully supported. Simply add the class `jrp-vertical`
to an element and all generated elements below it will use vertical styling. The
class doesn't enable vertical writing mode by itself, but you can change that by
adding this to your note type's style sheet:

```css
.jrp-vertical {
	writing-mode: vertical-rl;
}
```
