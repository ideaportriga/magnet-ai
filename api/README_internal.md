Information about internal specifics which are irrelevant for external users.
Needs to be excluded when sharing the code with them.


### Deploy (Azure)

Container images are built in GitLab CI pipeline and pushed to [ai-bridge](https://portal.azure.com/#view/Microsoft_Azure_ContainerRegistries/RepositoryBlade/id/%2Fsubscriptions%2Fc01db071-2c12-4850-be42-2b9fe86aa362%2FresourceGroups%2FIdeaport-Magnet-AI%2Fproviders%2FMicrosoft.ContainerRegistry%2Fregistries%2Fmagnetai/repository/ai-bridge) of Azure container registry container registry [magnetai](https://portal.azure.com/#@ideaportriga.lv/resource/subscriptions/c01db071-2c12-4850-be42-2b9fe86aa362/resourceGroups/Ideaport-Magnet-AI/providers/Microsoft.ContainerRegistry/registries/magnetai/overview)

#### Environments

##### Test

Test environment is used for internal releases.

Deploy is triggered on push to the `main` branch.

It will push the new container image with the tag `latest` and re-tag current `latest` image as `previous`

##### Demo

Demo environment is used to showcase the app externally. Releases to the environment must be approved within the team.

Deploy is triggered on a new Git tag.

It will push the new container image with a tag with the same value as the Git tag.

For the new version use prefixed semantic version, like “v1.2.3” ([prefixing a semantic version](https://semver.org/#is-v123-a-semantic-version)) - container image tag will be unprefixed.


#### Apply deploy

Currently this should be done manually in Azure.
TODO - Automate with CI/CD

##### Environment Container apps

Test - [test-ai-bridge](https://portal.azure.com/#@ideaportriga.lv/resource/subscriptions/c01db071-2c12-4850-be42-2b9fe86aa362/resourceGroups/Ideaport-Magnet-AI/providers/Microsoft.App/containerApps/test-ai-bridge/containerapp)

Demo - [ai-bridge](https://portal.azure.com/#@ideaportriga.lv/resource/subscriptions/c01db071-2c12-4850-be42-2b9fe86aa362/resourceGroups/Ideaport-Magnet-AI/providers/Microsoft.App/containerApps/ai-bridge/containerapp)


##### Instructions

1. Go to Container app of needed environment

2.1. If image version needs to be changed or/and environment variables needs to be added/updated (If only secret values needs to be changed see 4.2)
  - Go to `Containers` and press `Edit and deploy` (or go to `Revisions and replicas` and press `Create new revision`)
  - In section `Container image` select needed image (normally there should be only one image)
  - Edit environment variables and press `Save`
  - Press `Create`

    New revision for the app should be deployed

2.2. In no changes in environment variables and container image version
  - Optional: If secrets needs to be updated - update them in Settings -> Secrets
  - Go to `Revisions and replicas` and select active revision
  - Press `Restart`

### Releases repository

Releases repository is created to share code externally - [ai-bridge-releases](https://cbox.ideaportriga.lv/ai-research/ai-bridge-releases)


#### Version release

Code in the `ai-bridge-releases` repository is updated automatically on creating git tag with the value of the next version (use prefixed semantic version, like “v1.2.3”)

CI pipeline job `commit_to_releases_repo` will commit the current code to the `ai-bridge-releases` repository with the following params:
- commit message: "Release version <semantic version>"
- tag: prefixed semantic version
- author name: magnetai.dev
- author email: magnetai.dev@ideaportriga.com

Some internal files are excluded from adding to the `ai-bridge-releases` repository:
- README_internal.md
- TODO.md
- .gitlab-ci.yml

This is managed in the job `commit_to_releases_repo`.

#### Access key

For a better control - create access key for a new client in the `ai-bridge-releases` [Settings -> Project access tokens](https://cbox.ideaportriga.lv/ai-research/ai-bridge-releases/-/settings/access_tokens) with scope `read_repository`.

With it it is possible to clone/pull code from the repo.

```
git clone https://<client_name>:<project_access_token>@cbox.ideaportriga.lv/ai-research/ai-bridge-releases.git
```

`client_name` could have any value - it is not linked with the token name.

