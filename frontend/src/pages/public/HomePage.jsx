// Belongs in: frontend/src/pages/public/HomePage.jsx
// Public, unauthenticated landing page. Uses the OrbitalHeroSection as the
// hero background and VoicePoweredOrb as the AI voice assistant visual.
// Microphone access is only requested after the user explicitly clicks
// "Talk to TalentHire AI" (enableVoiceControl stays false until then).

import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext.jsx";
import { OrbitalHeroSection } from "../../components/effects/OrbitalHeroSection.jsx";
import { VoicePoweredOrb } from "../../components/effects/VoicePoweredOrb.jsx";

const INTRO_LINE =
  "Hi, I'm TalentHire AI. I can help you prepare for interviews, analyze your resume, and practice role-based interviews. Try asking me about resumes, mock interviews, or recruiters.";

// Lightweight, honest scope: this Home Page assistant recognizes real speech
// (via the browser's built-in Web Speech API — no API key, no server call)
// and replies from a small fixed knowledge base read aloud with the
// browser's built-in text-to-speech. It does NOT run a full AI conversation
// or the actual mock interview — that stays inside /candidate/interview,
// which uses the real Gemini + Whisper + Sentence-Transformers pipeline.
const KNOWLEDGE_BASE = [
  { keywords: ["resume", "cv", "ats", "skill"], reply: "You can upload your resume as a PDF after signing up. Our AI extracts your skills automatically using spaCy and SkillNER." },
  { keywords: ["interview", "mock", "practice", "question"], reply: "The Mock Interview module generates role-specific questions with Google Gemini, and scores your spoken or typed answers using semantic similarity." },
  { keywords: ["recruiter", "hire", "job", "post", "company"], reply: "Recruiters can post job openings, auto-generate interview questions, and review AI-ranked applicants from their dashboard." },
  { keywords: ["how", "work", "platform", "what"], reply: "TalentHire AI combines resume parsing, AI question generation, speech recognition, and semantic answer evaluation into one platform." },
  { keywords: ["price", "cost", "free", "pay"], reply: "TalentHire AI is free to try — just click Get Started to create a candidate or recruiter account." },
  { keywords: ["feedback", "score", "report"], reply: "After a mock interview, TalentHire AI generates a full report with your score, strengths, and areas to improve." },
];

function getReplyFor(transcript) {
  const lower = transcript.toLowerCase();
  const match = KNOWLEDGE_BASE.find(({ keywords }) => keywords.some((k) => lower.includes(k)));
  return match
    ? match.reply
    : "I can tell you about resumes, mock interviews, or how recruiters use TalentHire AI. What would you like to know?";
}

/**
 * Text-to-speech with the two fixes for the common "won't play / won't
 * replay" browser bugs:
 *  1. On first page load, getVoices() can return an empty list until the
 *     browser's async 'voiceschanged' event fires — speaking before that
 *     silently does nothing. We wait for voices to be ready first.
 *  2. Some browsers get stuck if a previous utterance wasn't fully
 *     cancelled — we always cancel() right before speaking a new line.
 */
function waitForVoices() {
  return new Promise((resolve) => {
    const existing = window.speechSynthesis.getVoices();
    if (existing.length > 0) {
      resolve(existing);
      return;
    }
    const handler = () => {
      window.speechSynthesis.removeEventListener("voiceschanged", handler);
      resolve(window.speechSynthesis.getVoices());
    };
    window.speechSynthesis.addEventListener("voiceschanged", handler);
    // Fallback in case the event never fires on some browsers
    setTimeout(() => resolve(window.speechSynthesis.getVoices()), 1000);
  });
}

async function speak(text, { onEnd, onStart } = {}) {
  if (!("speechSynthesis" in window)) {
    onEnd?.();
    return;
  }
  await waitForVoices();
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.onstart = () => onStart?.();
  utterance.onend = () => onEnd?.();
  utterance.onerror = () => onEnd?.();
  window.speechSynthesis.speak(utterance);
}

