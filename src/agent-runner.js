/**
 * agent-runner.js
 *
 * Runs the ACP agent in non-interactive background mode.
 * Solves the core problem: ACP sessions_spawn in "run" mode fails because
 * it requires interactive approval prompts that aren't available in background.
 *
 * Solution: Use permission-mode "accept-edits-and-execution" and pre-configure
 * allowed tools so no interactive prompt is ever triggered.
 */

const { spawn } = require('child_process');
const path = require('path');

const DEFAULT_AGENT = process.env.DVORA_DEFAULT_AGENT || 'dvora';
const PERMISSION_MODE = 'accept-edits-and-execution';

/**
 * Spawns an ACP agent session in non-interactive background mode.
 *
 * Instead of using sessions_spawn with mode "thread" (which tries to bind
 * to a conversation that doesn't exist in WhatsApp context) or mode "run"
 * (which triggers interactive approval), we:
 *
 * 1. Use --permission-mode to pre-approve all tool usage
 * 2. Pipe input/output programmatically instead of relying on interactive TTY
 * 3. Use --print mode for single-shot request/response (no session binding needed)
 *
 * @param {string} prompt - The user message to process
 * @param {object} options - Configuration options
 * @param {string} options.agent - Agent name (default: dvora)
 * @param {string} options.workdir - Working directory for the agent
 * @param {number} options.timeout - Timeout in ms (default: 120000)
 * @param {string[]} options.allowedTools - Pre-approved tools list
 * @returns {Promise<string>} Agent response text
 */
async function runAgentBackground(prompt, options = {}) {
  const {
    agent = DEFAULT_AGENT,
    workdir = process.cwd(),
    timeout = 120000,
    allowedTools = [],
  } = options;

  return new Promise((resolve, reject) => {
    const args = [
      '--print',                              // Non-interactive: single prompt in, response out
      '--permission-mode', PERMISSION_MODE,   // Auto-approve all edits and execution
      '--output-format', 'text',              // Plain text output (no JSON wrapping)
    ];

    // If a named agent is configured, use it
    if (agent && agent !== 'default') {
      args.push('--agent', agent);
    }

    // Pre-approve specific tools to avoid any residual prompts
    for (const tool of allowedTools) {
      args.push('--allowedTools', tool);
    }

    // The prompt itself
    args.push(prompt);

    const child = spawn('claude', args, {
      cwd: workdir,
      env: {
        ...process.env,
        // Force non-interactive mode at environment level
        CI: 'true',
        CLAUDE_NON_INTERACTIVE: '1',
      },
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout,
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve(stdout.trim());
      } else {
        reject(new Error(
          `Agent exited with code ${code}.\n` +
          `stderr: ${stderr}\n` +
          `stdout: ${stdout}`
        ));
      }
    });

    child.on('error', (err) => {
      reject(new Error(`Failed to spawn agent: ${err.message}`));
    });

    // Timeout safety net
    setTimeout(() => {
      if (!child.killed) {
        child.kill('SIGTERM');
        reject(new Error(`Agent timed out after ${timeout}ms`));
      }
    }, timeout);
  });
}

/**
 * Alternative: Use the Claude SDK directly for background execution.
 * This avoids the CLI entirely and gives full control over permissions.
 */
async function runAgentSDK(prompt, options = {}) {
  try {
    // Try to use the SDK if available
    const { Claude } = require('@anthropic-ai/claude-code');

    const result = await Claude.run({
      prompt,
      permissionMode: PERMISSION_MODE,
      agent: options.agent || DEFAULT_AGENT,
      cwd: options.workdir || process.cwd(),
      // Key fix: provide an auto-approve callback so no interactive prompt is needed
      permissionCallback: (toolName, input) => {
        // Auto-approve all tools in background mode
        // In production, you should whitelist specific tools
        console.log(`[background] Auto-approved tool: ${toolName}`);
        return true;
      },
    });

    return result.text;
  } catch (err) {
    if (err.code === 'MODULE_NOT_FOUND') {
      // SDK not available, fall back to CLI
      console.log('[background] SDK not available, falling back to CLI mode');
      return runAgentBackground(prompt, options);
    }
    throw err;
  }
}

module.exports = {
  runAgentBackground,
  runAgentSDK,
  DEFAULT_AGENT,
  PERMISSION_MODE,
};
