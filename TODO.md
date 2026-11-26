# TODO

## Ladda ner metadatafilen för kartblad (ortofoto)

**Status:** kryssruta byggd och dokumenterad på grenen `seamlines` (pushad, ej mergad, ej släppt, versionsnumret är fortfarande 1.1.2). Kvar: versionsnummer och release, samt att testa hel-fil-nedladdning med metadata och rutor som saknar metadatafil i QGIS.

Önskemål från en användare: möjlighet att välja att även ladda ner kartbladens
metadatafil, t.ex. `.json` med sömlinjer (seamlines).

- Bekräftat av användaren: önskemålet gäller sömlinjer för **historiska ortofoton**.
- Bekräftat att pluginet redan hittar dem: sökning med flygår 1950–2026 ger träffar i
  kollektioner som `orto-historiska-1960-1969`, `orto-historiska-1970-1979` och
  `orto-historiska-2000-2004` (bildtyp `pan`, 0,5–1 m, 14–88 MB per ruta), bredvid
  vanliga `orto-a-2006`.
- **Sömlinjer finns även för historiska ortofoton** (bekräftat i praktiken för
  `orto-historiska-1960-1969`), trots att produktdokumentationen (Informationsinnehåll,
  version 2025.02) säger att de saknas för 1949–2005 och för 2006–2009. Filen
  `<ruta>_flygbild.json` ligger på publik sökväg `/bild/pub/` (ingen inloggning) och är
  en GeoJSON `FeatureCollection` i EPSG:3006 med `bildidentitet` och `tidpunkt` per
  flygbild. Alla rutor har inte nödvändigtvis filen; pluginet hoppar över dem som saknar
  `metadata`-asset (`application/geo+json`, bekräftat även för `orto-l2-2019`).
- Klart på grenen: kryssruta "Hämta även metadatafil med sömlinjer (.json)" (bara för
  ortofoto), sparas som `<utdatamapp>/<kollektion>/<ruta>_flygbild.json` efter bilderna.
- Kvar: README/docs/CHANGELOG, versionsnummer, test av dialogen i QGIS, och att fråga
  användaren om flera år i samma mosaik (här hade alla delbilder samma datum).

## Svar från Lantmäteriet (nov 2026) – att åtgärda

Avvaktar eventuella fler kommentarer från Lantmäteriet innan något ändras.

- **Betalda produkter i ortofotokatalogen:** STAC-bild kan, precis som STAC-hojd,
  innehålla avgiftsbelagda produkter (t.ex. Ythöjdmodell Nedladdning). Kontrollera
  om ortofotosökningen visar samlingar som ger 403 utan avtal, och dölj dem som
  `dsm-cog` i 1.1.2.
- **Rutstorlek i README och docs:** README rad ~127 och `docs/anvandning.md` rad ~141
  säger att äldre 10 km-rutor tas bort till förmån för 2,5 km-rutor. Det gäller
  laserdata. För markhöjdmodellen går det åt motsatt håll (2,5 → 10 km, enligt
  produktnyhet 8 juni 2026, fortsatt 1 m upplösning). Skilj tydligt på de två
  produkterna.
- **`mhm-*` i `docs/anvandning.md`** (rad ~95–96, ~120): beskrivs som 2,5 km-rutor.
  Lantmäteriet har inte angett avvecklingsdatum eller ersättare för `mhm-2.5`;
  formulera om efter det.
- Lantmäteriet tar vidare synpunkten att stora filer försvårar nedladdning av små
  områden (hela filen hämtas).
