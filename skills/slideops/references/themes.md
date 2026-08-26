# Theme presets

The template's entire look derives from the single `:root` token block at the top of
`assets/template.html` (every tint and border is `color-mix`-derived from these tokens).
**Switching theme = replacing that one block wholesale.** Each preset below is a complete
drop-in replacement; after pasting it, the only line you might still touch is `--font`
(and `--mono`) if the user chose a font from § Font options. The default block's role
comments are optional and the presets omit them.

After swapping, confirm no literals escaped the block:
`grep -nE "rgba?\(|#[0-9a-fA-F]{3,6}\b" deck.html` must only hit lines inside `:root`
(plus any inline SVG you embedded, whose colors are baked at render time).

Offer these in the intake as one-liners, default first:

- **Ledger Light** (default): warm paper surfaces, deep olive accent, dark code blocks;
  reads well in bright rooms, on projectors, and on paper.
- **Ledger Dark**: the default after dark. Warm espresso surfaces and a soft gold accent,
  the same warm family as the light theme rather than a separate design. Pick this when
  the deck is presented in a dim room or embedded in dark docs.
- **Midnight**: deep navy + sky-blue accent; calm, corporate-friendly dark.
- **Graphite**: near-black neutral + amber accent; highest contrast, projector-safe.
- **Match a brand**: user gives a site/style guide; extract real values per
  style-guide.md § Theming and map them onto the token roles below.

Ledger Light and Ledger Dark are a matched pair: one warm family, with the surface/ink
roles inverted and the accent moved from deep olive to soft gold so it holds up on dark
surfaces. Offering "the same deck, dark" is therefore a one-block swap with no redesign.

## Ledger Light (default)

Already in the template; shown here for reference when mapping a brand.

```css
:root{
  /* surfaces */
  --bg:#faf6ee; --bg2:#f2ecdf; --card:#ffffff; --code-bg:#2b2820;
  --stage-1:#e8e0cf; --stage-2:#cfc6b2;
  --section-1:#f4eede; --section-2:#e6dcc6;
  /* text */
  --fg:#2b2620; --text:#3d372e; --strong:#171310; --muted:#8a8069;
  /* roles */
  --accent:#7a7f1f; --accent2:#5f6419; --warn:#a34a3f; --bad:#b5544a;
  /* code block */
  --code-fg:#e8dfc0; --code-comment:#948b74; --code-keyword:#d3c87a; --code-string:#c9b98a;
  /* title gradient: dark ink to accent */
  --grad-1:#2b2620; --grad-2:#7a7f1f;
  /* misc */
  --card-border:color-mix(in srgb, var(--muted) 30%, transparent);
  --img-bg:#ffffff; --shadow:rgba(60,50,30,.25); --radius:14px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --mono: "SFMono-Regular", Consolas, Menlo, "Liberation Mono", monospace;
}
```

Light-theme check: tinted tags and cards derive from the accent, so after building,
screenshot a slide of each pattern you used and confirm tag text stays readable. If one
is too faint, darken that role token (not the tint percentages).

## Ledger Dark

The default's night-time counterpart: the same warm family, with espresso surfaces in
place of paper and a soft gold accent where the light theme uses deep olive. Warm all the
way through, including the code block.

```css
:root{
  /* surfaces */
  --bg:#1b1814; --bg2:#241f19; --card:#2b251e; --code-bg:#141110;
  --stage-1:#312a21; --stage-2:#14110e;
  --section-1:#282219; --section-2:#17130f;
  /* text */
  --fg:#f7f3ea; --text:#e7dfd0; --strong:#ffffff; --muted:#a4977e;
  /* roles */
  --accent:#c3a94a; --accent2:#9d8636; --warn:#c96a4f; --bad:#d1735c;
  /* code block */
  --code-fg:#e8dfc0; --code-comment:#8b7f68; --code-keyword:#e0c274; --code-string:#c9b98a;
  /* title gradient: white to accent */
  --grad-1:#ffffff; --grad-2:#e0c274;
  /* misc */
  --card-border:color-mix(in srgb, var(--muted) 22%, transparent);
  --img-bg:#ffffff; --shadow:rgba(0,0,0,.55); --radius:14px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --mono: "SFMono-Regular", Consolas, Menlo, "Liberation Mono", monospace;
}
```

## Midnight

```css
:root{
  --bg:#12161f; --bg2:#1a2130; --card:#1e2636; --code-bg:#0d111a;
  --stage-1:#233047; --stage-2:#0d1017;
  --section-1:#1f2940; --section-2:#10141d;
  --fg:#f2f5fa; --text:#d8dfeb; --strong:#ffffff; --muted:#8b98b0;
  --accent:#5aa9e6; --accent2:#4a90c2; --warn:#e6a15a; --bad:#e05c6e;
  --code-fg:#a8c7e8; --code-comment:#5d6b84; --code-keyword:#7ab8f0; --code-string:#9fd0a8;
  --grad-1:#ffffff; --grad-2:#a8d4f5;
  --card-border:color-mix(in srgb, var(--muted) 18%, transparent);
  --img-bg:#ffffff; --shadow:rgba(0,0,0,.55); --radius:14px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --mono: "SFMono-Regular", Consolas, Menlo, "Liberation Mono", monospace;
}
```

## Graphite

```css
:root{
  --bg:#161616; --bg2:#1f1f1f; --card:#242424; --code-bg:#101010;
  --stage-1:#2c2c2c; --stage-2:#0e0e0e;
  --section-1:#262626; --section-2:#121212;
  --fg:#fafafa; --text:#e4e4e4; --strong:#ffffff; --muted:#9a9a9a;
  --accent:#e8c547; --accent2:#c2a63c; --warn:#e07b39; --bad:#e05c5c;
  --code-fg:#e8dfc0; --code-comment:#7d7d6a; --code-keyword:#f0d47a; --code-string:#d8c68f;
  --grad-1:#ffffff; --grad-2:#f0dc8f;
  --card-border:color-mix(in srgb, var(--muted) 18%, transparent);
  --img-bg:#ffffff; --shadow:rgba(0,0,0,.55); --radius:14px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --mono: "SFMono-Regular", Consolas, Menlo, "Liberation Mono", monospace;
}
```

## Font options

Swap `--font` (and `--mono` if asked). All stacks are system fonts: no webfont downloads,
decks stay self-contained and identical offline.

| Choice | `--font` value |
|---|---|
| Modern sans (default) | `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif` |
| Humanist | `"Gill Sans", "Segoe UI", Verdana, sans-serif` |
| Editorial serif | `"Iowan Old Style", "Palatino Linotype", Georgia, serif` |
| Mono-flavoured | keep default `--font`, and set headings only: add `h1,h2,.kicker{font-family:var(--mono);letter-spacing:0;}` |

If the user picks a serif or mono-flavoured look, re-run the visual pass on text-heavy
slides: metrics differ and previously-fitting lines may wrap.

## Mapping a brand onto the tokens

Extract real values (style-guide.md § Theming), then fill roles in this order:
`--accent` (the brand's primary), `--bg/--bg2/--card` (its dark surface family, or a
neutral dark if the brand is light-only and the user wants dark), `--warn/--bad` (its
warning/danger colors if defined, else keep the preset's), text tokens by contrast against
your chosen surfaces. Leave the `color-mix` tints alone: they follow the roles
automatically.
