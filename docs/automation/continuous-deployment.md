### Continuous Deployment

If we tag a commit with the pattern `mvp_v*`, the [`deploy.yml`](.github/workflows/deploy.yml) workflow is triggered and deploys that exact revision to production.

| Stage | Key tools | What we use them for |
|-------|-----------|----------------------|
| **SSH handover** | **webfactory/ssh-agent** | Injects the private key stored in `SSH_PRIVATE_KEY` so the runner can hop onto the production server. |
| **Remote update** | **git pull** · **docker-compose** | On the server we pull **main**, stop the stack, pull the fresh images pushed by CI, start the stack again, and prune old layers. |

All CD runs are visible under **GitHub Actions → CD**:  
`https://github.com/Team26SWP/InnoAlias/actions/workflows/deploy.yml`
