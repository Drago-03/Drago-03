# 🔥 Setting Up Waka Readme Stats

Follow these steps to fix your Waka Readme stats section:

## 1. Get Required API Keys

### WakaTime API Key
1. Sign up or log in to [WakaTime](https://wakatime.com/)
2. Go to [WakaTime Settings → Account](https://wakatime.com/settings/account)
3. Copy your API Key

### GitHub Token
You need a GitHub Personal Access Token with `repo` scope:
1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Generate a new token with `repo` scope
3. Copy your token

## 2. Add Secrets to Your GitHub Repository

1. Go to your GitHub repository
2. Click on `Settings` → `Secrets and variables` → `Actions`
3. Click on `New repository secret`
4. Add the following secrets:
   - Name: `WAKATIME_API_KEY`
   - Value: *Your WakaTime API Key*
   
   - Name: `GH_TOKEN`
   - Value: *Your GitHub Personal Access Token*

## 3. Manual Trigger (First Time)

After adding the secrets:
1. Go to your repository on GitHub
2. Navigate to `Actions` → `Waka Readme`
3. Click `Run workflow` → `Run workflow`

## Troubleshooting

If your Waka stats don't appear after running the workflow:

1. Check the workflow run logs for any errors
2. Verify that your README.md has the proper section tags:
   ```
   <!--START_SECTION:waka-->
   <!--END_SECTION:waka-->
   ```
3. Ensure your WakaTime account has data (you've been coding with the WakaTime plugin installed)
4. Make sure your GitHub token has the `repo` scope

## Extra Notes

- The stats update once a day automatically (at 12am IST)
- The first run may take a while to gather enough data
- If you're new to WakaTime, install their extension for your code editor:
  - [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=WakaTime.vscode-wakatime)
  - [Other editors](https://wakatime.com/plugins) 