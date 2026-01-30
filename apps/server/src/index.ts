import "dotenv/config";
import express from "express";
import multer from "multer";
import cors from "cors";
import fetch from "node-fetch";
import { initSendGrid, sendRegisterEmail } from "./mail";
import fs from "fs";
import path from "path";
import crypto from "crypto";

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer();
const AI_URL = process.env.AI_URL || "http://127.0.0.1:8001/analyze";

app.get("/api/activity", async (req, res) => {
  const u = req.query.url as string;
  if (!u) {
    res.status(400).json({ error: "missing url" });
    return;
  }
  try {
    const r = await fetch(u);
    const text = await r.text();
    const titleMatch = text.match(/<title>(.*?)<\/title>/i);
    const title = titleMatch ? titleMatch[1] : "";
    const summary = text.slice(0, 200);
    res.json({ title, summary });
  } catch (e) {
    res.status(500).json({ error: "fetch failed" });
  }
});

app.post("/api/register", async (req, res) => {
  const { email } = req.body || {};
  if (!email) {
    res.status(400).json({ error: "missing email" });
    return;
  }
  try {
    const key = process.env.SENDGRID_API_KEY || "";
    const from = process.env.SENDGRID_FROM || "";
    const baseUrl = process.env.APP_BASE_URL || "";
    if (!key || !from) {
      res.status(500).json({ error: "sendgrid not configured" });
      return;
    }
    initSendGrid(key);
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    await sendRegisterEmail(email, from, code, baseUrl);
    res.json({ message: "registration email sent" });
  } catch (e) {
    res.status(500).json({ error: "send email failed" });
  }
});

app.post("/api/analyze", upload.single("file"), async (req, res) => {
  if (!req.file) {
    res.status(400).json({ error: "missing file" });
    return;
  }
  try {
    const userId = (req.body && (req.body.user_id as string)) || "anon";
    const providedSession = req.body && (req.body.session_id as string);
    const activityName = (req.body && (req.body.activity_name as string)) || "";
    const windowMs = 10 * 60 * 1000;
    const bucket = Math.floor(Date.now() / windowMs) * windowMs;
    const sessionId = providedSession || `${userId}-${bucket}`;
    const hash = crypto.createHash("sha256").update(req.file.buffer).digest("hex");
    const day = new Date().toISOString().slice(0, 10);
    const uploadsRoot = path.resolve(process.cwd(), "uploads", day, sessionId);
    await fs.promises.mkdir(uploadsRoot, { recursive: true });
    const ext = req.file.mimetype === "audio/webm" ? "webm" : req.file.mimetype === "audio/ogg" ? "ogg" : "bin";
    const filename = `${Date.now()}_${hash.slice(0, 8)}.${ext}`;
    const fullPath = path.join(uploadsRoot, filename);
    await fs.promises.writeFile(fullPath, req.file.buffer);
    const ai = await fetch(AI_URL, {
      method: "POST",
      body: req.file.buffer,
      headers: { "Content-Type": "application/octet-stream" }
    });
    const data = await ai.json();
    const score =
      data.sentiment === "positive" ? 80 : data.sentiment === "neutral" ? 60 : 40;
    res.json({
      score,
      sentiment: data.sentiment,
      keywords: data.keywords || [],
      audio_hash: hash,
      stored_path: path.relative(process.cwd(), fullPath),
      session_id: sessionId,
      user_id: userId,
      activity_name: activityName
    });
  } catch (e) {
    res.status(500).json({ error: "ai service failed" });
  }
});

app.get("/api/analyze_session", async (req, res) => {
  const sessionId = req.query.session_id as string;
  if (!sessionId) {
    res.status(400).json({ error: "missing session_id" });
    return;
  }
  try {
    const today = new Date();
    const dayFmt = (d: Date) => d.toISOString().slice(0, 10);
    const days = [dayFmt(today), dayFmt(new Date(today.getTime() - 24 * 60 * 60 * 1000))];
    let dir: string | null = null;
    for (const day of days) {
      const candidate = path.resolve(process.cwd(), "uploads", day, sessionId);
      try {
        await fs.promises.access(candidate);
        dir = candidate;
        break;
      } catch {}
    }
    if (!dir) {
      res.status(404).json({ error: "session not found" });
      return;
    }
    const files = (await fs.promises.readdir(dir)).filter(f => f.includes("_"));
    files.sort(); // timestamp prefix ensures order
    let totalScore = 0;
    const sentiments: Record<string, number> = {};
    const keywordsSet = new Set<string>();
    const items: any[] = [];
    for (const f of files) {
      const p = path.join(dir, f);
      const buf = await fs.promises.readFile(p);
      const ai = await fetch(AI_URL, {
        method: "POST",
        body: buf,
        headers: { "Content-Type": "application/octet-stream" }
      });
      const data = await ai.json();
      const score = data.sentiment === "positive" ? 80 : data.sentiment === "neutral" ? 60 : 40;
      totalScore += score;
      sentiments[data.sentiment] = (sentiments[data.sentiment] || 0) + 1;
      for (const k of (data.keywords || [])) keywordsSet.add(k);
      items.push({ file: path.relative(process.cwd(), p), sentiment: data.sentiment, score });
    }
    const count = files.length || 1;
    let topSent = "neutral";
    let topCount = -1;
    for (const [s, c] of Object.entries(sentiments)) {
      if (c > topCount) {
        topCount = c;
        topSent = s;
      }
    }
    res.json({
      session_id: sessionId,
      file_count: files.length,
      aggregated_score: Math.round(totalScore / count),
      aggregated_sentiment: topSent,
      aggregated_keywords: Array.from(keywordsSet),
      items
    });
  } catch (e) {
    res.status(500).json({ error: "aggregate failed" });
  }
});

const port = process.env.PORT ? parseInt(process.env.PORT) : 8000;
app.listen(port, () => {});
