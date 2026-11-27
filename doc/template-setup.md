# Note Type Setup

You'll have to make some adjustments to your card templates for the add-on to
work properly.

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

---

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
`jrp-front` elements. In the note type's style settings
(_Tools_ → _JRP Add-on Preferences_ → _Note Types_ → _Edit Style_) you can
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
