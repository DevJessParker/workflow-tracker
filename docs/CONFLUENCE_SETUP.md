# Confluence Setup Guide

This guide walks you through setting up Workflow Tracker to publish to your Confluence Cloud personal space.

## Step 1: Get Your Confluence API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name like "Workflow Tracker"
4. Copy the token (you won't be able to see it again!)

## Step 2: Find Your Personal Space Key

### Method 1: Via Confluence UI

1. Log into your Confluence Cloud instance
2. Click "Spaces" in the top navigation
3. Click "Personal"
4. You should see your personal space
5. Click on it and look at the URL

The URL will look like:
```
https://your-domain.atlassian.net/wiki/spaces/~123456789abcdef/overview
```

The part after `/spaces/` is your space key: `~123456789abcdef`

### Method 2: Via API

You can also find it using curl:

```bash
curl -u your.email@company.com:YOUR_API_TOKEN \
  https://your-domain.atlassian.net/wiki/rest/api/space?type=personal
```

Look for the `key` field in the response.

## Step 3: Configure Workflow Tracker

Edit your `config/local.yaml`:

```yaml
confluence:
  # Your Confluence Cloud URL
  url: "https://your-domain.atlassian.net"

  # Your email address (Confluence username)
  username: "your.email@company.com"

  # The API token you created in Step 1
  api_token: "your-api-token-here"

  # Your personal space key from Step 2
  space_key: "~123456789abcdef"

  # Optional: Parent page ID if you want to organize docs under a specific page
  parent_page_id: null
```

## Step 4: Test the Connection

Run a test scan with publishing:

```bash
workflow-tracker scan --repo /path/to/your/test/repo --publish
```

You should see output like:

```
✓ Published to Confluence:
  https://your-domain.atlassian.net/wiki/spaces/~123456789abcdef/pages/123456
```

## Step 5: Move to Company Space (Later)

Once you've tested and are happy with the documentation format:

1. Create a new page in your team's Confluence space
2. Note the page ID from the URL
3. Update your config to use the team space:

```yaml
confluence:
  # ... other settings ...
  space_key: "YOURTEAMSPACE"
  parent_page_id: "123456"  # The page ID from step 1
```

## Permissions

Make sure your Confluence account has permission to:
- Create pages in the target space
- Edit pages in the target space
- Attach files to pages

## Troubleshooting

### "Space not found" error

- Double-check your space key
- Verify you have access to the space in Confluence
- For personal spaces, make sure the key starts with `~`

### "Authentication failed" error

- Verify your email address is correct
- Check that your API token is valid
- Try creating a new API token

### "Permission denied" error

- Check that you have permission to create/edit pages in the space
- Contact your Confluence administrator

### Pages are created but not in the right location

- Set the `parent_page_id` in your config
- Get the parent page ID from the URL when viewing the page in Confluence

## Best Practices

1. **Test in Personal Space First**: Always test in your personal space before moving to team spaces
2. **Use Parent Pages**: Organize workflow docs under a parent page for better structure
3. **Scheduled Updates**: Set up CI/CD to update docs automatically on deployments
4. **Version History**: Confluence keeps page history, so you can track changes over time
5. **Page Naming**: The tool creates pages named "Workflow Documentation - {repo-name}"
   - You can manually rename them in Confluence if needed

## Example CI/CD Setup

For automated updates in TeamCity or Octopus Deploy:

1. Store Confluence credentials as secret variables/parameters
2. Run the workflow tracker as part of your deployment
3. Documentation will be updated automatically
4. Team members always have up-to-date workflow docs

## Security Notes

- Never commit your API token to source control
- Use environment variables or secret management for CI/CD
- Rotate API tokens periodically
- Use a service account for CI/CD if possible
