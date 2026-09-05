(() => {
  "use strict";

  const API_BASE = ""; // same origin as this page

  // ---------------------------------------------------------------------
  // i18n
  // ---------------------------------------------------------------------
  const STRINGS = {
    fa: {
      brandName: "گفتار به نوشتار",
      engineChecking: "در حال بررسی موتور…",
      engineOnline: "موتور تشخیص گفتار متصل است",
      engineOffline: "موتور تشخیص گفتار در دسترس نیست",
      heroTitle: "صدا را بگو، تا برایت بنویسم",
      heroSub: "یک فایل صوتی بارگذاری کن یا زنده صحبت کن؛ متن آن را همین‌جا دریافت می‌کنی.",
      tabUpload: "بارگذاری فایل",
      tabRecord: "ضبط زنده",
      dzMain: "فایل صوتی را اینجا رها کن یا کلیک کن",
      dzSub: "WAV، MP3، M4A، OGG، WEBM — حداکثر ۵۰ مگابایت",
      recIdle: "برای شروع ضبط زنده، دکمه را بزن",
      recConnecting: "در حال اتصال به موتور…",
      recRecording: "در حال ضبط زنده…",
      recFinalizing: "در حال پردازش نهایی…",
      recDone: "آماده",
      liveLabel: "متن زنده",
      langOfAudio: "زبان فایل صوتی",
      langFa: "فارسی",
      langEn: "انگلیسی",
      langAuto: "تشخیص خودکار",
      submitBtn: "تبدیل به متن",
      submitBtnLoading: "در حال تبدیل…",
      resultTitle: "متن پیاده‌شده (نهایی)",
      copyBtn: "کپی متن",
      downloadBtn: "دانلود متن",
      footNote: "فایل‌های صوتی و متنی و لاگ‌ها به‌صورت محلی روی سرور ذخیره می‌شوند.",
      errNoFile: "ابتدا یک فایل صوتی انتخاب کن.",
      errGeneric: "خطایی رخ داد. دوباره تلاش کن.",
      errMic: "دسترسی به میکروفون ممکن نشد.",
      errNoMediaRecorder: "مرورگر شما از ضبط زنده پشتیبانی نمی‌کند.",
      copied: "کپی شد ✓",
      metaTemplate: "زبان: {lang} · مدت پردازش: {elapsed} ثانیه",
    },
    en: {
      brandName: "Speech to Text",
      engineChecking: "Checking engine…",
      engineOnline: "Speech engine connected",
      engineOffline: "Speech engine unavailable",
      heroTitle: "Say it, and I'll write it down",
      heroSub: "Upload an audio file or talk live — get the text right here.",
      tabUpload: "Upload file",
      tabRecord: "Live recording",
      dzMain: "Drop an audio file here, or click to browse",
      dzSub: "WAV, MP3, M4A, OGG, WEBM — up to 50 MB",
      recIdle: "Press the button to start live recording",
      recConnecting: "Connecting to the engine…",
      recRecording: "Recording live…",
      recFinalizing: "Finalizing…",
      recDone: "Done",
      liveLabel: "Live text",
      langOfAudio: "Audio language",
      langFa: "Farsi",
      langEn: "English",
      langAuto: "Auto-detect",
      submitBtn: "Transcribe",
      submitBtnLoading: "Transcribing…",
      resultTitle: "Final transcript",
      copyBtn: "Copy text",
      downloadBtn: "Download text",
      footNote: "Audio, text, and logs are stored locally on the server.",
      errNoFile: "Choose an audio file first.",
      errGeneric: "Something went wrong. Please try again.",
      errMic: "Could not access the microphone.",
      errNoMediaRecorder: "Your browser does not support live recording.",
      copied: "Copied ✓",
      metaTemplate: "Language: {lang} · Processed in {elapsed}s",
    },
  };

  let lang = "fa";

  function applyI18n() {
    const dict = STRINGS[lang];
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key] !== undefined) el.textContent = dict[key];
    });
    document.documentElement.lang = lang === "fa" ? "fa" : "en";
    document.documentElement.dir = lang === "fa" ? "rtl" : "ltr";
    document.body.classList.toggle("lang-en", lang === "en");
    langToggle.textContent = lang === "fa" ? "EN" : "فا";
    if (!engineOnline) engineLabel.textContent = dict.engineChecking;
  }

  // ---------------------------------------------------------------------
  // Elements
  // ---------------------------------------------------------------------
  const langToggle = document.getElementById("langToggle");
  const engineDot = document.getElementById("engineDot");
  const engineLabel = document.getElementById("engineLabel");

  const tabUpload = document.getElementById("tabUpload");
  const tabRecord = document.getElementById("tabRecord");
  const uploadMode = document.getElementById("uploadMode");
  const recordMode = document.getElementById("recordMode");

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const filePill = document.getElementById("filePill");
  const fileName = document.getElementById("fileName");
  const fileClear = document.getElementById("fileClear");
  const langSelectUpload = document.getElementById("langSelectUpload");
  const submitBtn = document.getElementById("submitBtn");

  const recBtn = document.getElementById("recBtn");
  const recWave = document.getElementById("recWave");
  const recTime = document.getElementById("recTime");
  const recStatus = document.getElementById("recStatus");
  const langSelectRecord = document.getElementById("langSelectRecord");
  const liveTextWrap = document.getElementById("liveTextWrap");
  const liveText = document.getElementById("liveText");

  const resultPanel = document.getElementById("resultPanel");
  const resultText = document.getElementById("resultText");
  const resultMeta = document.getElementById("resultMeta");
  const copyBtn = document.getElementById("copyBtn");
  const downloadBtn = document.getElementById("downloadBtn");

  const statusLine = document.getElementById("statusLine");

  let engineOnline = false;
  let selectedFile = null;

  // ---------------------------------------------------------------------
  // Engine health polling
  // ---------------------------------------------------------------------
  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      const data = await res.json();
      engineOnline = !!data.engine_online;
    } catch {
      engineOnline = false;
    }
    engineDot.classList.toggle("online", engineOnline);
    engineDot.classList.toggle("offline", !engineOnline);
    engineLabel.textContent = STRINGS[lang][engineOnline ? "engineOnline" : "engineOffline"];
  }
  checkHealth();
  setInterval(checkHealth, 15000);

  // ---------------------------------------------------------------------
  // Language toggle
  // ---------------------------------------------------------------------
  langToggle.addEventListener("click", () => {
    lang = lang === "fa" ? "en" : "fa";
    applyI18n();
  });

  // ---------------------------------------------------------------------
  // Mode tabs
  // ---------------------------------------------------------------------
  function setMode(mode) {
    tabUpload.classList.toggle("is-active", mode === "upload");
    tabRecord.classList.toggle("is-active", mode === "record");
    tabUpload.setAttribute("aria-selected", mode === "upload");
    tabRecord.setAttribute("aria-selected", mode === "record");
    uploadMode.hidden = mode !== "upload";
    recordMode.hidden = mode !== "record";
  }
  tabUpload.addEventListener("click", () => setMode("upload"));
  tabRecord.addEventListener("click", () => setMode("record"));

  function showStatus(msg) {
    statusLine.hidden = !msg;
    statusLine.textContent = msg || "";
  }

  function showResult(data) {
    resultText.value = data.text || "";
    resultMeta.textContent = STRINGS[lang].metaTemplate
      .replace("{lang}", data.language)
      .replace("{elapsed}", data.elapsed_seconds);
    resultPanel.hidden = false;
    resultPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // ---------------------------------------------------------------------
  // Upload flow
  // ---------------------------------------------------------------------
  function pickFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    filePill.hidden = false;
    submitBtn.disabled = false;
  }

  dropzone.addEventListener("click", (e) => {
    if (e.target === fileClear) return;
    fileInput.click();
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) pickFile(fileInput.files[0]);
  });
  ["dragover", "dragenter"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("is-drag"); })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("is-drag"); })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) pickFile(file);
  });
  fileClear.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = "";
    filePill.hidden = true;
    submitBtn.disabled = true;
  });

  submitBtn.addEventListener("click", async () => {
    showStatus("");
    if (!selectedFile) {
      showStatus(STRINGS[lang].errNoFile);
      return;
    }
    submitBtn.disabled = true;
    submitBtn.classList.add("is-loading");
    submitBtn.textContent = STRINGS[lang].submitBtnLoading;
    resultPanel.hidden = true;

    const form = new FormData();
    form.append("file", selectedFile);
    form.append("language", langSelectUpload.value);

    try {
      const res = await fetch(`${API_BASE}/api/transcribe`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || STRINGS[lang].errGeneric);
      }
      showResult(await res.json());
    } catch (err) {
      showStatus(err.message || STRINGS[lang].errGeneric);
    } finally {
      submitBtn.disabled = !selectedFile;
      submitBtn.classList.remove("is-loading");
      submitBtn.textContent = STRINGS[lang].submitBtn;
    }
  });

  // ---------------------------------------------------------------------
  // Live recording flow
  // ---------------------------------------------------------------------
  let mediaRecorder = null;
  let liveSocket = null;
  let micStream = null;
  let recordedChunks = [];
  let recordTimer = null;
  let recordSeconds = 0;
  let isRecording = false;
  let sessionId = null;

  function formatTime(sec) {
    const m = String(Math.floor(sec / 60)).padStart(2, "0");
    const s = String(sec % 60).padStart(2, "0");
    return `${m}:${s}`;
  }

  function newSessionId() {
    return (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`).replace(/-/g, "").slice(0, 8);
  }

  function wsUrl(path) {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${location.host}${path}`;
  }

  // wlk's live messages describe the current transcript state; the exact
  // schema can vary by version, so this pulls out whatever text field it
  // can find rather than assuming one fixed shape.
  function extractLiveText(raw) {
    try {
      const data = JSON.parse(raw);
      if (typeof data.text === "string" && data.text.trim()) return data.text;
      if (Array.isArray(data.lines)) {
        const joined = data.lines
          .map((l) => (typeof l === "string" ? l : l.text || l.transcript || ""))
          .filter(Boolean)
          .join(" ");
        if (joined.trim()) return joined;
      }
      if (typeof data.transcript === "string" && data.transcript.trim()) return data.transcript;
    } catch {
      // not JSON - ignore
    }
    return null;
  }

  async function startRecording() {
    if (!window.MediaRecorder) {
      showStatus(STRINGS[lang].errNoMediaRecorder);
      return;
    }
    showStatus("");
    liveText.textContent = "";
    liveTextWrap.hidden = false;
    resultPanel.hidden = true;
    recStatus.textContent = STRINGS[lang].recConnecting;

    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      showStatus(STRINGS[lang].errMic);
      liveTextWrap.hidden = true;
      return;
    }

    sessionId = newSessionId();
    recordedChunks = [];

    liveSocket = new WebSocket(wsUrl(`/ws/live?session_id=${sessionId}`));
    liveSocket.onmessage = (event) => {
      const text = extractLiveText(event.data);
      if (text) liveText.textContent = text;
    };
    liveSocket.onerror = () => {
      // Live preview is best-effort; the final result still comes from
      // /api/recording/finalize even if the live socket has trouble.
    };

    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";
    mediaRecorder = new MediaRecorder(micStream, { mimeType });

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        recordedChunks.push(e.data);
        if (liveSocket && liveSocket.readyState === WebSocket.OPEN) {
          liveSocket.send(e.data);
        }
      }
    };

    mediaRecorder.start(250); // emit a chunk every 250ms for a responsive live preview

    isRecording = true;
    recordSeconds = 0;
    recTime.textContent = formatTime(0);
    recBtn.classList.add("is-recording");
    recWave.classList.add("is-active");
    recStatus.textContent = STRINGS[lang].recRecording;
    recordTimer = setInterval(() => {
      recordSeconds += 1;
      recTime.textContent = formatTime(recordSeconds);
    }, 1000);
  }

  async function stopRecording() {
    isRecording = false;
    recBtn.classList.remove("is-recording");
    recWave.classList.remove("is-active");
    clearInterval(recordTimer);
    recStatus.textContent = STRINGS[lang].recFinalizing;

    await new Promise((resolve) => {
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.onstop = resolve;
        mediaRecorder.stop();
      } else {
        resolve();
      }
    });

    if (micStream) micStream.getTracks().forEach((t) => t.stop());
    if (liveSocket) {
      try { liveSocket.close(); } catch {}
      liveSocket = null;
    }

    if (recordedChunks.length === 0) {
      recStatus.textContent = STRINGS[lang].recIdle;
      liveTextWrap.hidden = true;
      return;
    }

    const blob = new Blob(recordedChunks, { type: "audio/webm" });
    const form = new FormData();
    form.append("file", blob, "recording.webm");
    form.append("session_id", sessionId);
    form.append("language", langSelectRecord.value);

    try {
      const res = await fetch(`${API_BASE}/api/recording/finalize`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || STRINGS[lang].errGeneric);
      }
      showResult(await res.json());
      recStatus.textContent = STRINGS[lang].recDone;
    } catch (err) {
      showStatus(err.message || STRINGS[lang].errGeneric);
      recStatus.textContent = STRINGS[lang].recIdle;
    }
  }

  recBtn.addEventListener("click", () => {
    if (isRecording) stopRecording();
    else startRecording();
  });

  // ---------------------------------------------------------------------
  // Result actions (shared by both flows)
  // ---------------------------------------------------------------------
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(resultText.value);
      const original = copyBtn.textContent;
      copyBtn.textContent = STRINGS[lang].copied;
      setTimeout(() => (copyBtn.textContent = STRINGS[lang].copyBtn), 1500);
    } catch {
      resultText.select();
      document.execCommand("copy");
    }
  });

  downloadBtn.addEventListener("click", () => {
    const blob = new Blob([resultText.value], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "transcript.txt";
    a.click();
    URL.revokeObjectURL(url);
  });

  // ---------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------
  applyI18n();
  setMode("upload");
})();
