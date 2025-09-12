# Promptu veidnes konfigurācija

Apskatīsim tuvāk Magnet AI lietotājiem pieejamos promptu veidņu parametrus.

## Promptu veidne

![image.png](image.png)

## Modeļa iestatījumi

Izvēlieties optimālo modeli, kas nodrošina pietiekamu atbilžu kvalitāti un nepieciešamo formātu. Pielāgojiet Temperature un Top P parametrus.

Temperature nosaka, cik nejauša/radoša būs modeļa atbilde, kur 0 ir visparedzamākais, bet 1 – visradošākais. Top P nosaka, cik daudz iespējamo vārdu LLM apsver nākamā vārda izvēlē, kur 0 ir šaurākā izvēle, bet 1 – visdaudzveidīgākā.

Atbildes limits ir papildu iestatījums, kas var būt noderīgs, ja nepieciešams, lai LLM atbild ar ierobežotu tokenu skaitu.

![![image.png](image%201.png)]()

## Atbildes formāts

Modeļiem, kas atbalsta JSON formātu, var ieslēgt slēdzi, lai piespiestu modeli **atbildēt ar JSON**. Lūdzu, ņemiet vērā, ka jums joprojām jānorāda modelim atbildēt JSON formātā arī promptu veidnē.

**Atbilstības shēma** ir vēl uzlabotāks iestatījums. Ieslēdziet to, lai norādītu savu JSON shēmu, kurai atbildei jāatbilst.

![image.png](image%202.png)

## Piezīmes

Izmantojiet šo cilni, lai glabātu testa ievades un priekšskatītu, kā darbojas jūsu promptu veidne. Alternatīvi šo lauku var izmantot arī piezīmēm par promptu veidni un tās konfigurāciju.

![image.png](image%203.png)

## Testu kopas

Šī cilne ļauj piesaistīt Testu kopu promptu veidnei, lai ātri piekļūtu testu ierakstiem. Izvēlieties atbilstošāko Testu kopu no nolaižamās izvēlnes, un ieraksti parādīsies sarakstā. Klikšķinot uz testa ieraksta, tas tiks nokopēts priekšskatījuma laukā.

![image.png](image%204.png "image.png")
