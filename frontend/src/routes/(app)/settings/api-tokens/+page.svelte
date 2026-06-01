<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import {
    Plus,
    Copy,
    Check,
    Trash2,
    KeyRound,
    ChevronDown,
    ChevronRight,
    TriangleAlert
  } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import * as Table from '$lib/components/ui/table/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const tokens = $derived(data.tokens || []);

  let formName = $state('');
  let formExpiresAt = $state('');
  let creating = $state(false);

  // Copy-once panel state — populated only from the create action result.
  let copied = $state(false);
  /** @type {string} */
  let confirmingId = $state('');
  let helpOpen = $state(false);

  const claudeConfig = `{
  "mcpServers": {
    "bottlecrm": {
      "command": "uvx",
      "args": ["bcrm-mcp"],
      "env": {
        "BCRM_BASE_URL": "<your CRM URL>",
        "BCRM_TOKEN": "bcrm_pat_… (paste the token you just created)"
      }
    }
  }
}`;

  $effect(() => {
    if (form?.created?.token) {
      // Reset the create form after a successful creation.
      formName = '';
      formExpiresAt = '';
      copied = false;
    } else if (form?.revoked) {
      toast.success('Token revoked');
      confirmingId = '';
    } else if (form?.error) {
      const message = typeof form.error === 'string' ? form.error : JSON.stringify(form.error);
      toast.error(message);
    }
  });

  /** @param {string} value */
  async function copyToClipboard(value) {
    try {
      await navigator.clipboard.writeText(value);
      copied = true;
      toast.success('Token copied to clipboard');
      setTimeout(() => (copied = false), 2000);
    } catch {
      toast.error('Could not copy — select and copy manually');
    }
  }

  /** @param {string | null | undefined} value */
  function formatDate(value) {
    if (!value) return 'Never';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return 'Never';
    return d.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  /** @param {any} token */
  function isRevoked(token) {
    return !!token.revoked_at;
  }
</script>

<svelte:head>
  <title>API Tokens - Settings - BottleCRM</title>
</svelte:head>

<PageHeader
  title="API Tokens"
  subtitle="Connect your AI agent to BottleCRM. Tokens act as you and inherit your role."
/>

<div class="flex-1 p-4 md:p-6 lg:p-8">
  <div class="mx-auto max-w-4xl space-y-6">
    {#if data.loadError}
      <div
        class="rounded-lg border border-[var(--color-danger-default)] bg-[var(--color-danger-light)] p-4 text-sm text-[var(--color-danger-default)]"
      >
        {data.loadError}
      </div>
    {/if}

    <!-- Copy-once panel: only shown immediately after a create action. -->
    {#if form?.created?.token}
      <section
        class="rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-900/30"
      >
        <div class="flex items-start gap-2">
          <TriangleAlert class="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
          <div class="min-w-0 flex-1 space-y-2">
            <h2 class="text-sm font-medium text-amber-900 dark:text-amber-200">
              Token “{form.created.name}” created
            </h2>
            <p class="text-sm text-amber-800 dark:text-amber-300">
              Copy this token now — you won't be able to see it again.
            </p>
            <div class="flex items-center gap-2">
              <code
                class="min-w-0 flex-1 overflow-x-auto rounded-md border border-amber-300 bg-white px-3 py-2 font-mono text-xs text-[var(--text-primary)] dark:border-amber-700 dark:bg-slate-900"
              >
                {form.created.token}
              </code>
              <Button
                type="button"
                size="sm"
                class="gap-1"
                onclick={() => copyToClipboard(form.created.token)}
              >
                {#if copied}
                  <Check class="h-4 w-4" />
                  Copied
                {:else}
                  <Copy class="h-4 w-4" />
                  Copy
                {/if}
              </Button>
            </div>
          </div>
        </div>
      </section>
    {/if}

    <!-- Create token -->
    <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)]">
      <header class="border-b border-[var(--border-default)] p-4">
        <h2 class="text-base font-medium text-[var(--text-primary)]">Create token</h2>
        <p class="text-sm text-[var(--text-secondary)]">
          Give the token a recognisable name. Set an optional expiry, or leave it blank for a token
          that never expires.
        </p>
      </header>
      <form
        method="POST"
        action="?/create"
        use:enhance={() => {
          creating = true;
          return async ({ update }) => {
            await update({ reset: false });
            creating = false;
            await invalidateAll();
          };
        }}
        class="flex flex-col gap-4 p-4 sm:flex-row sm:items-end"
      >
        <div class="flex-1 space-y-1.5">
          <Label for="name">Name *</Label>
          <Input id="name" name="name" required bind:value={formName} placeholder="My AI agent" />
        </div>
        <div class="space-y-1.5">
          <Label for="expires_at">Expires (optional)</Label>
          <Input id="expires_at" name="expires_at" type="date" bind:value={formExpiresAt} />
        </div>
        <Button type="submit" class="gap-2" disabled={creating}>
          <Plus class="h-4 w-4" />
          {creating ? 'Creating…' : 'Create token'}
        </Button>
      </form>
    </section>

    <!-- Existing tokens -->
    <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)]">
      <header class="border-b border-[var(--border-default)] p-4">
        <h2 class="text-base font-medium text-[var(--text-primary)]">Your tokens</h2>
        <p class="text-sm text-[var(--text-secondary)]">
          Tokens you have created. Revoke any token you no longer use.
        </p>
      </header>

      {#if tokens.length === 0}
        <div class="p-6 text-center text-sm text-[var(--text-secondary)]">
          No tokens yet. Create one above to connect your AI agent.
        </div>
      {:else}
        <Table.Root>
          <Table.Header>
            <Table.Row>
              <Table.Head>Name</Table.Head>
              <Table.Head>Prefix</Table.Head>
              <Table.Head>Last used</Table.Head>
              <Table.Head>Expires</Table.Head>
              <Table.Head>Created</Table.Head>
              <Table.Head>Status</Table.Head>
              <Table.Head class="text-right">Actions</Table.Head>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {#each tokens as token (token.id)}
              <Table.Row>
                <Table.Cell class="font-medium text-[var(--text-primary)]">
                  {token.name}
                </Table.Cell>
                <Table.Cell>
                  <code class="font-mono text-xs text-[var(--text-secondary)]">
                    {token.token_prefix}
                  </code>
                </Table.Cell>
                <Table.Cell class="text-sm text-[var(--text-secondary)]">
                  {formatDate(token.last_used_at)}
                </Table.Cell>
                <Table.Cell class="text-sm text-[var(--text-secondary)]">
                  {formatDate(token.expires_at)}
                </Table.Cell>
                <Table.Cell class="text-sm text-[var(--text-secondary)]">
                  {formatDate(token.created_at)}
                </Table.Cell>
                <Table.Cell>
                  {#if isRevoked(token)}
                    <Badge variant="secondary">Revoked</Badge>
                  {:else}
                    <Badge variant="outline">Active</Badge>
                  {/if}
                </Table.Cell>
                <Table.Cell class="text-right">
                  {#if !isRevoked(token)}
                    {#if confirmingId === token.id}
                      <form
                        method="POST"
                        action="?/revoke"
                        use:enhance={() => {
                          return async ({ update }) => {
                            await update({ reset: false });
                            await invalidateAll();
                          };
                        }}
                        class="inline-flex items-center gap-1"
                      >
                        <input type="hidden" name="id" value={token.id} />
                        <Button type="submit" variant="destructive" size="sm" class="gap-1">
                          <Check class="h-3.5 w-3.5" />
                          Confirm
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onclick={() => (confirmingId = '')}
                        >
                          Cancel
                        </Button>
                      </form>
                    {:else}
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        class="gap-1 text-[var(--color-danger-default)]"
                        onclick={() => (confirmingId = token.id)}
                      >
                        <Trash2 class="h-3.5 w-3.5" />
                        Revoke
                      </Button>
                    {/if}
                  {:else}
                    <span class="text-xs text-[var(--text-secondary)]">—</span>
                  {/if}
                </Table.Cell>
              </Table.Row>
            {/each}
          </Table.Body>
        </Table.Root>
      {/if}
    </section>

    <!-- Help: connect your AI -->
    <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)]">
      <button
        type="button"
        onclick={() => (helpOpen = !helpOpen)}
        class="flex w-full items-center gap-2 p-4 text-left"
      >
        {#if helpOpen}
          <ChevronDown class="h-4 w-4 text-[var(--text-secondary)]" />
        {:else}
          <ChevronRight class="h-4 w-4 text-[var(--text-secondary)]" />
        {/if}
        <KeyRound class="h-4 w-4 text-[var(--text-secondary)]" />
        <span class="text-base font-medium text-[var(--text-primary)]">
          Connect your AI (Claude Desktop)
        </span>
      </button>
      {#if helpOpen}
        <div class="space-y-3 border-t border-[var(--border-default)] p-4">
          <p class="text-sm text-[var(--text-secondary)]">
            Add the following to your Claude Desktop MCP config, replacing
            <code class="font-mono text-xs">BCRM_BASE_URL</code> with your CRM URL and
            <code class="font-mono text-xs">BCRM_TOKEN</code> with the token you just created.
          </p>
          <pre
            class="overflow-x-auto rounded-md border border-[var(--border-default)] bg-[var(--surface-muted)] p-3 font-mono text-xs text-[var(--text-primary)]">{claudeConfig}</pre>
        </div>
      {/if}
    </section>
  </div>
</div>
