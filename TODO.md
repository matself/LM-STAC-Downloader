# TODO

## Ladda ner metadatafilen för kartblad (ortofoto)

Önskemål från en användare: möjlighet att välja att även ladda ner kartbladens
metadatafil, t.ex. `.json` med sömlinjer (seamlines).

- Bekräftat av användaren: önskemålet gäller sömlinjer för **historiska ortofoton**.
- Bekräftat att pluginet redan hittar dem: sökning med flygår 1950–2026 ger träffar i
  kollektioner som `orto-historiska-1960-1969`, `orto-historiska-1970-1979` och
  `orto-historiska-2000-2004` (bildtyp `pan`, 0,5–1 m, 14–88 MB per ruta), bredvid
  vanliga `orto-a-2006`.
- **Sömlinjer finns inte för historiska ortofoton.** Enligt produktdokumentationen
  för Ortofoto Nedladdning (Informationsinnehåll, version 2025.02) finns för
  1949–2005 "endast begränsade metadata och inga bildsömlinjer". Sömlinjer
  (polygoner) finns bara från 2006 och framåt, och inte för 2006–2009. Önskemålet
  går alltså inte att uppfylla för historiska ortofoton. Kvar att verifiera: finns
  det en separat metadata-asset i STAC-items för 2006+ (felsökningsloggen på
  grenen `seamlines` visar assets-nycklar). Svara användaren och fråga vilka år
  de egentligen behöver.
- Lägg till ett val (kryssruta) i dialogen: "Ladda ner metadatafil (.json)".
- Kolla i STAC-items/assets för historiska ortofoton vilken asset som innehåller
  sömlinjerna och vilken typ den har.
- Spara metadatafilen bredvid bilderna, med samma namnschema.

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