function getSpeechRecognitionCtor() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function NavBar({ user, onGetStarted }) {
  return (
    <header className="fixed top-0 left-0 right-0 z-30 border-b border-white/10 bg-black/40 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2">
          <img src="/logo.png" alt="TalentHire AI" className="h-8 w-8 rounded-lg object-contain" />
          <span className="text-lg font-bold text-white">TalentHire AI</span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-medium text-white/70 lg:flex">
          <a href="#about" className="hover:text-white">About</a>
          <a href="#features" className="hover:text-white">Features</a>
          <a href="#how-it-works" className="hover:text-white">How It Works</a>
          <a href="#for-candidates" className="hover:text-white">For Candidates</a>
          <a href="#for-recruiters" className="hover:text-white">For Recruiters</a>
          <a href="#ai-technology" className="hover:text-white">AI Technology</a>
          <a href="#contact" className="hover:text-white">Contact</a>
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <Link to={`/${user.role}/dashboard`} className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-white/90">
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-white/80 hover:text-white">
                Login
              </Link>
              <button
                onClick={onGetStarted}
                className="rounded-lg bg-gradient-to-r from-blue-500 via-cyan-400 to-purple-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-purple-500/20 hover:opacity-90"
              >
                Get Started
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

function GetStartedModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-8 text-center shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-2 text-xl font-bold text-white">What would you like to do?</h3>
        <p className="mb-6 text-sm text-white/60">Choose how you want to use TalentHire AI.</p>
        <div className="flex flex-col gap-3">
          <Link
            to="/register?role=candidate"
            className="rounded-lg bg-gradient-to-r from-blue-500 to-cyan-400 px-4 py-3 font-semibold text-white hover:opacity-90"
          >
            I'm a Candidate
          </Link>
          <Link
            to="/register?role=recruiter"
            className="rounded-lg bg-gradient-to-r from-purple-500 to-fuchsia-500 px-4 py-3 font-semibold text-white hover:opacity-90"
          >
            I'm a Recruiter
          </Link>
        </div>
        <button onClick={onClose} className="mt-5 text-xs text-white/40 hover:text-white/70">
          Cancel
        </button>
      </div>
    </div>
  );
}

function HeroSection({ onGetStarted, assistantActive, onTalkClick, onStopTalk, assistantStatus, transcript, reply }) {
  return (
    <section className="relative h-screen w-full">
      <OrbitalHeroSection
        className="absolute inset-0"
        scrim="left"
        scrimStrength={0.82}
        viewRadius={3.2}
      >
        <div className="flex h-full w-full items-center px-6 lg:px-16">
          <div className="max-w-xl">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300">
              AI-Powered Recruitment Platform
            </p>
            <h1 className="text-4xl font-extrabold leading-tight text-white sm:text-5xl lg:text-6xl">
              TALENTHIRE AI
            </h1>
            <p className="mt-4 text-xl font-medium text-white/90">
              AI-Powered Interview Evaluation Platform
            </p>
            <p className="mt-2 text-lg text-white/60">
              Prepare Better. Interview Smarter. Get Hired.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <button
                onClick={onGetStarted}
                className="rounded-lg bg-gradient-to-r from-blue-500 via-cyan-400 to-purple-500 px-6 py-3 font-semibold text-white shadow-lg shadow-purple-500/30 hover:opacity-90"
              >
                Get Started
              </button>

              <a
                href="#features"
                className="rounded-lg border border-white/30 px-6 py-3 font-semibold text-white hover:bg-white/10"
              >
                Explore Platform
              </a>

              {!assistantActive ? (
                <button
                  onClick={onTalkClick}
                  className="rounded-lg border border-cyan-300/50 bg-cyan-400/10 px-6 py-3 font-semibold text-cyan-200 hover:bg-cyan-400/20"
                >
                  🎙 Talk to TalentHire AI
                </button>
              ) : (
                <button
                  onClick={onStopTalk}
                  className="rounded-lg border border-rose-300/50 bg-rose-400/10 px-6 py-3 font-semibold text-rose-200 hover:bg-rose-400/20"
                >
                  ⏹ Stop Assistant
                </button>
              )}
            </div>

            {assistantActive && (
              <div className="mt-4 max-w-md space-y-1 text-sm">
                <p className="text-cyan-200/80">{assistantStatus}</p>
                {transcript && <p className="text-white/60">You said: "{transcript}"</p>}
                {reply && <p className="text-white/90">TalentHire AI: {reply}</p>}
              </div>
            )}
          </div>
        </div>
      </OrbitalHeroSection>

      {/* Voice assistant orb, right side of hero */}
      <div className="pointer-events-none absolute right-4 top-1/2 hidden h-72 w-72 -translate-y-1/2 sm:right-10 md:block lg:h-96 lg:w-96">
        <VoicePoweredOrb enableVoiceControl={assistantActive} hue={220} voiceSensitivity={1.6} />
      </div>
    </section>
  );
}

