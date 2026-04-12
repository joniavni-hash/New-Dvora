/**
 * whatsapp-handler.js
 *
 * Handles incoming WhatsApp messages and routes them to the ACP agent
 * in non-interactive background mode.
 *
 * Key design decisions:
 * - Does NOT use sessions_spawn in "thread" mode (can't bind to WhatsApp conversation)
 * - Does NOT use sessions_spawn in "run" mode (triggers interactive approval)
 * - Instead: uses --print mode (single-shot) or SDK with permissionCallback
 * - Maintains conversation context via in-memory store (upgrade to Redis for production)
 */

const express = require('express');
const { runAgentBackground, runAgentSDK } = require('./agent-runner');

const app = express();
app.use(express.json());

// In-memory conversation context store
// In production: use Redis or a database
const conversationContexts = new Map();
const MAX_CONTEXT_MESSAGES = 20;

/**
 * Builds a prompt that includes conversation history,
 * so the agent has context even though we use single-shot mode.
 */
function buildPromptWithContext(chatId, newMessage) {
  let context = conversationContexts.get(chatId) || [];

  // Add the new message
  context.push({ role: 'user', content: newMessage, timestamp: Date.now() });

  // Trim to max messages
  if (context.length > MAX_CONTEXT_MESSAGES) {
    context = context.slice(-MAX_CONTEXT_MESSAGES);
  }

  conversationContexts.set(chatId, context);

  // Build the full prompt with conversation history
  const historyLines = context.map((msg) => {
    const role = msg.role === 'user' ? 'User' : 'Dvora';
    return `${role}: ${msg.content}`;
  });

  return (
    `You are Dvora, a WhatsApp assistant. ` +
    `Respond in the same language the user writes in. ` +
    `Be helpful, concise, and friendly.\n\n` +
    `Conversation history:\n${historyLines.join('\n')}\n\n` +
    `Respond to the latest message.`
  );
}

/**
 * Stores the agent's response in conversation context.
 */
function storeAgentResponse(chatId, response) {
  const context = conversationContexts.get(chatId) || [];
  context.push({ role: 'assistant', content: response, timestamp: Date.now() });
  conversationContexts.set(chatId, context);
}

/**
 * WhatsApp webhook endpoint.
 * Receives messages and processes them via the ACP agent in background mode.
 */
app.post('/webhook', async (req, res) => {
  try {
    const { chatId, message, from } = req.body;

    if (!chatId || !message) {
      return res.status(400).json({ error: 'Missing chatId or message' });
    }

    console.log(`[webhook] Received message from ${from} in chat ${chatId}: ${message}`);

    // Respond immediately to WhatsApp (avoid timeout)
    res.status(200).json({ status: 'processing' });

    // Build prompt with conversation context
    const prompt = buildPromptWithContext(chatId, message);

    // Run agent in background mode - NO interactive approval needed
    let response;
    try {
      // Try SDK first (best option - full control over permissions)
      response = await runAgentSDK(prompt, {
        timeout: 60000,
      });
    } catch (sdkErr) {
      console.error(`[webhook] SDK failed, trying CLI: ${sdkErr.message}`);
      // Fallback to CLI with --print mode
      response = await runAgentBackground(prompt, {
        timeout: 60000,
      });
    }

    // Store response in context
    storeAgentResponse(chatId, response);

    console.log(`[webhook] Response for ${chatId}: ${response.substring(0, 100)}...`);

    // Send response back to WhatsApp via your WhatsApp API
    await sendWhatsAppMessage(chatId, response);
  } catch (err) {
    console.error(`[webhook] Error processing message: ${err.message}`);
    // Don't crash the server on individual message errors
  }
});

/**
 * WhatsApp verification endpoint (for webhook setup).
 */
app.get('/webhook', (req, res) => {
  const verifyToken = process.env.WHATSAPP_VERIFY_TOKEN || 'dvora-verify-token';
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];

  if (mode === 'subscribe' && token === verifyToken) {
    console.log('[webhook] Verification successful');
    return res.status(200).send(challenge);
  }

  return res.status(403).send('Verification failed');
});

/**
 * Send a message back to WhatsApp.
 * Replace this with your actual WhatsApp API integration
 * (Meta Cloud API, whatsapp-web.js, Baileys, etc.)
 */
async function sendWhatsAppMessage(chatId, message) {
  const apiUrl = process.env.WHATSAPP_API_URL;
  const apiToken = process.env.WHATSAPP_API_TOKEN;

  if (!apiUrl || !apiToken) {
    console.log(`[whatsapp] Would send to ${chatId}: ${message}`);
    console.log('[whatsapp] Set WHATSAPP_API_URL and WHATSAPP_API_TOKEN to enable sending');
    return;
  }

  try {
    const fetch = globalThis.fetch || require('node-fetch');
    await fetch(`${apiUrl}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messaging_product: 'whatsapp',
        to: chatId,
        type: 'text',
        text: { body: message },
      }),
    });
    console.log(`[whatsapp] Message sent to ${chatId}`);
  } catch (err) {
    console.error(`[whatsapp] Failed to send message: ${err.message}`);
  }
}

/**
 * Health check endpoint.
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    agent: 'dvora',
    mode: 'non-interactive-background',
    activeConversations: conversationContexts.size,
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`[dvora] Server running on port ${PORT}`);
  console.log(`[dvora] Mode: non-interactive background (no approval prompts)`);
  console.log(`[dvora] Permission mode: accept-edits-and-execution`);
});

module.exports = app;
