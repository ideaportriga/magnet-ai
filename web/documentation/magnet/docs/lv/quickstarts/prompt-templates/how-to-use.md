# Promptu veidņu izmantošana

## Promptu veidņu izmantošana citos Magnet AI rīkos

Magnet AI ir piegādāts ar [noklusētajām promptu veidnēm](../../../lv/admin/configure/prompt-templates/default.md), kas nodrošina būtisku uzdevumu izpildi, piemēram, atbilžu ģenerēšanu RAG rīkos, RAG un aģentu izvades pēcapstrādi, kā arī tulkošanu daudzvalodu plūsmās. Noklusētās veidnes ir iepriekš atlasītas dažādās lietotnes daļās, tāpēc uzsākot darbu ar Magnet AI, nav nepieciešams iedziļināties promptu inženierijā – viss darbojas uzreiz ar iepriekš konfigurētām veidnēm.

Attīstoties jūsu AI risinājumiem, iespējams, vēlēsieties klonēt un pielāgot noklusētās veidnes vai izveidot savas no nulles. Tad vienkārši nomainiet noklusētās veidnes citos rīkos un pārbaudiet rezultātu.

[Lasīt vairāk](../../../lv/admin/configure/prompt-templates/configuration.md) par promptu veidņu konfigurēšanu.

## Promptu veidņu izmantošana atsevišķi

Promptu veidnes var piekļūt no citas sistēmas caur API, lai veiktu tādus uzdevumus kā:

- Lietas vai e-pasta kopsavilkuma izveide;
- E-pasta melnraksta izveide;
- Ieraksta tulkošana;
- Lietas kategorizēšana;
- Sentimenta analīze u.c.

Lai izmantotu promptu veidni no ārējas sistēmas, nepieciešams nodot vajadzīgo kontekstu (piemēram, lietas aprakstu vai e-pasta tekstu) LLM un ieviest izsaukšanas mehānismu jūsu sistēmā.