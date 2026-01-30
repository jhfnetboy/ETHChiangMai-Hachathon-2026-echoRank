import React, { useEffect, useRef, useState } from "react";

function App() {
  const [url, setUrl] = useState("");
  const [activityInfo, setActivityInfo] = useState<any>(null);
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [result, setResult] = useState<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const fetchActivity = async () => {
    if (!url) return;
    const res = await fetch(`http://127.0.0.1:8000/api/activity?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    setActivityInfo(data);
  };

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream);
    chunksRef.current = [];
    mr.ondataavailable = e => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    mr.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      setAudioBlob(blob);
      setRecording(false);
    };
    mediaRecorderRef.current = mr;
    mr.start();
    setRecording(true);
    timerRef.current = window.setTimeout(() => {
      mr.stop();
    }, 180000);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
    }
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  const submitAudio = async () => {
    if (!audioBlob) return;
    const fd = new FormData();
    fd.append("file", audioBlob, "feedback.webm");
    const res = await fetch("http://127.0.0.1:8000/api/analyze", { method: "POST", body: fd });
    const data = await res.json();
    setResult(data);
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: 16 }}>
      <h1>EchoRank</h1>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          style={{ flex: 1 }}
          placeholder="输入活动链接或搜索关键词"
          value={url}
          onChange={e => setUrl(e.target.value)}
        />
        <button onClick={fetchActivity}>获取</button>
      </div>
      {activityInfo && (
        <div style={{ marginTop: 12, padding: 12, border: "1px solid #ddd" }}>
          <div>标题：{activityInfo.title || "未识别"}</div>
          <div>摘要：{activityInfo.summary || "未识别"}</div>
        </div>
      )}
      <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
        {!recording && <button onClick={startRecording}>开始录音</button>}
        {recording && <button onClick={stopRecording}>停止录音</button>}
        <button onClick={submitAudio} disabled={!audioBlob}>
          提交语音
        </button>
      </div>
      {audioBlob && (
        <div style={{ marginTop: 12 }}>
          <audio controls src={URL.createObjectURL(audioBlob)} />
        </div>
      )}
      {result && (
        <div style={{ marginTop: 16, padding: 12, border: "1px solid #ddd" }}>
          <div>总体评分：{result.score}</div>
          <div>情感：{result.sentiment}</div>
          <div>关键词：{Array.isArray(result.keywords) ? result.keywords.join(", ") : ""}</div>
        </div>
      )}
      <div style={{ marginTop: 24 }}>
        <h2>Email 注册</h2>
        <EmailRegister />
      </div>
    </div>
  );
}

function EmailRegister() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const submit = async () => {
    if (!email) return;
    const res = await fetch("http://127.0.0.1:8000/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    const data = await res.json();
    setMsg(data.message || "ok");
  };
  return (
    <div style={{ display: "flex", gap: 8 }}>
      <input
        style={{ flex: 1 }}
        placeholder="输入邮箱"
        value={email}
        onChange={e => setEmail(e.target.value)}
      />
      <button onClick={submit}>注册并绑定</button>
      {msg && <span>{msg}</span>}
    </div>
  );
}

export default App;
