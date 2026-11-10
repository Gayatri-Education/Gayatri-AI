import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowUpRight,
  ArrowRight,
  ArrowLeft,
  BookOpen,
  LayoutDashboard,
  Clock3,
  GraduationCap,
  LogOut,
  Check,
  ShieldCheck,
  BarChart3,
  Image as ImageIcon,
  Flag,
  X,
  Menu,
  Atom,
  FlaskConical,
  Leaf,
  CircleHelp,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { api, go } from "./api";
import "./style.css";

const icons = { Physics: Atom, Chemistry: FlaskConical, Biology: Leaf };
const formatTime = (seconds) =>
  `${Math.floor(Math.max(0, seconds) / 60)
    .toString()
    .padStart(2, "0")}:${Math.floor(Math.max(0, seconds) % 60)
    .toString()
    .padStart(2, "0")}`;
function ErrorBox({ error }) {
  return error ? (
    <div className="error" role="alert">
      {error}
    </div>
  ) : null;
}
function Loading() {
  return (
    <div className="loading">
      <span className="spinner" /> Loading your workspace…
    </div>
  );
}
function RichText({ text = "" }) {
  return (
    <span className="question-text">
      {text.split(/(\[image:\s*[^\]]+\])/g).map((part, i) =>
        part.startsWith("[image:") ? (
          <span key={i} className="image-reference">
            <ImageIcon size={14} /> See source image
          </span>
        ) : (
          <React.Fragment key={i}>{part}</React.Fragment>
        ),
      )}
    </span>
  );
}
function SourceImage({ question, openByDefault = false }) {
  const [open, setOpen] = useState(openByDefault);
  if (!question.reference_image) return null;
  return (
    <div className="source">
      <button className="text-button" onClick={() => setOpen(!open)}>
        <ImageIcon size={16} />
        {open ? "Hide" : "View"} original question image <span>↗</span>
      </button>
      {open && (
        <a
          href={`/api/images/${question.reference_image}`}
          target="_blank"
          rel="noreferrer"
        >
          <img
            src={`/api/images/${question.reference_image}`}
            alt={`Original source for ${question.external_id}`}
            loading="lazy"
          />
        </a>
      )}
    </div>
  );
}

