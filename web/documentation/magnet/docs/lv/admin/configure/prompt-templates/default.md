### Noklusētās promptu veidnes

Magnet AI ir piegādāts ar vairākām noklusētajām promptu veidnēm, kas ir ļoti svarīgas citiem rīkiem, piemēram, RAG rīkiem un aģentiem, kā arī pēcapstrādes uzdevumu veikšanai. Dažās no tām ir mainīgie, kas norādīti iekavās ar figūriekavām.

**Svarīgi:** Pārliecinieties, ka nemaināt un neizdzēšat nevienu no šiem mainīgajiem.

- QA_SYSTEM_PROMPT_TEMPLATE
  Izmanto: RAG rīks
  Noklusētā promptu veidne atbilžu ģenerēšanai, īpaši pielāgota OpenAI modeļiem.
  `{context}` : viettura atrastajam kontekstam (satura fragmentiem).
- RAG_TOOL_DETECT_LANGUAGE
  Izmanto: RAG rīks, Meklēšanas rīks
  Noklusētā promptu veidne valodas noteikšanai daudzvalodu gadījumos.
- RAG_TOOL_TRANSLATE_TEXT
  Izmanto: RAG rīks, Meklēšanas rīks
  Noklusētā veidne tulkošanai daudzvalodu gadījumos.
  `{source_language}` : viettura avota valodai tulkošanas plūsmā
  `{target_language}` : viettura mērķa valodai tulkošanas plūsmā
- POST_PROCESS
  Izmanto: RAG rīks
  Noklusētā promptu veidne RAG rīka atbilžu pēcapstrādei. Nodrošina pareizu metriku apkopošanu lietojuma atskaitēm/paneliem.
  `{CATEGORIES}` : viettura jautājumu kategorijām (tēmām). Kategoriju vērtības konfigurē katram RAG rīkam UI.
- DEFAULT_AGENT_CLASSIFICATION
  Izmanto: Aģents
  Noklusētā promptu veidne tēmas izvēlei aģentos. Tāpat nosaka citus lietotāja nodomus, piemēram, sveicienu/atvadu vai ārpus tēmas. Šai veidnei jāizmanto LLM ar JSON režīma atbalstu.
  `{TOPIC_DEFINITIONS}` : viettura katras tēmas nosaukumam, sistēmas nosaukumam un LLM aprakstam.
- DEFAULT_AGENT_TOPIC_PROCESSING
  Izmanto: Aģents
  Noklusētā promptu veidne tēmas apstrādei un rīku izsaukšanai pēc tēmas izvēles. Šai veidnei jāizmanto LLM ar rīku izsaukšanas atbalstu.
  `{TOPIC_NAME}` : viettura izvēlētās tēmas nosaukumam.
  `{TOPIC_INSTRUCTIONS}` : viettura papildu/uzlabotām instrukcijām, ko var konfigurēt tēmas līmenī.
- PASS
  Izmanto: Aģents
  Specifiska tēmas izvēles promptu veidne gadījumiem, kad aģentā ir tikai 1 tēma. Izmantojiet to, lai izvairītos no papildu LLM izsaukuma.
  Šīs veidnes instrukcijas ir tukšas.
- DEFAULT_AGENT_TOPIC_PROCESSING
  Izmanto: Aģents
  Noklusētā promptu veidne aģenta sarunu pēcapstrādei. Nosaka metriku, piemēram, sarunas sentimentu un atrisinājuma statusu.
  `{CONVERSATION}` : visa saruna starp aģentu un lietotāju.
