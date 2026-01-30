import express from "express";
import multer from "multer";
import cors from "cors";
import fetch from "node-fetch";

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer();

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
  res.json({ message: "registration email sent" });
});

app.post("/api/analyze", upload.single("file"), async (req, res) => {
  if (!req.file) {
    res.status(400).json({ error: "missing file" });
    return;
  }
  try {
    const ai = await fetch("http://127.0.0.1:8001/analyze", {
      method: "POST",
      body: req.file.buffer,
      headers: { "Content-Type": "application/octet-stream" }
    });
    const data = await ai.json();
    const score =
      data.sentiment === "positive" ? 80 : data.sentiment === "neutral" ? 60 : 40;
    res.json({ score, sentiment: data.sentiment, keywords: data.keywords || [] });
  } catch (e) {
    res.status(500).json({ error: "ai service failed" });
  }
});

const port = process.env.PORT ? parseInt(process.env.PORT) : 8000;
app.listen(port, () => {});
