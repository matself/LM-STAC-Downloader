# Användning

> **Fristående plugin.** Det här pluginet är inte utvecklat, granskat eller supportat av Lantmäteriet. Namnet Lantmäteriet används bara för att säga vilka tjänster pluginet fungerar mot. Frågor om pluginet ställer du i [det här repots ärenden](https://github.com/matself/LM-STAC-Downloader/issues), inte till Lantmäteriets support. Data hämtas från Lantmäteriets tjänster och omfattas av deras användningsvillkor.

Geodata: Ortofoto & höjd (Lantmäteriet) hämtar ortofoto och höjddata från Lantmäteriet. Den här sidan går igenom hela flödet, hur utsnitt
fungerar och vad man gör när något inte fungerar.

Pluginet hämtar bara avgiftsfria data. Lantmäteriets kataloger innehåller också avgiftsbelagda produkter, till exempel ytmodellerna (`dsm-cog` och `orto-dsm-cog`). De visas inte i sökresultaten, även om katalogen listar dem. Laserdata-kollektionen `dsm-skoglig-copc` (Laserdata Skog) har också `dsm` i namnet men är gratis (CC BY 4.0) och ingår.

## Innan du börjar

Du behöver:

* **QGIS 3.44 eller senare.**
* **Åtkomstnycklar** (Consumer Key och Consumer Secret) från Lantmäteriets
  [API-manager](https://apimanager.lantmateriet.se/).
* Att nycklarna hör till ett **systemkonto som har beställt behörigheten** på Geotorget:
  * *Ortofoto Nedladdning* för ortofoto
  * *Markhöjdmodell Nedladdning* för höjddata

Sökningen fungerar med alla giltiga nycklar, men nedladdningen kräver behörigheten. Ortofotona har dessutom särskilda
användningsvillkor som du godkänner hos Lantmäteriet.

### Hur kontona hänger ihop

* **Systemkonto**: äger behörigheterna du har beställt på Geotorget.
* **Applikation** (i API-managern): ett nyckelpar som ett program, här QGIS, använder. Den har inga behörigheter själv, utan
  kan bara använda det systemkontot har.
* **Prenumeration**: vilka API:er applikationen får anropa. Prenumerera på *STAC-bild* och *STAC-hojd*.

Nycklar för Nationella geodataplattformen (NGP-konsument) fungerar för sökning men får inte hämta filer i produktion.
Använd nycklar från ett systemkonto av typen *Geodataprodukter* som har beställt nedladdningstjänsterna.

## 1. Skapa en inloggning

1. Öppna panelen: webbmenyn (*Webb → Geodata: Ortofoto & höjd (Lantmäteriet)*) eller ikonen i verktygsfältet.
2. Under **Anslutning** finns väljaren *Autentisering*. Här kan du välja en befintlig OAuth 2-konfiguration, eller klicka på
   **Ny Lantmäteriet-inloggning…**.
3. Ange Consumer Key och Consumer Secret. Pluginet skapar en OAuth 2-konfiguration (Client Credentials) i QGIS
   autentiseringshanterare. Nyckeln sparas krypterat av QGIS, inte av pluginet.
4. Har du redan en fungerande konfiguration i QGIS (Client Credentials mot
   `https://apimanager.lantmateriet.se/oauth2/token`) kan du välja den direkt.

QGIS kan be om huvudlösenord första gången.

## 2. Sök

1. Välj **tjänst**: *Ortofoto*, *Höjddata (markhöjdmodell)* eller *Laserdata (punktmoln)*.
2. För ortofoto: välj **flygår** (från och till). Bilderna finns för många olika år, så begränsa till de år du vill ha.
3. Välj **område**, antingen:
   * **Använd kartvyn**: området blir det som syns i kartan just nu.
   * **Rita ruta**: dra en ruta i kartan.
4. Klicka **Sök**.

Sökområdet visas som en röd ruta, träffarna som blå konturer och de rutor du markerat som orange fyllning.
**Rensa sökområde och träffar** tar bort allt från kartan.

Listan och kartkonturerna visar som mest 1000 träffar. Blir det fler visas inga träffar, bara antalet. För ortofoto kan du
då kryssa i filter (**Upplösning**, **Bildtyp**, **Serie**) tills högst 1000 återstår, eller minska området eller åren. Inget
kryss i en rad visar allt, och flera kryss i en rad läggs ihop. Ger sökningen fler än 10 000 träffar hämtas ingen lista alls.

## 3. Välj rutor

Träffarna listas med rutans namn, kollektion (för ortofoto områdets namn och år), typ, år, upplösning, när datat senast ändrats (höjd) och filstorlek. Typen är bildtyp för ortofoto (`rgb` för färg, `cir` för färginfraröd) och rutstorlek för höjd. Klicka på
kolumnrubrikerna för att sortera.

Markera rutor genom att:

* kryssa i dem i listan, eller använda **Markera alla** och **Avmarkera alla**, eller
* klicka på **Välj rutor i kartan** och sedan på en ruta i kartan. Klicket markerar eller avmarkerar rutan. Där flera rutor
  överlappar, till exempel olika år, visas en meny där du väljer vilken det gäller.

Under listan står hur många rutor som är valda och deras sammanlagda storlek.

Överlappande rutor, till exempel samma plats från olika år, ligger kvar i listan. Du väljer själv vilken bild du vill ha.
Vill du ha den senaste, begränsa **flygår** innan du söker.

## 4. Hämta

Välj **målmapp** under *Hämta*. Du kan också kryssa i:

* **Hämta bara det valda området (utsnitt)**, se nedan.
* **Hämta även metadatafil med sömlinjer (.json)**, bara för ortofoto, se nedan.
* **Lägg till i projektet när klart**, som öppnar filerna som rasterlager. Sömlinjerna öppnas som ett lager per ruta.

Klicka **Hämta valda**. Framsteget visas i panelen, och **Avbryt** stoppar hämtningen. En avbruten hämtning lämnar ingen
ofullständig fil.

Pluginet frågar innan det hämtar mer än cirka 2 GB.

### Hela filer

Utan utsnitt hämtas varje vald ruta som en hel fil, sparad som `<målmapp>/<kollektion>/<fil>.tif`. Redan hämtade filer av
rätt storlek hoppas över.

Filerna är stora:

| Data | Rutans storlek | Filstorlek |
|---|---|---|
| Ortofoto | 2,5 × 2,5 km | cirka 640 MB |
| Höjd, `mhm-*` | 2,5 × 2,5 km | cirka 8 MB |
| Höjd, `dtm-cog` | 10 × 10 km | cirka 290 MB |

### Utsnitt

Rutorna är Cloud Optimized GeoTIFF, alltså filer där en läsare kan hämta just de delar den behöver. Med
**Hämta bara det valda området (utsnitt)** hämtas därför bara de delar som täcker området du sökte på.

* Rutorna som området berör **slås ihop till en fil per kollektion och bildtyp**. Färgbilder (`rgb`) och färginfraröda bilder (`cir`) av samma ruta hamnar i varsin fil.
* Täcker rutor från **olika flygår samma mark** (det förekommer bland de historiska ortofotona) blir det **en fil per flygår**, så att inget år döljer ett annat. Ligger åren bara bredvid varandra slås de ihop till en fil.
* Filen heter `<kollektion>[_<bildtyp>_<flygår>]_utsnitt_<minx>_<miny>_<maxx>_<maxy>_<kontrollsumma>.tif`, med koordinater i filens eget koordinatsystem. Flygår anges för ortofoto, som år eller intervall (`1957-1959`). Kontrollsumman bygger på vilka rutor som ingår, så att en fil gjord av andra rutor aldrig återanvänds.
* Kan någon av rutorna inte läsas skrivs **ingen** fil för den gruppen, och meddelandet namnger rutan.
* Koordinatsystemet, upplösningen och banden behålls som i originalet.
* Storleken följer området. Ett litet område ger några MB, medan en yta större än en ruta ger stora filer.
* Rutor som ligger helt utanför området hoppas över. Rutor som inte är Cloud Optimized GeoTIFF kan inte klippas.
* Utsnittet följer området du sökte på, inte kartvyn när du hämtar. Ritar du om området måste du söka och markera igen.

Ett exempel: fyra ortofotorutor (2,6 GB) som möts i ett hörn gav ett utsnitt på 436 × 436 m som en enda fil på 15 MB.

### Sömlinjer (metadatafil)

Ett ortofoto är en mosaik av flygbilder, ibland från olika dagar. Med **Hämta även metadatafil med sömlinjer (.json)**
sparas en fil per ruta som visar var gränserna mellan flygbilderna går och vilken bild som är vilken.

* Filen heter `<ruta>_flygbild.json` och sparas i samma mapp som bilden, `<målmapp>/<kollektion>/`.
* Det är en GeoJSON i SWEREF 99 TM (EPSG:3006) med en yta per flygbild. Varje yta har `bildidentitet`, till exempel
  `62_Eg_073_21`, och `tidpunkt`, flygbildens exakta tidpunkt.
* Filen hämtas efter bilderna. Den ligger öppet hos Lantmäteriet, så inloggningen behövs inte för den.
* Filen är alltid hela rutans, även när du bara hämtar ett utsnitt av bilden. Sömlinjerna klipps alltså inte till området,
  så du ser hur hela bildfilen är sammansatt. I utsnittsläge hämtas filen bara för rutor som verkligen klipps.
* Redan hämtade filer hoppas över.
* Med **Lägg till i projektet när klart** läggs sömlinjerna in som lager, med ofyllda gula ytor och svarta etiketter med
  bildidentitet och datum.
* Funktionen gäller även historiska ortofoton. Alla rutor har inte en metadatafil. Lantmäteriets dokumentation anger till
  exempel att sömlinjer saknas för vissa år. Pluginet visar hur många rutor som saknar fil i resultatmeddelandet.

### Höjdkollektioner

Höjdsökningen kan ge träffar i två sorters kollektioner. I kolumnen *Typ* syns rutstorleken:

* **`dtm-cog`, 10 km-ruta**: rutor om 10 × 10 km, cirka 290 MB. Det är Lantmäteriets nya format, med brytgeometrier i GeoPackage
  för ytor där vatten har plattats till, och en infofil med metadata. Rutor vid kusten och gränsen är avskurna till den del
  som är land och kan därför vara mindre (till exempel 10 × 5 km eller bara några MB), men de räknas ändå som 10 km-rutor och markeras *(beskuren)* i listan.
* **`mhm-*`, 2,5 km-ruta**: de äldre rutorna om 2,5 × 2,5 km, cirka 8–10 MB. Enligt Lantmäteriet slutade de uppdateras
  15 juni och avvecklas på sikt. Något slutdatum anges inte.

Båda är markhöjdmodeller med 1 m upplösning i Cloud Optimized GeoTIFF, och de täcker samma platser, så du kan få båda för
samma område. Kolumnen *Ändrad* visar när datat senast ändrats, så du ser vilken som är nyast. Välj den du vill ha. Med
utsnitt spelar filstorleken mindre roll. Se
[Lantmäteriets nyhet](https://www.lantmateriet.se/sv/geodata/vara-produkter/Produktnyheter/Geografisk-information/markhojdmodell-nedladdning-utokas-med-mer-innehall/).

### Laserdata (punktmoln)

Tjänsten *Laserdata (punktmoln)* söker i kollektionen `dsm-skoglig-copc` (Laserdata Skog) hos Lantmäteriet. Den täcker inte hela landet.
Datat är licensierat CC BY 4.0: ange Lantmäteriet som källa när du använder det. Behörigheten är samma som för höjddata
(*Markhöjdmodell Nedladdning*).

* I träfflistan visas antal **punkter** och **storlek** per ruta. Rutorna är oftast 2,5 × 2,5 km (cirka 100 till 160 MB).
* Laserdata hämtas alltid som **hela filer**, en fil per ruta, sparade som `<målmapp>/dsm-skoglig-copc/<fil>.copc.laz`. Det finns
  inget utsnitt för punktmoln. Vill du klippa ut ett område gör du det själv, till exempel med PDAL eller med QGIS bearbetning.
  Koordinatsystemet är EPSG:5845 (SWEREF 99 TM och RH2000).
* Med **Lägg till i projektet** öppnas varje fil som punktmolnslager. Filerna är COPC och läses direkt av QGIS.
* När hämtningen är klar visas resultatet i QGIS meddelandefält och **står kvar tills du stänger det**. Alla fel skrivs också i QGIS
  loggpanel, under fliken *Geodata: Ortofoto & höjd (Lantmäteriet)*.
* Lantmäteriet har meddelat att de äldre 10 km-rutorna tas bort (planerat 2 november 2026) och ersätts av 2,5 km-rutorna.

## Felsökning

**"åtkomst nekad" när du hämtar (HTTP 403).** Sökningen fungerade, men nycklarna får inte hämta filer. Kontrollera att de
hör till ett systemkonto som har beställt *Ortofoto Nedladdning* eller *Markhöjdmodell Nedladdning* (produktion) på
Geotorget, och att applikationen prenumererar på STAC-bild respektive STAC-hojd. Nycklar för NGP räcker inte.

**"Välj eller skapa en autentisering först".** Ingen inloggning är vald. Skapa eller välj en under *Anslutning*.

**Sökningen ger inga träffar.** Kontrollera området och, för ortofoto, flygåren. Alla år finns inte överallt.

**Sökningen ger träffar men listan är tom.** Fler än 1000 träffar återstår. Kryssa i filter, eller minska området eller
årsintervallet.

**Inloggningen frågar efter huvudlösenord.** QGIS skyddar autentiseringsdatabasen. Ange ditt huvudlösenord.

**Hämtningen går långsamt.** Filerna är stora. Använd utsnitt, och begränsa området så mycket det går.

**Utsnittet hoppar över rutor.** Antingen ligger rutan utanför området, eller så är filen inte Cloud Optimized GeoTIFF. Då
kan du avmarkera utsnitt och hämta den som en hel fil.

Loggmeddelanden hittar du i QGIS *Loggmeddelanden*-panel, under fliken *Geodata: Ortofoto & höjd (Lantmäteriet)*.
