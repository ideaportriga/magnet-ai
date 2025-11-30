# Aģenti

## Aģentiskās plūsmas principi

Aģenti tiek uzskatīti par nākamo Gen AI evolūcijas soli. Tiem parasti ir 4 pamatīpašības:

<div class="grid-container">
    <div class="grid-item">Loģiskā domāšana</div>
    <div class="grid-item">Rīku izmantošana</div>
    <div class="grid-item">Orķestrācija</div>
    <div class="grid-item">Atmiņa</div>
</div>

Galvenais aģentiskās plūsmas virzītājs ir **Rīku izsaukšana** (funkciju izsaukšana).

Aģents ir aprīkots ar rīkiem jeb **Darbībām** (Actions), kā tās sauc Magnet AI, kas var tikt ģenerētas no [RAG rīkiem](../rag-tools/overview.md), API rīkiem, [Meklēšanas rīkiem](../retrieval-tools/overview.md) un [Promptu veidnēm](../prompt-templates/overview.md).

## Kā darbojas aģentiskā plūsma ar rīku izsaukšanu:

1. Aģents saņem un analizē lietotāja ievadi, piemēram, _"Vēlos atcelt savu pasūtījumu"_ vai _"Kāda ir preces X atgriešanas politika"_.
2. Aģents nosaka lietotāja nodomu, un, ja tas atbilst konkrētai Tēmai, turpina ar Tēmas izpildi pēc instrukcijām.
3. Tēmas apstrādes laikā aģents izlemj, vai var izmantot vienu vai vairākas Darbības, lai atbildētu uz lietotāja jautājumu.
4. Ja atrod atbilstošu Darbību, pārbauda, vai ir visi nepieciešamie ievaddati, un, ja nepieciešams, pieprasa trūkstošo informāciju.
5. Aģents nodod visus ievaddatus funkcijai, un funkciju izsauc backend.
6. Aģents atgriež funkcijas izsaukuma rezultātu lietotājam, ietērpjot to lietotājam saprotamā ziņojumā.

## Gen AI aģenti vs Darbplūsmas

Jums var rasties jautājums, ar ko aģenti ar rīku izsaukšanas iespējām atšķiras no darbplūsmu aģentiem. Galvenā atšķirība ir tā, ka darbplūsmās darbību secība ir iepriekš noteikta, savukārt rīku izsaukšana dod aģentiem autonomiju dinamiski izvēlēties optimālo trajektoriju.
