
### Releases repository

Releases repository is created to share code externally - [knowledge-magnet-ui-releases](https://cbox.ideaportriga.lv/ai-research/knowledge-magnet-ui-releases)


#### Version release

Code in the `knowledge-magnet-ui-releases` repository is updated automatically on creating git tag with the value of the next version (use prefixed semantic version, like “v1.2.3”)

CI pipeline job `commit_to_releases_repo` will commit the current code to the `knowledge-magnet-ui-releases` repository with the following params:
- commit message: "Release version <semantic version>"
- tag: prefixed semantic version
- author name: magnetai.dev
- author email: magnetai.dev@ideaportriga.com

Some internal files are excluded from adding to the `knowledge-magnet-ui-releases` repository:
- README_internal.md
- TODO.md
- .gitlab-ci.yml

This is managed in the job `commit_to_releases_repo`.

#### Access key

For a better control - create access key for a new client in the `knowledge-magnet-ui-releases` [Settings -> Project access tokens](https://cbox.ideaportriga.lv/ai-research/knowledge-magnet-ui-releases/-/settings/access_tokens) with scope `read_repository`.

With it it is possible to clone/pull code from the repo.

```
git clone https://<client_name>:<project_access_token>@cbox.ideaportriga.lv/ai-research/knowledge-magnet-ui-releases.git
```

`client_name` could have any value - it is not linked with the token name.
