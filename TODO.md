# TODO

## Ladda ner metadatafilen för kartblad (ortofoto)

Önskemål från en användare: möjlighet att välja att även ladda ner kartbladens
metadatafil, t.ex. `.json` med sömlinjer (seamlines).

- Gäller sannolikt ortofoto (antagande, ej bekräftat med användaren).
- Lägg till ett val (kryssruta) i dialogen: "Ladda ner metadatafil (.json)".
- Kolla i STAC-items/assets för ortofoto vilken asset som innehåller sömlinjerna
  och vilken typ den har.
- Spara metadatafilen bredvid bilderna, med samma namnschema.
- Överväg att bekräfta med användaren vilken fil de menar.

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
