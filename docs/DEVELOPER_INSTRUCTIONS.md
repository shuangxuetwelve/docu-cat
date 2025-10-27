# Developer Instructions for DocuCat

DocuCat can read and follow instructions from PR comments, allowing developers to guide the documentation updates directly from the pull request conversation.

## How It Works

When DocuCat runs on a pull request, it:

1. **Reads all PR comments** - Fetches comments from the GitHub API
2. **Parses instructions** - Uses Claude Haiku 4.5 to understand developer intent
3. **Follows instructions** - Incorporates the guidance into its analysis and updates

## Giving Instructions to DocuCat

You can give instructions to DocuCat by adding comments to your pull request. DocuCat understands natural language instructions and various mention patterns.

### Special: Skipping DocuCat

You can tell DocuCat **not to run** on a specific PR by adding a skip instruction:

```markdown
@DocuCat skip
```

```markdown
No documentation needed for this PR
```

This will prevent DocuCat from analyzing and updating documentation entirely.

### Basic Patterns

#### Explicit Mention
```markdown
@DocuCat please update the API documentation
```

#### Prefix Pattern
```markdown
DocuCat: make sure to update the README with installation instructions
```

#### Implicit Instructions
```markdown
Please update CHANGELOG.md and docs/api.md with these changes
```

## Types of Instructions

### 1. Request Specific File Updates

Tell DocuCat which files to focus on:

```markdown
@DocuCat update the following files:
- README.md with new installation steps
- docs/api.md with the new endpoints
- CHANGELOG.md with version notes
```

### 2. Skip Certain Files

Tell DocuCat to avoid certain files:

```markdown
DocuCat: skip updating test documentation
```

```markdown
Don't update the examples in docs/examples/
```

### 3. Focus on Specific Aspects

Guide DocuCat to focus on particular documentation aspects:

```markdown
@DocuCat please focus on documenting the authentication changes
```

```markdown
Make sure to explain the breaking changes in the migration guide
```

### 4. Provide Context

Give DocuCat additional context about the changes:

```markdown
DocuCat: these changes add OAuth2 support. Update the security documentation
to explain the new authentication flow and configuration options.
```

## Examples

### Example 1: Skipping DocuCat

**PR Comment:**
```markdown
@DocuCat skip - this is just a minor refactoring, no docs needed
```

**Result:** DocuCat will not run at all on this PR. No analysis, no updates.

### Example 2: Feature Addition

**PR Comment:**
```markdown
@DocuCat this PR adds a new caching layer. Please update:
1. README.md - add caching to the features list
2. docs/configuration.md - document the cache configuration options
3. docs/performance.md - explain the performance benefits
```

**Result:** DocuCat will prioritize these three files and focus on caching-related documentation.

### Example 3: Bug Fix with Note

**PR Comment:**
```markdown
This is just a bug fix in internal utilities. Please make sure the troubleshooting guide is updated.
```

**Result:** DocuCat will run and focus on updating the troubleshooting guide.

### Example 4: API Changes

**PR Comment:**
```markdown
@DocuCat we changed the REST API endpoints. Make sure to:
- Update docs/api.md with the new endpoint paths
- Add migration notes to CHANGELOG.md
```

**Result:** DocuCat will focus on the specified files.

### Example 5: Multiple Reviewers

**First comment:**
```markdown
@developer1: LGTM! The authentication looks good.
```

**Second comment:**
```markdown
@reviewer: DocuCat please update the security section in README.md
```

**Result:** DocuCat will extract the instruction from the second comment and update the security section.

## What DocuCat Understands

DocuCat's AI can understand:

- ✅ Skip instructions - when NOT to run
- ✅ File names and paths
- ✅ Documentation sections to update
- ✅ Context about the changes
- ✅ Priority and focus areas
- ✅ Specific documentation needs

## Indicators in PR Comments

When DocuCat follows developer instructions, the PR comment summary will show:

```markdown
**Configuration:**
- Enabled: ✅ Yes
- Create Commits: ✅ Yes
- Developer Instructions: ✅ Followed
```

This lets you know that DocuCat incorporated your guidance into its analysis.

## Best Practices

### Be Specific
❌ "Update the docs"
✅ "Update docs/api.md section 3.2 with the new authentication parameters"

### Provide Context
❌ "Fix the README"
✅ "Update README.md installation section - we now require Python 3.12+"

### Use File Names
❌ "Update the configuration documentation"
✅ "Update docs/configuration.md and config/README.md"

### Combine Instructions
```markdown
@DocuCat please:
1. Update API.md with the new /users/profile endpoint
2. Add migration notes to CHANGELOG.md about the breaking change
3. Skip updating the examples (will do manually)
```

## Technical Details

- **Comment Source**: GitHub Issues API (includes PR comments)
- **Parser**: Claude Haiku 4.5 via OpenRouter
- **Output Structure**:
  - `should_run_docu_cat`: `true` (run normally) or `false` (skip entirely)
  - `instructions`: String with guidance, or `null` if none
- **Integration**: Instructions are added to the analysis prompt if provided
- **Parsing**: Natural language understanding, no strict format required
- **Default Behavior**: If no comments or no skip instruction, DocuCat runs normally

## Limitations

- Instructions must be in PR comments (not in the PR description - use configuration section for that)
- DocuCat makes best effort to follow instructions but may adapt based on code analysis
- Very complex or contradictory instructions may be interpreted with AI discretion
- Instructions are advisory - DocuCat still analyzes all changes independently

## See Also

- [CONFIGURATION.md](../CONFIGURATION.md) - Configure DocuCat via PR description
- [PR_COMMENT_EXAMPLE.md](PR_COMMENT_EXAMPLE.md) - See example PR comments
