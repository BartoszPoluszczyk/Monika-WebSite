# Fonts for the sidebar signature

`caveat-latin.woff2` is a locally served Latin/Polish subset of **Caveat**,
variable weight 400–700, by The Caveat Project Authors.

- Source: https://github.com/google/fonts/tree/main/ofl/caveat
- Source TTF blob: `f84acf2ce2d1b3329b194749530dbaec047e6df6`
- License: SIL Open Font License 1.1, included in `Caveat-OFL.txt`.
- Subset: U+0020–007E, U+00A0–024F, generated with fontTools/WOFF2.

`amsterdam-one.ttf` is the Amsterdam One Regular file supplied by the project
owner. It is used first for the four-line sidebar signature.

- Internal family name: `Amsterdam One`
- Supplied file name: `AmsterdamOne-eZ12l.ttf`
- The supplied file does not contain `ę`; CSS keeps Caveat as the fallback
  for that individual Polish character, so the visible text remains correct.

Body and heading fonts are unchanged. Both signature fonts are served from
this project, not a third-party CDN.