function Auth({ onLogin }) {
  const [register, setRegister] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const form = new FormData(e.currentTarget);
    try {
      onLogin(
        await api(`/auth/${register ? "register" : "login"}`, {
          method: "POST",
          body: Object.fromEntries(form),
        }),
      );
      go("/");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <div className="auth-story">
        <Brand />
        <div>
          <div className="eyebrow light">
            A LITTLE PRACTICE. A BIGGER POSSIBILITY.
          </div>
          <h1>
            Your next chapter
            <br />
            starts here<span>.</span>
          </h1>
          <p>
            Real questions. Focused sessions.
            <br />A clearer path to your medical dream.
          </p>
          <div className="auth-symbol">
            <Atom size={160} strokeWidth={0.65} />
            <span>NEET · 2015—2026</span>
          </div>
        </div>
        <small>Gayatri learning workspace</small>
      </div>
      <div className="auth-form">
        <span className="pill">
          <GraduationCap size={15} /> STUDENT WORKSPACE
        </span>
        <h2>{register ? "Make room for progress." : "Welcome back."}</h2>
        <p>
          {register
            ? "Create your account and begin a focused practice session."
            : "Pick up where you left off. Your practice is waiting."}
        </p>
        <form onSubmit={submit}>
          {register && (
            <label>
              Your name
              <input name="name" autoComplete="name" required maxLength={100} />
            </label>
          )}
          <label>
            Email address
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete={register ? "new-password" : "current-password"}
              minLength={10}
              maxLength={128}
              required
              placeholder="At least 10 characters"
            />
          </label>
          <ErrorBox error={error} />
          <button className="primary full" disabled={busy}>
            {busy ? "Please wait…" : register ? "Create account" : "Sign in"}
            <ArrowRight size={17} />
          </button>
        </form>
        <p className="auth-switch">
          {register ? "Already have an account?" : "New to Gayatri?"}{" "}
          <button
            onClick={() => {
              setRegister(!register);
              setError("");
            }}
          >
            {register ? "Sign in" : "Create an account"}
          </button>
        </p>
        <div className="auth-note">
          <ShieldCheck size={18} />
          <span>
            Your progress belongs to you.
            <br />
            Practice at your pace, in your own space.
          </span>
        </div>
      </div>
    </div>
  );
}
function Brand() {
  return (
    <div className="brand">
      <div className="brand-icon">
        <GraduationCap size={25} />
      </div>
      <div>
        gayatri<span>EXAM PORTAL</span>
      </div>
    </div>
  );
}
function App() {
  const [user, setUser] = useState(null),
    [initializing, setInitializing] = useState(true),
    [route, setRoute] = useState(location.hash.slice(1) || "/"),
    [mobileNav, setMobileNav] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    api("/auth/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setInitializing(false));
    const listen = () => {
      setRoute(location.hash.slice(1) || "/");
      setMobileNav(false);
    };
    addEventListener("hashchange", listen);
    return () => removeEventListener("hashchange", listen);
  }, []);
  async function logout() {
    try {
      await api("/auth/logout", { method: "POST" });
      setUser(null);
      go("/");
    } catch (e) {
      setError(e.message);
    }
  }
  if (initializing) return <Loading />;
  if (!user) return <Auth onLogin={setUser} />;
  const active = route.startsWith("/admin")
    ? "admin"
    : route.startsWith("/history")
      ? "history"
      : "home";
  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? "mobile-open" : ""}`}>
        <Brand />
        <div className="nav-label">YOUR WORKSPACE</div>
        <nav>
          <a href="#/" className={active === "home" ? "active" : ""}>
            <LayoutDashboard size={18} /> Overview <span className="nav-dot" />
          </a>
          <a href="#/history" className={active === "history" ? "active" : ""}>
            <Clock3 size={18} /> My attempts
          </a>
          {user.role === "admin" && (
            <a href="#/admin" className={active === "admin" ? "active" : ""}>
              <ShieldCheck size={18} /> Question review
            </a>
          )}
        </nav>
        <div className="sidebar-tip">
          <Sparkles size={22} />
          <h4>Small steps. Real progress.</h4>
          <p>One focused session today is one step closer to your goal.</p>
          <span>
            YOU’VE GOT THIS <ArrowUpRight size={14} />
          </span>
        </div>
        <div className="profile">
          <span className="avatar">{user.name.slice(0, 1).toUpperCase()}</span>
          <div>
            <strong>{user.name}</strong>
            <small>
              {user.role === "admin" ? "Administrator" : "NEET aspirant"}
            </small>
          </div>
          <button onClick={logout} aria-label="Sign out">
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <button
            className="menu-button"
            onClick={() => setMobileNav(!mobileNav)}
            aria-label="Toggle navigation"
          >
            <Menu size={22} />
          </button>
          <span>
            WORKSPACE <ChevronRight size={12} />{" "}
            <strong>
              {active === "admin"
                ? "Question review"
                : active === "history"
                  ? "My attempts"
                  : "Overview"}
            </strong>
          </span>
          <div className="topbar-right">
            <span className="green-dot" /> Ready when you are{" "}
            <span className="top-avatar">
              {user.name.slice(0, 1).toUpperCase()}
            </span>
          </div>
        </header>
        <div className="page-content">
          <ErrorBox error={error} />
          {route.startsWith("/attempt/") ? (
            <ExamTaking key={route} id={route.split("/")[2]} />
          ) : route.startsWith("/result/") ? (
            <ExamResult key={route} id={route.split("/")[2]} />
          ) : route.startsWith("/instructions/") ? (
            <Instructions id={route.split("/")[2]} />
          ) : route === "/history" ? (
            <History />
          ) : route === "/admin" ? (
            <Admin />
          ) : (
            <Dashboard user={user} />
          )}
        </div>
        <footer>
          © {new Date().getFullYear()} Gayatri{" "}
          <span>Built for a little more confidence, every day.</span>
          <span>LEARN. PRACTICE. PROGRESS.</span>
        </footer>
      </main>
    </div>
  );
}
function Dashboard({ user }) {
  const [exams, setExams] = useState(null),
    [history, setHistory] = useState([]),
    [error, setError] = useState("");
  useEffect(() => {
    Promise.all([api("/exams"), api("/attempts")])
      .then(([e, h]) => {
        setExams(e);
        setHistory(h);
      })
      .catch((e) => setError(e.message));
  }, []);
  if (!exams) return error ? <ErrorBox error={error} /> : <Loading />;
  const total = exams.reduce(
      (sum, e) => sum + e.sections.reduce((s, x) => s + x.bank_count, 0),
      0,
    ),
    completed = history.filter((x) => x.status !== "in_progress").length;
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">YOUR DAILY DOSE OF PROGRESS</div>
          <h1>
            Let’s make today count, {user.name.split(" ")[0]}
            <span className="purple">.</span>
          </h1>
          <p>
            A focused mind. A fresh start. Your next practice session awaits.
          </p>
        </div>
        <span className="date-label">
          {new Intl.DateTimeFormat("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric",
          }).format(new Date())}
        </span>
      </div>
      <section className="hero">
        <div className="hero-copy">
          <span className="hero-kicker">
            <span className="green-dot" /> YOUR MEDICAL JOURNEY, ONE QUESTION AT
            A TIME
          </span>
          <h2>
            Big dreams.
            <br />
            <em>Focused practice.</em>
          </h2>
          <p>
            Build confidence with real NEET past-year questions.
            <br />
            Choose your session. Find your rhythm. Keep growing.
          </p>
          <button
            className="cream-button"
            onClick={() =>
              document
                .getElementById("practice")
                .scrollIntoView({ behavior: "smooth" })
            }
          >
            Find your next session <ArrowUpRight size={17} />
          </button>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="orbit o1" />
          <div className="orbit o2" />
          <div className="orbit o3" />
          <div className="hero-atom">
            <Atom size={130} strokeWidth={0.8} />
          </div>
          <span className="art-card art-physics">
            <Atom /> Physics
          </span>
          <span className="art-card art-biology">
            <Leaf /> Biology
          </span>
          <span className="art-card art-chemistry">
            <FlaskConical /> Chemistry
          </span>
          <span className="art-spark">✧</span>
          <span className="art-caption">a little closer, every day.</span>
        </div>
      </section>
      <div className="stats-row">
        <Stat
          icon={BookOpen}
          value={total.toLocaleString("en-IN")}
          label="Past-year questions"
          detail="Your uploaded question bank"
        />
        <Stat
          icon={GraduationCap}
          value="12"
          label="Years of preparation"
          detail="2015 — 2026 source papers"
        />
        <Stat
          icon={Check}
          value={completed.toString().padStart(2, "0")}
          label="Sessions completed"
          detail="Every session is a step forward"
        />
      </div>
      <section id="practice">
        <div className="section-heading">
          <div>
            <div className="eyebrow">BUILD YOUR MOMENTUM</div>
            <h2>Your practice, your pace</h2>
          </div>
          <span className="muted">
            One exam. Three subjects. Endless potential.
          </span>
        </div>
        <div className="exam-grid">
          {exams.map((exam) => (
            <article className="exam-card" key={exam.id}>
              <div className="exam-card-top">
                <span className="exam-badge">
                  <GraduationCap size={26} />
                </span>
                <span className="pill green">PAST-YEAR PRACTICE</span>
              </div>
              <h3>NEET PYQ Practice</h3>
              <p>{exam.description}</p>
              <div className="subject-tags">
                {exam.sections.map((s) => {
                  const Icon = icons[s.subject] || BookOpen;
                  return (
                    <span key={s.subject} className={s.subject.toLowerCase()}>
                      <Icon size={14} />
                      {s.subject}
                    </span>
                  );
                })}
              </div>
              <div className="exam-meta">
                <span>
                  <BookOpen size={15} />
                  {exam.sections.reduce((s, x) => s + x.questions, 0)} questions
                </span>
                <span>
                  <Clock3 size={15} />
                  {exam.duration_seconds / 60} minutes
                </span>
                <span>2015–2026</span>
              </div>
              <div className="exam-card-bottom">
                <span>
                  <i className="green-dot" />
                  Unscored practice available
                </span>
                <button
                  className="primary"
                  onClick={() => go(`/instructions/${exam.id}`)}
                >
                  View session <ArrowRight size={16} />
                </button>
              </div>
            </article>
          ))}
          <article className="study-note">
            <span className="note-icon">
              <CircleHelp size={25} />
            </span>
            <div className="eyebrow">A NOTE BEFORE YOU BEGIN</div>
            <h3>
              Practice with
              <br />
              the full picture.
            </h3>
            <p>
              Source images are available with every question. Refer to them for
              diagrams, formulae, or unclear text.
            </p>
            <div className="note-divider" />
            <p className="small">
              Answer keys are awaiting review. Practice sessions show your
              responses without assigning an unverified score.
            </p>
            <span className="note-bottom">
              CLARITY OVER GUESSWORK <ArrowUpRight size={17} />
            </span>
          </article>
        </div>
      </section>
      <div className="section-heading recent-heading">
        <h2>Keep your momentum</h2>
        <a href="#/history" className="text-button">
          All attempts <ArrowRight size={15} />
        </a>
      </div>
      {history.length ? (
        <HistoryRows items={history.slice(0, 3)} />
      ) : (
        <div className="empty-inline">
          <div className="empty-icon">
            <Clock3 size={22} />
          </div>
          <div>
            <strong>Your story starts with one session.</strong>
            <p>Completed and in-progress attempts will appear here.</p>
          </div>
          <ArrowUpRight className="muted" size={20} />
        </div>
      )}
    </>
  );
}
function Stat({ icon: Icon, value, label, detail }) {
  return (
    <div className="stat">
      <span className="stat-icon">
        <Icon size={21} />
      </span>
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
        <small>{detail}</small>
      </div>
    </div>
  );
}
function Instructions({ id }) {
  const [exam, setExam] = useState(null),
    [mode, setMode] = useState("practice"),
    [year, setYear] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    api("/exams")
      .then((exams) => {
        const found = exams.find((x) => x.id === Number(id));
        if (!found) throw new Error("Exam not found");
        setExam(found);
      })
      .catch((e) => setError(e.message));
  }, [id]);
  async function start() {
    setBusy(true);
    setError("");
    try {
      const a = await api("/attempts", {
        method: "POST",
        body: { exam_id: exam.id, mode, year: year ? Number(year) : null },
      });
      go(`/attempt/${a.id}`);
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }
  return (
    <>
      <a href="#/" className="text-button">
        <ArrowLeft size={16} /> Back to overview
      </a>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SET YOURSELF UP FOR A GOOD SESSION</div>
          <h1>
            Before you begin<span className="purple">.</span>
          </h1>
          <p>A few things to know, then you’re ready.</p>
        </div>
      </div>
      <ErrorBox error={error} />
      {exam && (
        <div className="instructions-grid">
          <section className="panel">
            <h2>{exam.name}</h2>
            <p>{exam.description}</p>
            <div className="instruction-facts">
              <span>
                <Clock3 /> {exam.duration_seconds / 60} minutes
              </span>
              <span>
                <BookOpen />{" "}
                {exam.sections.reduce((s, x) => s + x.questions, 0)} questions
              </span>
            </div>
            <ol className="rules">
              <li>
                The timer starts as soon as you begin. The server enforces the
                deadline even if this tab is closed.
              </li>
              <li>
                Responses save when you select an option. Wait for “Saved”
                before leaving the page.
              </li>
              <li>
                Use the question palette to move around. Flag questions to
                revisit during this browser session.
              </li>
              <li>
                Check the original image for diagrams, formulas and OCR
                uncertainties. Difficulty labels are automated estimates.
              </li>
              <li>
                Unscored practice has no aggregate grade. Reviewed mocks award +
                {exam.marks_per_question} for a correct answer, −
                {exam.negative_marks} for an incorrect answer and 0 for an
                unanswered question.
              </li>
            </ol>
            <div className="notice">
              The uploaded papers and years have not been independently
              authenticated. This short study blueprint is not an official
              full-length NEET simulation.
            </div>
          </section>
          <section className="panel session-options">
            <h3>Make it your session</h3>
            <label>
              Session type
              <select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="practice">Unscored practice</option>
                <option value="mock" disabled={!exam.mock_ready}>
                  Reviewed mock{" "}
                  {exam.mock_ready ? "" : "— awaiting answer keys"}
                </option>
              </select>
            </label>
            <label>
              Source year
              <select value={year} onChange={(e) => setYear(e.target.value)}>
                <option value="">All years</option>
                {exam.years.map((y) => (
                  <option key={y}>{y}</option>
                ))}
              </select>
            </label>
            <div className="section-list">
              {exam.sections.map((s) => (
                <div key={s.subject}>
                  <span>{s.subject}</span>
                  <strong>{s.questions} questions</strong>
                </div>
              ))}
            </div>
            <p className="small">
              {mode === "practice"
                ? "No score will be assigned. Your responses and source images remain available after submission."
                : "Only questions approved by a reviewer with a sourced answer key are eligible."}
            </p>
            <button className="primary full" disabled={busy} onClick={start}>
              {busy ? "Preparing session…" : "Begin session"}
              <ArrowRight size={16} />
            </button>
          </section>
        </div>
      )}
    </>
  );
}
function ExamTaking({ id }) {
  const [attempt, setAttempt] = useState(null),
    [index, setIndex] = useState(0),
    [error, setError] = useState(""),
    [saving, setSaving] = useState(false),
    [saveLabel, setSaveLabel] = useState("All responses saved"),
    [remaining, setRemaining] = useState(0),
    [flagged, setFlagged] = useState(new Set()),
    [confirm, setConfirm] = useState(false),
    [submitting, setSubmitting] = useState(false);
  useEffect(() => {
    let active = true;
    let localDeadline = 0;
    async function sync() {
      try {
        const a = await api(`/attempts/${id}`);
        if (!active) return;
        if (a.status !== "in_progress") {
          go(`/result/${id}`);
          return;
        }
        localDeadline = Date.now() + a.remaining_seconds * 1000;
        setAttempt((current) => current || a);
        setRemaining(Math.ceil(a.remaining_seconds));
      } catch (e) {
        if (active) setError(e.message);
      }
    }
    sync();
    const timer = setInterval(() => {
      if (localDeadline) {
        const seconds = Math.ceil((localDeadline - Date.now()) / 1000);
        setRemaining(Math.max(0, seconds));
        if (seconds <= 0) {
          localDeadline = 0;
          sync();
        }
      }
    }, 1000);
    const poll = setInterval(sync, 15000);
    return () => {
      active = false;
      clearInterval(timer);
      clearInterval(poll);
    };
  }, [id]);
  async function choose(option) {
    setSaving(true);
    setError("");
    setSaveLabel("Saving…");
    try {
      await api(`/attempts/${id}/answer`, {
        method: "PUT",
        body: {
          question_id: attempt.questions[index].id,
          selected_option: option,
        },
      });
      setAttempt((a) => ({
        ...a,
        questions: a.questions.map((q, i) =>
          i === index ? { ...q, selected_option: option } : q,
        ),
      }));
      setSaveLabel("Saved");
    } catch (e) {
      setError(e.message);
      setSaveLabel("Not saved — retry");
    } finally {
      setSaving(false);
    }
  }
  async function submit() {
    setSubmitting(true);
    try {
      await api(`/attempts/${id}/submit`, { method: "POST" });
      go(`/result/${id}`);
    } catch (e) {
      setError(e.message);
      setSubmitting(false);
      setConfirm(false);
    }
  }
  if (!attempt) return error ? <ErrorBox error={error} /> : <Loading />;
  const q = attempt.questions[index],
    answered = attempt.questions.filter((q) => q.selected_option).length;
  return (
    <>
      <div className="exam-header">
        <div>
          <div className="eyebrow">
            {attempt.mode === "practice"
              ? "UNSCORED PRACTICE"
              : "REVIEWED MOCK"}
          </div>
          <h1>
            One question at a time<span className="purple">.</span>
          </h1>
        </div>
        <div
          className={`timer ${remaining < 120 ? "urgent" : ""}`}
          role="timer"
        >
          <Clock3 size={20} />
          <strong>{formatTime(remaining)}</strong>
          <span>remaining</span>
        </div>
      </div>
      <ErrorBox error={error} />
      {attempt.mode === "practice" && (
        <div className="notice">
          Study mode · Answer keys are not verified for this paper. Your
          responses will be saved without an aggregate score.
        </div>
      )}
      <div className="taking-grid">
        <section className="panel question-panel">
          <div className="question-heading">
            <span className={`pill ${q.subject.toLowerCase()}`}>
              {q.subject}
            </span>
            <span className="muted small">
              {q.year} · {q.difficulty} estimate
            </span>
            <button
              className={`flag-button ${flagged.has(index) ? "flagged" : ""}`}
              onClick={() =>
                setFlagged((s) => {
                  const next = new Set(s);
                  next.has(index) ? next.delete(index) : next.add(index);
                  return next;
                })
              }
            >
              <Flag size={16} />
              {flagged.has(index) ? "Flagged" : "Flag for review"}
            </button>
          </div>
          <div className="eyebrow question-number">
            QUESTION {String(index + 1).padStart(2, "0")} /{" "}
            {attempt.questions.length}
          </div>
          <h2 className="question-stem">
            <RichText text={q.text} />
          </h2>
          {q.review_flags && (
            <div className="review-note">
              This source has extraction review flags. Refer to the original
              image below.
            </div>
          )}
          <div className="options">
            {Object.entries(q.options).map(([letter, text]) => (
              <button
                key={letter}
                className={`option ${q.selected_option === letter ? "selected" : ""}`}
                onClick={() => choose(letter)}
                disabled={saving || submitting || remaining <= 0}
              >
                <span className="option-letter">{letter}</span>
                <RichText text={text} />
                {q.selected_option === letter && <Check size={17} />}
              </button>
            ))}
          </div>
          <SourceImage
            key={q.id}
            question={q}
            openByDefault={
              !!q.review_flags ||
              Object.values(q.options).some((x) => x.includes("[image:"))
            }
          />
          <div className="question-actions">
            <button
              className="secondary"
              disabled={!q.selected_option || saving || remaining <= 0}
              onClick={() => choose(null)}
            >
              Clear response
            </button>
            <span
              className={`save-status ${saveLabel.startsWith("Not") ? "failed" : ""}`}
            >
              {saving ? <span className="spinner" /> : <Check size={14} />}{" "}
              {saveLabel}
            </span>
          </div>
          <div className="question-nav">
            <button
              className="secondary"
              disabled={index === 0 || saving}
              onClick={() => setIndex(index - 1)}
            >
              <ArrowLeft size={15} />
              Previous
            </button>
            <button
              className="primary"
              disabled={index === attempt.questions.length - 1 || saving}
              onClick={() => setIndex(index + 1)}
            >
              Next question
              <ArrowRight size={15} />
            </button>
          </div>
        </section>
        <aside className="panel palette">
          <h3>Your session</h3>
          <p className="small">
            {answered} of {attempt.questions.length} answered
          </p>
          <div className="progress-track">
            <span
              style={{
                width: `${(answered / attempt.questions.length) * 100}%`,
              }}
            />
          </div>
          <div className="palette-grid">
            {attempt.questions.map((q, i) => (
              <button
                key={q.id}
                aria-label={`Question ${i + 1}`}
                aria-current={i === index ? "step" : undefined}
                disabled={saving}
                onClick={() => setIndex(i)}
                className={`${q.selected_option ? "answered" : ""} ${i === index ? "current" : ""} ${flagged.has(i) ? "flagged" : ""}`}
              >
                {i + 1}
                {flagged.has(i) && <i />}
              </button>
            ))}
          </div>
          <div className="palette-legend">
            <span>
              <i className="legend-answered" />
              Answered
            </span>
            <span>
              <i />
              Unanswered
            </span>
            <span>
              <i className="legend-flagged" />
              Flagged
            </span>
          </div>
          <button
            className="primary full"
            disabled={saving || submitting}
            onClick={() => setConfirm(true)}
          >
            Finish session
            <ArrowRight size={16} />
          </button>
          <p className="small muted">
            You can return to this attempt from My attempts while the timer is
            running.
          </p>
        </aside>
      </div>
      {confirm && (
        <div className="modal-backdrop">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="submit-title"
          >
            <button
              className="modal-close"
              onClick={() => setConfirm(false)}
              aria-label="Close"
            >
              <X size={20} />
            </button>
            <h2 id="submit-title">Ready to finish?</h2>
            <p>
              You have answered {answered} of {attempt.questions.length}{" "}
              questions. Submission is final.
            </p>
            <div className="modal-actions">
              <button
                className="secondary"
                disabled={submitting}
                onClick={() => setConfirm(false)}
              >
                Keep practising
              </button>
              <button
                className="primary"
                disabled={submitting}
                onClick={submit}
              >
                {submitting ? "Submitting…" : "Submit session"}
              </button>
            </div>
          </section>
        </div>
      )}
    </>
  );
}
function HistoryRows({ items }) {
  return (
    <div className="history-list">
      {items.map((a) => (
        <a
          key={a.id}
          href={`#/${a.status === "in_progress" ? "attempt" : "result"}/${a.id}`}
          className="history-row"
        >
          <div className="history-symbol">
            <BookOpen size={21} />
          </div>
          <div>
            <strong>{a.exam_name}</strong>
            <small>
              {new Date(a.started_at * 1000).toLocaleString("en-IN")} ·{" "}
              {a.mode === "practice" ? "Unscored practice" : "Reviewed mock"}
            </small>
          </div>
          <span className={`pill ${a.status === "in_progress" ? "" : "green"}`}>
            {a.status.replaceAll("_", " ")}
          </span>
          <strong>
            {a.raw_score === null ? "—" : `${a.raw_score} / ${a.max_score}`}
          </strong>
          <ArrowUpRight size={19} />
        </a>
      ))}
    </div>
  );
}
function History() {
  const [items, setItems] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/attempts")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">EVERY SESSION COUNTS</div>
          <h1>
            Your practice journey<span className="purple">.</span>
          </h1>
          <p>Resume a session or take a moment to reflect.</p>
        </div>
      </div>
      <ErrorBox error={error} />
      {items ? (
        items.length ? (
          <HistoryRows items={items} />
        ) : (
          <div className="panel">
            <h3>Your first session is waiting.</h3>
            <a href="#/" className="text-button">
              Explore practice <ArrowRight size={16} />
            </a>
          </div>
        )
      ) : (
        !error && <Loading />
      )}
    </>
  );
}
function ExamResult({ id }) {
  const [result, setResult] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    api(`/results/${id}`)
      .then(setResult)
      .catch((e) => setError(e.message));
  }, [id]);
  if (!result) return error ? <ErrorBox error={error} /> : <Loading />;
  const answered = result.questions.filter((q) => q.selected_option).length;
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">A STEP FORWARD, WELL TAKEN</div>
          <h1>
            Progress looks good on you<span className="purple">.</span>
          </h1>
          <p>
            {result.status === "auto_submitted"
              ? "Time elapsed. Your session was submitted automatically."
              : "Session complete. Here’s a moment to reflect and learn."}
          </p>
        </div>
        <a href="#/" className="primary">
          New session <ArrowRight size={16} />
        </a>
      </div>
      <div className="stats-row">
        <Stat
          icon={Check}
          value={`${answered}/${result.questions.length}`}
          label="Questions answered"
          detail="Your saved responses"
        />
        <Stat
          icon={BarChart3}
          value={
            result.raw_score === null
              ? "Unscored"
              : `${result.raw_score}/${result.max_score}`
          }
          label={
            result.raw_score === null ? "Practice session" : "Reviewed score"
          }
          detail={
            result.raw_score === null
              ? "No verified aggregate grade"
              : "+4 correct · −1 incorrect · 0 blank"
          }
        />
        <Stat
          icon={Clock3}
          value={formatTime(result.duration_seconds)}
          label="Session time limit"
          detail={result.status.replaceAll("_", " ")}
        />
      </div>
      {result.raw_score === null && (
        <div className="notice">
          This session is unscored. Missing answer keys remain marked “Awaiting
          verified key”; they are never guessed.
        </div>
      )}
      <section className="panel">
        <h2>Subject snapshot</h2>
        <div className="breakdown">
          {Object.entries(result.topic_breakdown).map(([subject, b]) => (
            <div key={subject}>
              <strong>{subject}</strong>
              <p>
                {b.answered}/{b.total} answered
              </p>
              <div className="progress-track">
                <span style={{ width: `${(b.answered / b.total) * 100}%` }} />
              </div>
              <small>
                {b.correct} correct · {b.incorrect} incorrect · {b.ungraded}{" "}
                ungraded responses
              </small>
            </div>
          ))}
        </div>
        <p className="small muted">{result.percentile_note}</p>
      </section>
      <div className="section-heading">
        <h2>Review your responses</h2>
        <span className="muted small">
          Original paper snapshots are retained.
        </span>
      </div>
      {result.questions.map((q, i) => (
        <section className="panel result-question" key={q.id}>
          <div className="question-heading">
            <span className="pill">
              QUESTION {i + 1} · {q.subject}
            </span>
            <span className="small muted">{q.year}</span>
          </div>
          <h3>
            <RichText text={q.text} />
          </h3>
          {Object.entries(q.options).map(([letter, value]) => (
            <div
              key={letter}
              className={`result-option ${q.correct_option === letter ? "correct" : q.selected_option === letter ? "chosen" : ""}`}
            >
              <strong>{letter}</strong>
              <RichText text={value} />
              {q.selected_option === letter && (
                <span className="small">Your response</span>
              )}
              {q.correct_option === letter && <Check size={16} />}
            </div>
          ))}
          <div className="review-note">
            {!q.selected_option && "Unanswered · "}
            {q.correct_option
              ? `Verified key: ${q.correct_option}. ${q.explanation}`
              : "Awaiting verified key — no correctness judgment available."}
          </div>
          {q.answer_key_source && (
            <p className="small muted">Key source: {q.answer_key_source}</p>
          )}
          <SourceImage question={q} />
        </section>
      ))}
    </>
  );
}
function Admin() {
  const [data, setData] = useState(null),
    [reports, setReports] = useState(null),
    [offset, setOffset] = useState(0),
    [subject, setSubject] = useState(""),
    [status, setStatus] = useState("pending"),
    [error, setError] = useState(""),
    [reload, setReload] = useState(0);
  useEffect(() => {
    setData(null);
    Promise.all([
      api(
        `/admin/questions?offset=${offset}&limit=5&subject=${encodeURIComponent(subject)}&status=${status}`,
      ),
      api("/admin/reports"),
    ])
      .then(([d, r]) => {
        setData(d);
        setReports(r);
      })
      .catch((e) => setError(e.message));
  }, [offset, subject, status, reload]);
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">HUMAN REVIEW, BEFORE A SCORE</div>
          <h1>
            A question bank you can trust<span className="purple">.</span>
          </h1>
          <p>
            Check the source image and supply a verified key before approving a
            question.
          </p>
        </div>
      </div>
      <ErrorBox error={error} />
      {reports && (
        <div className="stats-row">
          <Stat
            icon={BookOpen}
            value={reports.questions}
            label="Bank questions"
            detail={`${reports.flagged} with extraction flags`}
          />
          <Stat
            icon={ShieldCheck}
            value={reports.approved}
            label="Reviewed & approved"
            detail="Eligible for scored mocks"
          />
          <Stat
            icon={BarChart3}
            value={reports.completed}
            label="Completed attempts"
            detail={`${reports.users} registered users`}
          />
        </div>
      )}
      <div className="filter-bar">
        <label>
          Subject
          <select
            value={subject}
            onChange={(e) => {
              setSubject(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All subjects</option>
            {Object.keys(icons).map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          Review status
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setOffset(0);
            }}
          >
            <option value="pending">Awaiting review</option>
            <option value="approved">Approved</option>
            <option value="all">All questions</option>
          </select>
        </label>
        <span className="muted small">
          {data?.total ?? "…"} matching questions
        </span>
      </div>
      {data ? (
        <>
          {data.items.map((q) => (
            <ReviewCard
              key={`${q.id}-${q.version}`}
              q={q}
              onSaved={() => setReload((x) => x + 1)}
            />
          ))}
          {!data.items.length && (
            <div className="panel">No questions match this filter.</div>
          )}
          <div className="pagination">
            <button
              className="secondary"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 5))}
            >
              Previous
            </button>
            <span>
              {offset + (data.items.length ? 1 : 0)}–
              {offset + data.items.length} of {data.total}
            </span>
            <button
              className="secondary"
              disabled={offset + 5 >= data.total}
              onClick={() => setOffset(offset + 5)}
            >
              Next
            </button>
          </div>
        </>
      ) : (
        !error && <Loading />
      )}
    </>
  );
}
function ReviewCard({ q, onSaved }) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const values = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await api(`/admin/questions/${q.id}/review`, {
        method: "PUT",
        body: {
          ...values,
          version: q.version,
          confirm_source_reviewed: values.confirm_source_reviewed === "on",
        },
      });
      onSaved();
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }
  return (
    <section className="panel review-card">
      <div className="question-heading">
        <span className="pill">
          {q.subject} · {q.year}
        </span>
        <span className="small muted">{q.external_id}</span>
      </div>
      <h3>
        <RichText text={q.text} />
      </h3>
      {Object.entries(q.options).map(([k, v]) => (
        <p key={k}>
          <strong>{k}. </strong>
          <RichText text={v} />
        </p>
      ))}
      <p className="review-note">
        Extraction flags:{" "}
        {q.review_flags ||
          "None reported; manual verification is still required."}
      </p>
      <SourceImage question={q} openByDefault />
      <details>
        <summary>Source metadata</summary>
        <pre>{JSON.stringify(q.metadata, null, 2)}</pre>
      </details>
      <form onSubmit={save}>
        <div className="review-fields">
          <label>
            Verified correct option
            <select
              name="correct_option"
              defaultValue={q.correct_option || ""}
              required
            >
              <option value="" disabled>
                Select key
              </option>
              {["A", "B", "C", "D"].map((k) => (
                <option key={k}>{k}</option>
              ))}
            </select>
          </label>
          <label>
            Answer-key source / citation
            <input
              name="answer_key_source"
              defaultValue={q.answer_key_source}
              required
              minLength={5}
              maxLength={2000}
              placeholder="Official key reference or reviewer derivation"
            />
          </label>
        </div>
        <label>
          Verified explanation
          <textarea
            name="explanation"
            defaultValue={q.explanation}
            required
            minLength={5}
            maxLength={20000}
          />
        </label>
        <label className="checkbox-label">
          <input name="confirm_source_reviewed" type="checkbox" required />I
          checked the original image, all extraction flags, all options and the
          answer key. The question is suitable for scored use.
        </label>
        <ErrorBox error={error} />
        <button className="primary" disabled={busy}>
          {busy ? "Saving review…" : "Approve verified question"}
          <ShieldCheck size={16} />
        </button>
      </form>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
