# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0-dev.2](https://github.com/ideaportriga/magnet-ai/compare/v0.4.0-dev.1...v0.4.0-dev.2) (2026-02-05)

### 🐛 Bug Fixes

* **ci:** force fetch branches for semantic-release ([d3bc7b6](https://github.com/ideaportriga/magnet-ai/commit/d3bc7b6662fa30c51164cd9a2687ff4d25a95bef))

## [0.4.0-dev.1](https://github.com/ideaportriga/magnet-ai/compare/v0.3.0...v0.4.0-dev.1) (2026-02-05)

### ✨ Features

* add bearer token support for API tools ([297f3e7](https://github.com/ideaportriga/magnet-ai/commit/297f3e7ed78e269ce6cf075c1707eeeb14029e12))
* add observability level to prompt templates ([5becf4f](https://github.com/ideaportriga/magnet-ai/commit/5becf4f8d45cfd053e7915bfb0837d4778acfa79))
* added document title for retrieval preview ([4e46609](https://github.com/ideaportriga/magnet-ai/commit/4e466094e217423f79256125f95bf58e7ac9f4c8))
* added keyterm support to elevenlabs ([daa9384](https://github.com/ideaportriga/magnet-ai/commit/daa938440e8819aec9bfbe2baff9deeb84da8ddf))
* added meeting info for note taker ([3ac5e06](https://github.com/ideaportriga/magnet-ai/commit/3ac5e06aa0c69f72f5e61bc37ee207ea0c98472c))
* added process file support for note taker ([2481050](https://github.com/ideaportriga/magnet-ai/commit/2481050a66d6acfe4a23006abc4aa075d46bcd9c))
* adding the teams user table ([#51](https://github.com/ideaportriga/magnet-ai/issues/51)) ([3f199c4](https://github.com/ideaportriga/magnet-ai/commit/3f199c4b3a7205232e657ccda63cbd6d2481f9d5))
* basic support for note-taker ms teams app ([aa03316](https://github.com/ideaportriga/magnet-ai/commit/aa03316c7325ea3c68d89245b3f4028a84b69a2b))
* **deep-research:** improve tracing ([77d9529](https://github.com/ideaportriga/magnet-ai/commit/77d952945019bff6fa457f745c4c3333d88a0954))
* format note-taker recordings summary, incl also size/duration ([a7a2c75](https://github.com/ideaportriga/magnet-ai/commit/a7a2c751e1a0904844cd001e520f01ae16a47f4b))
* implemented api ([4178313](https://github.com/ideaportriga/magnet-ai/commit/417831377a8634c73382fdded13c6bde4953f6b8))
* implemented external url for documents ([7701c95](https://github.com/ideaportriga/magnet-ai/commit/7701c953e50f3c89444703aa941ae9081b86fe46))
* implemented fluidtopics source, implemented sync scheduling ([4c10755](https://github.com/ideaportriga/magnet-ai/commit/4c1075577eb6b2397d90fd9b8008baf7d77a87f3))
* improved metadata studio ui and added fluid topics metadata search  ([#61](https://github.com/ideaportriga/magnet-ai/issues/61)) ([b410f85](https://github.com/ideaportriga/magnet-ai/commit/b410f853f1b38d6a6172eac231cd7f73b9eeb589))
* introduce experimental deep research ([97aa935](https://github.com/ideaportriga/magnet-ai/commit/97aa935fa2e01e9763acb486e9733cc36c5a7ca7))
* **knowledge-graph:** add route for document search ([926d274](https://github.com/ideaportriga/magnet-ai/commit/926d2748cae4f99832991c3b6885de7bce232b60))
* **knowledge-graphs:** add Sharepoint page support ([c0bb41c](https://github.com/ideaportriga/magnet-ai/commit/c0bb41ce0693a036a45d24864a637e544b1c62c7))
* **knowledge-graphs:** allow using client id for conversations ([2fd52d7](https://github.com/ideaportriga/magnet-ai/commit/2fd52d73d8dcb95271bf30cd81f81bf9188cfe42))
* **knowledge-graphs:** make sync asyncronous ([65bf01d](https://github.com/ideaportriga/magnet-ai/commit/65bf01dff1c6fe7f404d371d17d7c75c96c617a9))
* metadata wip ([98033ca](https://github.com/ideaportriga/magnet-ai/commit/98033cab737b414cc63818b9037e832ac1f183ac))
* metadata wip ([07c1816](https://github.com/ideaportriga/magnet-ai/commit/07c1816d0e36aa81447fa98a4adda22428cdc977))
* migration file ([f2a4ed0](https://github.com/ideaportriga/magnet-ai/commit/f2a4ed01ddb9d99d8ba2d877e433738ce084e664))
* model and provider test functionality ([ab51a73](https://github.com/ideaportriga/magnet-ai/commit/ab51a737ee23c712bff07a5d375ebc176c9c2638))
* note taker accepts only messages from the meeting organizer ([405b37a](https://github.com/ideaportriga/magnet-ai/commit/405b37a5c0e0eca7a6e1d8b16fc6cc23c8feb81a))
* **scheduler:** add cleanup logs job for traces and metrics ([e0b0f75](https://github.com/ideaportriga/magnet-ai/commit/e0b0f75e7dde6bd3525786898a29042ff5f02894))
* **stt:** changed elevenlabs model to scribe_v2 ([c91c6ce](https://github.com/ideaportriga/magnet-ai/commit/c91c6cec9009aabd0933a9c02aba86ff73d54819))
* ui implementation for metadata management ([7d86904](https://github.com/ideaportriga/magnet-ai/commit/7d8690484492ac4f32ab49ac389ac531dda8d3d0))
* update UI for the metadata ([403c016](https://github.com/ideaportriga/magnet-ai/commit/403c016ba961d7968074e01f2a65c533278a024b))
* upgrade microsoft/agents-for-python to 0.6.1 ([1c2c30e](https://github.com/ideaportriga/magnet-ai/commit/1c2c30e2d1acbf07e7618db78bf12a88a4b82470))

### 🐛 Bug Fixes

* add rerank to openapi and add model refresh to ai_model updates/creates ([2b5c7ea](https://github.com/ideaportriga/magnet-ai/commit/2b5c7ea037b1158ca6018e784da9e6e80ad11426))
* add ruff format to pre-commit hook ([31da5d9](https://github.com/ideaportriga/magnet-ai/commit/31da5d9b30b3473c803cce875c4d39953cd1b9bb))
* added custom headers to handle  special APIs, fixed metadata sanitazing for oracle store ([41fae38](https://github.com/ideaportriga/magnet-ai/commit/41fae38c7c1debe23d2bb677d2b2ede9431ad89c))
* added missing entry_type for fluid topics ([4780c03](https://github.com/ideaportriga/magnet-ai/commit/4780c0327d96f9f17f850ea633e1dd2bde874348))
* **api:** configure custom httpx timeouts ([6f6d01e](https://github.com/ideaportriga/magnet-ai/commit/6f6d01ed148aa6528a6870f3e5889e093a9e5562))
* **api:** directly set timeout for elevenlabs sdk ([aafd5d3](https://github.com/ideaportriga/magnet-ai/commit/aafd5d3e26f82ce9edf70fdd44213775e8ecef7b))
* **api:** Increased read timeout for elevenlabs ([6155d96](https://github.com/ideaportriga/magnet-ai/commit/6155d964fcb61f7fd10ac12aa2589acd5117f33c))
* **api:** use httpx_client when configuring ElevenLabs timeouts ([ef8a1be](https://github.com/ideaportriga/magnet-ai/commit/ef8a1bebee2d41d3991f5a6fe06f86f0972b3a8c))
* changed duplicate name ([852710c](https://github.com/ideaportriga/magnet-ai/commit/852710c4ca34d2691ea1d5bf118b45f22b9a20cf))
* **ci:** sync release workflow with main ([11527af](https://github.com/ideaportriga/magnet-ai/commit/11527afa84af4c7ec5efeb9bcdfadf99d6af5f9a))
* **deep-research:** fix and standardize UI ([0304514](https://github.com/ideaportriga/magnet-ai/commit/03045148784a841c29ff3564a87312322e22784a))
* **deep-research:** fix UI issues ([1402ba9](https://github.com/ideaportriga/magnet-ai/commit/1402ba939fb567805b6ed9939f4342110fca3d1c))
* error handling for rerank ([675829a](https://github.com/ideaportriga/magnet-ai/commit/675829a70844b768867ee5ca00d089af1973ea30))
* evaluation process result saving problem ([4a786f8](https://github.com/ideaportriga/magnet-ai/commit/4a786f8ccf18a428dc0e9d51c9ea47954f1e5861))
* fix missing auth routes ([583ed96](https://github.com/ideaportriga/magnet-ai/commit/583ed9622e9255f7b051f900c3a4b025c1afa054))
* fixed content profile new button and source selection ([c3a3b5c](https://github.com/ideaportriga/magnet-ai/commit/c3a3b5c933bcfa2b2b84825da4e5f66191263d9e))
* fixed formatting errors ([295275d](https://github.com/ideaportriga/magnet-ai/commit/295275dfe3533b3eac97355c7ffa93b39c47af03))
* fixed knowledge graph tracing ([03559f0](https://github.com/ideaportriga/magnet-ai/commit/03559f02caac0faa4030501ed1089fff2c5a5e81))
* fixed migration conflicts ([327cfbb](https://github.com/ideaportriga/magnet-ai/commit/327cfbb8dfdc92a7333a10c09fc5ae998f633428))
* fixed migrations and formatting after merge ([dbd8ce8](https://github.com/ideaportriga/magnet-ai/commit/dbd8ce844d8773ae2bccc694b57b7b1b056b47df))
* fixed sharepoint multiselect choice field ingestion and search ([#67](https://github.com/ideaportriga/magnet-ai/issues/67)) ([bd66fed](https://github.com/ideaportriga/magnet-ai/commit/bd66fed9f1631aa7391dce89fcfec5b022ba9d05))
* fixing migration conflicts ([346669b](https://github.com/ideaportriga/magnet-ai/commit/346669bd9789f72ee1547745915f422da84085f4))
* fixture loader for all entities ([5ffaf1f](https://github.com/ideaportriga/magnet-ai/commit/5ffaf1f80a43ec0a9ae371f2eb5208b79d2ebe75))
* format errors ([fe72dd5](https://github.com/ideaportriga/magnet-ai/commit/fe72dd52ab1051ab6fdbd5c87faaa2e4bbe6ce48))
* handle heavy recordings ([55fa674](https://github.com/ideaportriga/magnet-ai/commit/55fa674332560f19c0cb3f98f0da0afe9b4d3d08))
* indentation ([eb62be9](https://github.com/ideaportriga/magnet-ai/commit/eb62be9571ac1f8caafa9ef0af3495b595bcceb4))
* **kg:** chunk similarity search was incorrectly joining documents ([a4d60f9](https://github.com/ideaportriga/magnet-ai/commit/a4d60f945705cf59e2a8281ed6c48b01a909681c))
* **knowledge-graphs:** restore getting files from Sharepoint ([c01b56f](https://github.com/ideaportriga/magnet-ai/commit/c01b56f49acb7b66029a069e92207df360c3401b))
* **knowledge-graphs:** return option to sync custom Sharepoint library ([21514a6](https://github.com/ideaportriga/magnet-ai/commit/21514a63563a877f3a8fd397c55f5ad52053ce4b))
* merge remote-tracking branch 'origin/main' into develop ([50551a0](https://github.com/ideaportriga/magnet-ai/commit/50551a007245781a78f7c9fa225dbcff9d38cec9))
* **model-providers:** change default api_version for Azure OpenAI ([badb11f](https://github.com/ideaportriga/magnet-ai/commit/badb11f8199156aa0d2b0ee7fd16da7b840d2b89))
* ram bloat ([1d097e5](https://github.com/ideaportriga/magnet-ai/commit/1d097e577a30cc030df2cacbfa8a31598f24ffcc))
* regenerated poetry lock ([e99c90a](https://github.com/ideaportriga/magnet-ai/commit/e99c90aeb216cdedfd66c91cdc0b6bd6f0f790fb))
* remove filename field from the knowledge graph sync logs ([c4dba5f](https://github.com/ideaportriga/magnet-ai/commit/c4dba5fdab6820bcb48f7e222084b4512e5209e9))
* remove unnecessary validation and editing for schema field name ([80504eb](https://github.com/ideaportriga/magnet-ai/commit/80504eb0bd9f2f7a2616dd825d414377f2b815a6))
* scheduled jobs UI and backend improvements ([f864ad0](https://github.com/ideaportriga/magnet-ai/commit/f864ad09cc1554778715e51fa1833025a76a2140))
* system_name validation ([b2fa88f](https://github.com/ideaportriga/magnet-ai/commit/b2fa88fa947795286fd09080bf51f293ab053a9b))
* transcription not returning full meta ([58f489c](https://github.com/ideaportriga/magnet-ai/commit/58f489c025c032c07b2bf84fcba4c279fedbc3c1))
* updated pyproject and requirements ([389d24a](https://github.com/ideaportriga/magnet-ai/commit/389d24a51e5811ede45c07073f0c12dff8c30068))

### 📚 Documentation

* created devops guide, created deployment documentation ([d63aa35](https://github.com/ideaportriga/magnet-ai/commit/d63aa355657905401519d277eb48f314953f7b32))

### ♻️ Code Refactoring

* changed chunks and documents table handling, added new fields ([c9b60a8](https://github.com/ideaportriga/magnet-ai/commit/c9b60a8890a8ae471b6c2531fea66436578f88e1))
* get rid of using Graph API for getting online meeting id ([689e156](https://github.com/ideaportriga/magnet-ai/commit/689e156b0f2e52354fd31e1ccaf306b430247358))
* improving note taker oauth flow ([34a5880](https://github.com/ideaportriga/magnet-ai/commit/34a5880686faa883bc508a8441450d50b41e9dc0))
* note-taker cleaned up oauth flow ([a9c9bf5](https://github.com/ideaportriga/magnet-ai/commit/a9c9bf58865e3c6ac83e81bf95348d3bc5c2725d))
* note-taker oauth flow ([311eafd](https://github.com/ideaportriga/magnet-ai/commit/311eafd00cbd3a6963b136576d9e1464737442dc))

## [0.3.0](https://github.com/ideaportriga/magnet-ai/compare/v0.2.1...v0.3.0) (2025-12-10)

### ✨ Features

* implemented retrieval agent for knowledge graphs ([b39c07c](https://github.com/ideaportriga/magnet-ai/commit/b39c07c28333d6d775600f4253150235863c562b))
* implemented retrieval agent for knowledge graphs ([c618d28](https://github.com/ideaportriga/magnet-ai/commit/c618d2816adf24de3e70b67e8b60b49ee4dce435))

## [0.2.1](https://github.com/ideaportriga/magnet-ai/compare/v0.2.0...v0.2.1) (2025-12-10)

### 🐛 Bug Fixes

* updated the documentation and some CI-related scripts. ([574d258](https://github.com/ideaportriga/magnet-ai/commit/574d258a9d7c13adb3c063e82364822602228bb5))

## [0.2.0](https://github.com/ideaportriga/magnet-ai/compare/v0.1.1...v0.2.0) (2025-12-08)

### ✨ Features

* update introduces asynchronous message processing capabilities and lays the groundwork for Microsoft Teams meeting integration. ([#40](https://github.com/ideaportriga/magnet-ai/issues/40)) ([0292eb5](https://github.com/ideaportriga/magnet-ai/commit/0292eb500f269f6cc41486af00bbe714d41df410))

### 🐛 Bug Fixes

* resolve security vulnerabilities and unblock ci ([#41](https://github.com/ideaportriga/magnet-ai/issues/41)) ([bb0f20d](https://github.com/ideaportriga/magnet-ai/commit/bb0f20de829caafa35eb589aaab5a8369132c7e8))

### 📚 Documentation

* add links to online documentation in README ([62bb143](https://github.com/ideaportriga/magnet-ai/commit/62bb143ae9eb50cc44a76d57c02af20813d5cc20))

## [0.1.1](https://github.com/ideaportriga/magnet-ai/compare/v0.1.0...v0.1.1) (2025-12-02)

### 🐛 Bug Fixes

* docs correct malformed YAML footer in Latvian index; fix iconPicker code; update ci.yml ([0ac22c8](https://github.com/ideaportriga/magnet-ai/commit/0ac22c87a6968a7c5a994736ab2ca6d4d844ce66))