function Section({ id, eyebrow, title, children, dark = false }) {
  return (
    <section id={id} className={`px-6 py-20 lg:px-16 ${dark ? "bg-slate-950 text-white" : "bg-white text-slate-900"}`}>
      <div className="mx-auto max-w-6xl">
        {eyebrow && (
          <p className={`mb-2 text-xs font-semibold uppercase tracking-[0.25em] ${dark ? "text-cyan-300" : "text-brand-600"}`}>
            {eyebrow}
          </p>
        )}
        {title && <h2 className="mb-10 text-3xl font-bold">{title}</h2>}
        {children}
      </div>
    </section>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md">
      <div className="mb-3 text-3xl">{icon}</div>
      <h3 className="mb-2 font-semibold text-slate-800">{title}</h3>
      <p className="text-sm text-slate-500">{description}</p>
    </div>
  );
}

export default function HomePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [assistantActive, setAssistantActive] = useState(false);
  const [assistantStatus, setAssistantStatus] = useState("");
  const [transcript, setTranscript] = useState("");
  const [reply, setReply] = useState("");

  const recognitionRef = useRef(null);
  const activeRef = useRef(false); // mirrors assistantActive for use inside async callbacks

  const stopAssistant = () => {
    activeRef.current = false;
    setAssistantActive(false);
    setAssistantStatus("");
    setTranscript("");
    setReply("");
    window.speechSynthesis?.cancel();
    recognitionRef.current?.stop();
    recognitionRef.current = null;
  };

  const listenOnce = () => {
    if (!activeRef.current) return;

    const SpeechRecognitionCtor = getSpeechRecognitionCtor();
    if (!SpeechRecognitionCtor) {
      setAssistantStatus("Voice recognition isn't supported in this browser — try Chrome or Edge on desktop.");
      return;
    }

    setAssistantStatus("🎧 Listening...");
    const recognition = new SpeechRecognitionCtor();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      if (!activeRef.current) return;
      const heard = event.results[0][0].transcript;
      setTranscript(heard);
      setAssistantStatus("🤔 Thinking...");
      const answer = getReplyFor(heard);
      setReply(answer);
      setAssistantStatus("🔊 Speaking...");
      speak(answer, {
        onEnd: () => {
          if (activeRef.current) {
            setAssistantStatus("🎧 Listening...");
            listenOnce();
          }
        },
      });
    };

    recognition.onerror = (event) => {
      if (!activeRef.current) return;
      if (event.error === "no-speech" || event.error === "aborted") {
        // Quietly keep listening — this fires often and isn't a real error
        listenOnce();
      } else if (event.error === "not-allowed") {
        setAssistantStatus("Microphone access was denied. Please allow microphone access and try again.");
      } else {
        setAssistantStatus("Something went wrong with the microphone. Click the mic button to try again.");
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const handleTalkClick = () => {
    activeRef.current = true;
    setAssistantActive(true);
    setTranscript("");
    setReply("");
    setAssistantStatus("🔊 Speaking...");
    speak(INTRO_LINE, {
      onEnd: () => {
        if (activeRef.current) {
          setAssistantStatus("🎧 Listening...");
          listenOnce();
        }
      },
    });
  };

  const handleGetStarted = () => {
    if (user) {
      navigate(`/${user.role}/dashboard`);
    } else {
      setShowModal(true);
    }
  };

  useEffect(() => {
    return () => {
      activeRef.current = false;
      window.speechSynthesis?.cancel();
      recognitionRef.current?.stop();
    };
  }, []);

  return (
    <div className="min-h-screen bg-white">
      <NavBar user={user} onGetStarted={handleGetStarted} />
      {showModal && <GetStartedModal onClose={() => setShowModal(false)} />}

      <HeroSection
        onGetStarted={handleGetStarted}
        assistantActive={assistantActive}
        onTalkClick={handleTalkClick}
        onStopTalk={stopAssistant}
        assistantStatus={assistantStatus}
        transcript={transcript}
        reply={reply}
      />

      <Section id="about" eyebrow="About" title="A smarter way to prepare and hire">
        <p className="max-w-3xl text-lg text-slate-600">
          TalentHire AI combines machine learning, generative AI, and speech recognition into one
          platform — helping candidates practice real interviews with instant feedback, and helping
          recruiters screen and evaluate candidates faster and more fairly.
        </p>
      </Section>

      <Section id="features" eyebrow="Features" title="Everything you need, in one platform" dark>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <FeatureCard icon="📄" title="Resume Analysis" description="Upload your resume and get an instant skills breakdown and ATS compatibility score." />
          <FeatureCard icon="🎯" title="AI Question Generator" description="Role-specific interview questions generated dynamically for every job." />
          <FeatureCard icon="🎙" title="Voice-Based Interviews" description="Practice speaking your answers with real-time voice interaction." />
          <FeatureCard icon="📊" title="Answer Evaluation" description="Semantic scoring compares your answers against ideal responses." />
          <FeatureCard icon="📝" title="AI Feedback Reports" description="Personalized strengths, gaps, and improvement suggestions after every session." />
          <FeatureCard icon="🏢" title="Recruiter Dashboard" description="Post jobs, screen resumes, and review candidate interview reports in one place." />
        </div>
      </Section>

      <Section id="how-it-works" eyebrow="How It Works" title="From resume to offer, faster">
        <ol className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["1", "Upload your resume", "We extract your skills and match you to relevant roles."],
            ["2", "Practice a mock interview", "Answer AI-generated, role-specific questions."],
            ["3", "Get instant feedback", "See your score and a detailed AI-written report."],
            ["4", "Apply with confidence", "Recruiters review your profile and interview history."],
          ].map(([n, t, d]) => (
            <li key={n} className="rounded-xl border border-slate-200 p-6">
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 font-bold text-white">{n}</div>
              <h3 className="mb-1 font-semibold text-slate-800">{t}</h3>
              <p className="text-sm text-slate-500">{d}</p>
            </li>
          ))}
        </ol>
      </Section>

      <Section id="for-candidates" eyebrow="For Candidates" title="Walk into every interview prepared">
        <ul className="grid grid-cols-1 gap-3 text-slate-600 sm:grid-cols-2">
          <li>✅ Personalized mock interviews for your target role</li>
          <li>✅ Resume skill extraction and ATS scoring</li>
          <li>✅ Instant, detailed feedback after every session</li>
          <li>✅ Track your progress across multiple attempts</li>
        </ul>
      </Section>

      <Section id="for-recruiters" eyebrow="For Recruiters" title="Screen candidates in a fraction of the time" dark>
        <ul className="grid grid-cols-1 gap-3 text-white/70 sm:grid-cols-2">
          <li>✅ Post roles and auto-generate interview questions</li>
          <li>✅ AI-ranked applicants by skill match</li>
          <li>✅ Review interview scores and full transcripts</li>
          <li>✅ Centralized candidate analytics dashboard</li>
        </ul>
      </Section>

      <Section id="ai-technology" eyebrow="AI Technology" title="Built on real ML and generative AI">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 text-sm">
          <div className="rounded-lg bg-slate-50 p-4"><strong>Google Gemini</strong><p className="text-slate-500 mt-1">Question &amp; feedback generation</p></div>
          <div className="rounded-lg bg-slate-50 p-4"><strong>Sentence-Transformers</strong><p className="text-slate-500 mt-1">Semantic answer evaluation</p></div>
          <div className="rounded-lg bg-slate-50 p-4"><strong>spaCy + SkillNER</strong><p className="text-slate-500 mt-1">Resume skill extraction</p></div>
          <div className="rounded-lg bg-slate-50 p-4"><strong>Whisper</strong><p className="text-slate-500 mt-1">Speech-to-text transcription</p></div>
        </div>
      </Section>

      <section id="contact" className="bg-gradient-to-r from-blue-600 via-cyan-500 to-purple-600 px-6 py-16 text-center text-white lg:px-16">
        <h2 className="mb-3 text-3xl font-bold">Ready to get started?</h2>
        <p className="mb-6 text-white/80">Join TalentHire AI today — it's free to try.</p>
        <button onClick={handleGetStarted} className="rounded-lg bg-white px-6 py-3 font-semibold text-slate-900 hover:bg-white/90">
          Get Started
        </button>
      </section>

      <footer className="bg-slate-950 px-6 py-10 text-center text-sm text-white/40 lg:px-16">
        <p>© {new Date().getFullYear()} TalentHire AI — PES Institute of Technology &amp; Management, Shivamogga</p>
      </footer>
    </div>
  );
}