// server.js
//
// Pattern: accept fast (202), work in background, report status.
//
// This file is a self-contained demo using an in-memory store + setInterval
// worker loop, so you can run it with zero infra. Every spot where a real
// deployment needs a durable queue (Redis/BullMQ, SQS, Postgres row-locking,
// etc.) is marked with "// PROD:" — swap that piece, keep the shape.

const express = require("express");
const crypto = require("crypto");

const app = express();
app.use(express.json());

// ---------------------------------------------------------------------------
// 1. THE JOB STORE
// ---------------------------------------------------------------------------
// PROD: this is a table (jobs) in Postgres, or a Redis hash. In-memory here
// only because it's a demo — restart the process and all jobs vanish.
//
// Job shape:
// {
//   id, status: 'queued'|'running'|'succeeded'|'failed',
//   idempotencyKey, input, result, error,
//   attempts, maxAttempts, createdAt, updatedAt
// }
const jobs = new Map();

// Idempotency index: maps a client-supplied key -> jobId.
// This is what makes "the request arrives twice" safe.
const idempotencyIndex = new Map();

// The actual queue. PROD: replace this array with BullMQ .add() / SQS
// SendMessage. The interface you want is just: push(job) / pop() -> job.
const queue = [];

function createJob(idempotencyKey, input) {
  const id = crypto.randomUUID();
  const job = {
    id,
    status: "queued",
    idempotencyKey,
    input,
    result: null,
    error: null,
    attempts: 0,
    maxAttempts: 3,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
  jobs.set(id, job);
  queue.push(id);
  return job;
}

// ---------------------------------------------------------------------------
// 2. THE ENQUEUE ENDPOINT — answers in milliseconds
// ---------------------------------------------------------------------------
//
// Idempotency: the client sends an Idempotency-Key header (or you derive one
// from the input, e.g. hash of the prompt + userId). If we've seen it before,
// we return the *existing* job instead of creating a new one. This is the
// non-negotiable that stops "double-click" or "client retried after a
// timeout" from running your A6 AI call twice and charging you twice / giving
// the user two different answers.
app.post("/jobs", (req, res) => {
  const idempotencyKey =
    req.header("Idempotency-Key") ||
    // fallback: derive a key from the input itself so identical requests
    // dedupe even without a header
    crypto
      .createHash("sha256")
      .update(JSON.stringify(req.body))
      .digest("hex");

  const existingJobId = idempotencyIndex.get(idempotencyKey);
  if (existingJobId && jobs.has(existingJobId)) {
    // Same request came in again (retry, double-click, whatever).
    // Do NOT enqueue a second job. Return the same job id.
    return res.status(202).json({ jobId: existingJobId, deduped: true });
  }

  const job = createJob(idempotencyKey, req.body);
  idempotencyIndex.set(idempotencyKey, job.id);

  // 202 Accepted: "I took your request, work hasn't happened yet."
  // Note: no result here. Just enough for the client to poll with.
  res.status(202).json({ jobId: job.id, statusUrl: `/jobs/${job.id}` });
});

// ---------------------------------------------------------------------------
// 3. THE STATUS ENDPOINT — client polls this
// ---------------------------------------------------------------------------
app.get("/jobs/:id", (req, res) => {
  const job = jobs.get(req.params.id);
  if (!job) return res.status(404).json({ error: "job not found" });

  res.json({
    jobId: job.id,
    status: job.status, // queued | running | succeeded | failed
    result: job.status === "succeeded" ? job.result : undefined,
    error: job.status === "failed" ? job.error : undefined,
    attempts: job.attempts,
  });
});

// ---------------------------------------------------------------------------
// 4. THE WORKER
// ---------------------------------------------------------------------------
// PROD: this is a separate process (worker.js), not a setInterval in your
// web server. The web server should only ever enqueue and read status; if
// the worker lives in the same process, a slow job can still starve your
// HTTP event loop or die when you redeploy the web dyno.

async function runYourA6AICall(input) {
  // <-- your actual slow operation goes here -->
  // Simulated: 2s "thinking" + a chance of failure, to exercise retries.
  await new Promise((r) => setTimeout(r, 2000));
  if (Math.random() < 0.3) {
    throw new Error("AI provider timeout (simulated)");
  }
  return { answer: `AI result for: ${JSON.stringify(input)}` };
}

// PROD: alerting. A real alert is a Slack webhook / PagerDuty / Sentry call.
// The point isn't the transport, it's that failures are NOT allowed to just
// sit silently as a row with status='failed' that nobody looks at.
function alertOnFinalFailure(job) {
  console.error(
    `[ALERT] job ${job.id} failed permanently after ${job.attempts} attempts:`,
    job.error
  );
  // e.g. await fetch(SLACK_WEBHOOK_URL, { method: 'POST', body: ... })
}

async function processNextJob() {
  const jobId = queue.shift();
  if (!jobId) return; // nothing to do

  const job = jobs.get(jobId);
  if (!job) return;

  job.status = "running";
  job.attempts += 1;
  job.updatedAt = Date.now();

  try {
    // Idempotency at the *work* level too: if your AI call has side effects
    // (writes to a DB, sends an email), the operation itself should be safe
    // to run twice — e.g. "upsert result for jobId" rather than "insert".
    // A job can retry AND the underlying action can still be idempotent.
    const result = await runYourA6AICall(job.input);
    job.status = "succeeded";
    job.result = result;
  } catch (err) {
    if (job.attempts < job.maxAttempts) {
      // Retry: put it back on the queue. PROD: use exponential backoff
      // (BullMQ/SQS support this natively — e.g. delay = 2^attempts * 1000ms)
      // instead of immediately re-queuing.
      job.status = "queued";
      queue.push(job.id);
      console.warn(
        `job ${job.id} failed (attempt ${job.attempts}/${job.maxAttempts}), retrying:`,
        err.message
      );
    } else {
      // Out of retries. This is terminal — someone must find out.
      job.status = "failed";
      job.error = err.message;
      alertOnFinalFailure(job);
    }
  } finally {
    job.updatedAt = Date.now();
  }
}

// PROD: this loop is your worker process's main loop (or BullMQ's internal
// consumer). Polling every 200ms here purely for demo responsiveness.
setInterval(processNextJob, 200);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`listening on :${PORT}`));
