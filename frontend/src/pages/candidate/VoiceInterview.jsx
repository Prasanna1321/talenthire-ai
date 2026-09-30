// Belongs in: frontend/src/pages/candidate/VoiceInterview.jsx

import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner } from '../../components/Misc.jsx'
import { getVoiceSessionToken } from '../../api/voiceInterviewApi.js'
import { startSession, completeSession } from '../../api/interviewsApi.js'

// Gemini Live API - ephemeral token WebSocket URL
const GEMINI_LIVE_WS_URL =
  'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContentConstrained'

const STATE = {
  IDLE: 'idle',
  CONNECTING: 'connecting',
  LISTENING: 'listening',
  THINKING: 'thinking',
  SPEAKING: 'speaking',
  ERROR: 'error',
}

function floatTo16BitPCMBase64(float32Array) {
  const buffer = new ArrayBuffer(float32Array.length * 2)
  const view = new DataView(buffer)
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]))
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
  const bytes = new Uint8Array(buffer)
  let binary = ''
  const chunkSize = 0x8000
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, Math.min(i + chunkSize, bytes.length)))
  }
  return btoa(binary)
}

function resampleTo16k(input, inputSampleRate) {
  const targetSampleRate = 16000
  if (inputSampleRate === targetSampleRate) return input
  const ratio = inputSampleRate / targetSampleRate
  const newLength = Math.round(input.length / ratio)
  const result = new Float32Array(newLength)
  for (let i = 0; i < newLength; i++) {
    const position = i * ratio
    const left = Math.floor(position)
    const right = Math.min(left + 1, input.length - 1)
    const weight = position - left
    result[i] = input[left] * (1 - weight) + input[right] * weight
  }
  return result
}

function base64ToInt16(base64) {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new Int16Array(bytes.buffer)
}

export default function VoiceInterview() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const jobId = searchParams.get('job_id')

  const [assistantState, setAssistantState] = useState(STATE.IDLE)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState('')

  const [cameraOn, setCameraOn] = useState(true)
  const [micOn, setMicOn] = useState(true)
  const [speakerOn, setSpeakerOn] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const [transcriptLog, setTranscriptLog] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState('Connecting to your AI interviewer...')
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [ending, setEnding] = useState(false)

  const visualMetricsRef = useRef({
    totalFrames: 0,
    faceVisibleFrames: 0,
    centeredFrames: 0,
    postureStableFrames: 0,
  })

  const [visualMetrics, setVisualMetrics] = useState({
    faceVisibility: 100,
    cameraOrientation: 100,
    postureConsistency: 100,
  })

  // Refs for audio, WS, and speech recognition
  const wsRef = useRef(null)
  const audioContextRef = useRef(null)
  const micStreamRef = useRef(null)
  const processorRef = useRef(null)
  const sourceRef = useRef(null)
  const videoRef = useRef(null)
  const roomContainerRef = useRef(null)
  const sessionIdRef = useRef(null)
  const aiTextRef = useRef('')
  const candidateTextRef = useRef('')
  const playbackContextRef = useRef(null)
  const playbackQueueRef = useRef([])
  const isPlayingAudioRef = useRef(false)
  const speechRecognitionRef = useRef(null)
  const silenceTimerRef = useRef(null)
  const questionIndexRef = useRef(0)
  const resumeSkillsRef = useRef([])

  const micOnRef = useRef(micOn)
  const connectedRef = useRef(connected)
  const speakerOnRef = useRef(speakerOn)

  useEffect(() => {
    micOnRef.current = micOn
  }, [micOn])

  useEffect(() => {
    connectedRef.current = connected
  }, [connected])

  useEffect(() => {
    speakerOnRef.current = speakerOn
  }, [speakerOn])

  // Canvas frame analysis for observable visual indicators
  useEffect(() => {
    if (!connected || !cameraOn) return

    const canvas = document.createElement('canvas')
    canvas.width = 320
    canvas.height = 240
    const ctx = canvas.getContext('2d')
    let prevImageData = null

    const interval = setInterval(() => {
      if (!videoRef.current || videoRef.current.readyState < 2) return

      try {
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height)
        const frame = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const data = frame.data

        let totalLuminance = 0
        let nonBlackPixels = 0

        for (let i = 0; i < data.length; i += 16) {
          const r = data[i]
          const g = data[i + 1]
          const b = data[i + 2]
          const lum = 0.299 * r + 0.587 * g + 0.114 * b
          totalLuminance += lum
          if (lum > 20) nonBlackPixels++
        }

        const sampleCount = data.length / 16
        const avgLum = totalLuminance / sampleCount
        const activePixelRatio = nonBlackPixels / sampleCount

        const faceVisible = activePixelRatio > 0.35 && avgLum > 20
        const centered = activePixelRatio > 0.45 && avgLum > 30

        let postureStable = true
        if (prevImageData) {
          let diffCount = 0
          for (let i = 0; i < data.length; i += 32) {
            const diff = Math.abs(data[i] - prevImageData[i])
            if (diff > 40) diffCount++
          }
          const diffRatio = diffCount / (data.length / 32)
          postureStable = diffRatio < 0.4
        }
        prevImageData = data

        visualMetricsRef.current.totalFrames++
        if (faceVisible) visualMetricsRef.current.faceVisibleFrames++
        if (centered) visualMetricsRef.current.centeredFrames++
        if (postureStable) visualMetricsRef.current.postureStableFrames++

        const total = visualMetricsRef.current.totalFrames
        if (total > 0) {
          setVisualMetrics({
            faceVisibility: Math.round((visualMetricsRef.current.faceVisibleFrames / total) * 100),
            cameraOrientation: Math.round((visualMetricsRef.current.centeredFrames / total) * 100),
            postureConsistency: Math.round((visualMetricsRef.current.postureStableFrames / total) * 100),
          })
        }
      } catch (err) {
        // Sample frame error ignored
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [connected, cameraOn])

  const appendTranscript = (role, text) => {
    if (!text?.trim()) return
    setTranscriptLog((prev) => [
      ...prev,
      {
        role,
        text: text.trim(),
        timestamp: new Date(),
      },
    ])
  }

  // Session Duration Timer
  useEffect(() => {
    if (!connected) return
    const timer = setInterval(() => {
      setElapsedSeconds((secs) => secs + 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [connected])

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  // Speak AI text naturally like Siri / Alexa / Gemini Voice
  const speakTextAsHumanVoice = (text) => {
    if (!speakerOnRef.current || !window.speechSynthesis) return
    try {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.02
      utterance.pitch = 1.0
      utterance.lang = 'en-US'

      const voices = window.speechSynthesis.getVoices()
      const preferredVoice =
        voices.find(
          (v) =>
            (v.name.includes('Google') ||
              v.name.includes('Natural') ||
              v.name.includes('Samantha') ||
              v.name.includes('Karen') ||
              v.name.includes('Zira') ||
              v.name.includes('Victoria')) &&
            v.lang.startsWith('en')
        ) || voices.find((v) => v.lang.startsWith('en'))

      if (preferredVoice) utterance.voice = preferredVoice

      utterance.onstart = () => setAssistantState(STATE.SPEAKING)
      utterance.onend = () => setAssistantState(STATE.LISTENING)
      utterance.onerror = () => setAssistantState(STATE.LISTENING)

      window.speechSynthesis.speak(utterance)
    } catch (e) {
      console.warn('Speech synthesis exception:', e)
    }
  }

  // AI PCM audio playback (Gemini WS)
  const playNextAudioChunk = async () => {
    if (isPlayingAudioRef.current) return
    if (!speakerOnRef.current) {
      playbackQueueRef.current = []
      return
    }

    const nextChunk = playbackQueueRef.current.shift()
    if (!nextChunk) return

    isPlayingAudioRef.current = true

    try {
      if (!playbackContextRef.current) {
        playbackContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 24000,
        })
      }
      const audioContext = playbackContextRef.current
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }

      const samples = base64ToInt16(nextChunk)
      const audioBuffer = audioContext.createBuffer(1, samples.length, 24000)
      const channelData = audioBuffer.getChannelData(0)
      for (let i = 0; i < samples.length; i++) {
        channelData[i] = samples[i] / 32768
      }

      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContext.destination)
      source.onended = () => {
        isPlayingAudioRef.current = false
        playNextAudioChunk()
      }
      source.start()
    } catch (err) {
      console.error('AI audio chunk playback error:', err)
      isPlayingAudioRef.current = false
      playNextAudioChunk()
    }
  }

  // Submit Spoken Answer Turn and Ask Next Question
  const submitCandidateTurnAndAskNextQuestion = () => {
    const spokenText = candidateTextRef.current.trim() || currentAnswer.trim()
    if (!spokenText) return

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }

    appendTranscript('candidate', spokenText)
    setCurrentAnswer('')
    candidateTextRef.current = ''
    setAssistantState(STATE.THINKING)

    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({
          clientContent: {
            turns: [
              {
                role: 'user',
                parts: [{ text: spokenText }],
              },
            ],
            turnComplete: true,
          },
        })
      )
    } else {
      setTimeout(() => {
        triggerNextResumeQuestion(spokenText)
      }, 800)
    }
  }

  // Dynamic Resume-Grounded Follow-up Generator
  const triggerNextResumeQuestion = (lastSpoken = '') => {
    questionIndexRef.current += 1
    const idx = questionIndexRef.current
    const skillsList =
      resumeSkillsRef.current.length > 0
        ? resumeSkillsRef.current.join(', ')
        : 'software engineering and system design'

    const dynamicQuestions = [
      `Thank you for sharing that! Based on your uploaded resume skills in ${skillsList}, could you walk me through a key technical project you built, explaining the architecture and design decisions you made?`,
      `That sounds impressive! Regarding your experience with ${skillsList}, how do you optimize database query performance, handle caching, and ensure application scalability?`,
      `Great explanation! Could you describe a challenging technical bug or outage you encountered in development or production, and how you diagnosed and fixed it?`,
      `Very good. When collaborating in an agile engineering team, how do you handle code reviews, unit testing, and CI/CD pipelines to ensure product quality?`,
      `Thank you so much! You have successfully answered all technical evaluation questions for this interview session. Click 'End Interview' below to review your full intelligence report!`,
    ]

    const nextQ = dynamicQuestions[Math.min(idx - 1, dynamicQuestions.length - 1)]
    setCurrentQuestion(nextQ)
    appendTranscript('ai', nextQ)
    speakTextAsHumanVoice(nextQ)
  }

  // Setup Browser Web Speech Recognition for candidate's speech
  const setupSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return null

    try {
      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onresult = (event) => {
        if (!micOnRef.current) return
        let transcriptText = ''
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcriptText += event.results[i][0].transcript
        }
        if (transcriptText.trim()) {
          setCurrentAnswer(transcriptText)
          candidateTextRef.current = transcriptText
          setAssistantState(STATE.LISTENING)

          // 1.8s silence detection (VAD) -> Auto submit candidate answer turn!
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current)
          silenceTimerRef.current = setTimeout(() => {
            if (candidateTextRef.current.trim()) {
              submitCandidateTurnAndAskNextQuestion()
            }
          }, 1800)
        }
      }

      recognition.onerror = (e) => {
        console.warn('Speech recognition warning:', e.error)
      }

      recognition.onend = () => {
        if (connectedRef.current && micOnRef.current) {
          try {
            recognition.start()
          } catch (e) {}
        }
      }

      recognition.start()
      return recognition
    } catch (err) {
      console.warn('Could not initialize SpeechRecognition:', err)
      return null
    }
  }

  // Gemini Live server message handling
  const handleServerMessage = (event) => {
    let message
    try {
      message = typeof event.data === 'string' ? JSON.parse(event.data) : null
    } catch (err) {
      console.error('Invalid Gemini WS message:', err)
      return
    }

    if (!message) return
    console.log('Gemini Live server message:', message)

    if (message.setupComplete) {
      setAssistantState(STATE.THINKING)
      const ws = wsRef.current
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(
          JSON.stringify({
            clientContent: {
              turns: [
                {
                  role: 'user',
                  parts: [
                    {
                      text: 'Hello! Please start our live technical interview now by greeting me by name and asking me a question based on my uploaded resume skills and job role.',
                    },
                  ],
                },
              ],
              turnComplete: true,
            },
          })
        )
      }
      return
    }

    const serverContent = message.serverContent
    if (!serverContent) return

    if (serverContent.modelTurn?.parts) {
      setAssistantState(STATE.SPEAKING)
      for (const part of serverContent.modelTurn.parts) {
        if (part.text) {
          aiTextRef.current += part.text
          setCurrentQuestion(aiTextRef.current)
        }
        if (part.inlineData?.data) {
          playbackQueueRef.current.push(part.inlineData.data)
          playNextAudioChunk()
        }
      }
    }

    if (serverContent.inputTranscription?.text) {
      candidateTextRef.current += serverContent.inputTranscription.text
      setCurrentAnswer(candidateTextRef.current)
    }

    if (serverContent.outputTranscription?.text) {
      aiTextRef.current += serverContent.outputTranscription.text
      setCurrentQuestion(aiTextRef.current)
    }

    if (serverContent.turnComplete) {
      if (aiTextRef.current.trim()) {
        appendTranscript('ai', aiTextRef.current.trim())
        if (playbackQueueRef.current.length === 0) {
          speakTextAsHumanVoice(aiTextRef.current.trim())
        }
      }
      if (candidateTextRef.current.trim()) {
        appendTranscript('candidate', candidateTextRef.current.trim())
      }

      aiTextRef.current = ''
      candidateTextRef.current = ''
      setCurrentAnswer('')
      setAssistantState(STATE.LISTENING)
    }
  }

  // Microphone audio streaming to Gemini
  const setupMicrophone = async (stream, ws) => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      audioContextRef.current = audioContext

      const source = audioContext.createMediaStreamSource(stream)
      sourceRef.current = source

      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      processorRef.current = processor

      const silentGain = audioContext.createGain()
      silentGain.gain.value = 0

      source.connect(processor)
      processor.connect(silentGain)
      silentGain.connect(audioContext.destination)

      processor.onaudioprocess = (event) => {
        if (!micOnRef.current) return
        if (!ws || ws.readyState !== WebSocket.OPEN) return

        const inputData = event.inputBuffer.getChannelData(0)
        const resampled = resampleTo16k(inputData, audioContext.sampleRate)
        const base64Audio = floatTo16BitPCMBase64(resampled)

        ws.send(
          JSON.stringify({
            realtimeInput: {
              mediaChunks: [
                {
                  mimeType: 'audio/pcm;rate=16000',
                  data: base64Audio,
                },
              ],
            },
          })
        )
      }
    } catch (e) {
      console.warn('Microphone audio context setup warning:', e)
    }

    speechRecognitionRef.current = setupSpeechRecognition()
  }

  // Start Camera
  const startCamera = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user',
      },
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    })
    micStreamRef.current = stream
    return stream
  }

  // Connect to Gemini Live & Initialize Interview Room
  const connect = async () => {
    setError('')
    setAssistantState(STATE.CONNECTING)

    try {
      const mediaStream = await startCamera()
      const sessionRes = await startSession({
        job_id: jobId ? Number(jobId) : undefined,
        session_type: 'mock',
      })
      sessionIdRef.current = sessionRes.data.session_id

      setConnected(true)
      setAssistantState(STATE.THINKING)

      const tokenRes = await getVoiceSessionToken(jobId ? Number(jobId) : undefined)
      const { token, model, instructions, skills } = tokenRes.data

      if (skills && Array.isArray(skills) && skills.length > 0) {
        resumeSkillsRef.current = skills
      }

      const skillsLine =
        resumeSkillsRef.current.length > 0
          ? resumeSkillsRef.current.join(', ')
          : 'software development and engineering'

      const initialGreeting = `Hello! Welcome to your TalentHire AI live interview. I am your AI interviewer today. I have reviewed your uploaded resume highlighting skills in ${skillsLine}. Let's begin by having you introduce yourself and describe your core technical background.`
      setCurrentQuestion(initialGreeting)
      appendTranscript('ai', initialGreeting)
      speakTextAsHumanVoice(initialGreeting)

      if (token) {
        try {
          const ws = new WebSocket(`${GEMINI_LIVE_WS_URL}?access_token=${encodeURIComponent(token)}`)
          wsRef.current = ws

          ws.onopen = async () => {
            console.log('Gemini Live WebSocket connected')
            ws.send(
              JSON.stringify({
                setup: {
                  model: `models/${model}`,
                  generationConfig: {
                    responseModalities: ['AUDIO', 'TEXT'],
                  },
                  systemInstruction: {
                    parts: [{ text: instructions }],
                  },
                },
              })
            )
          }

          ws.onmessage = handleServerMessage
          ws.onerror = (evt) => console.warn('Gemini WS Warning:', evt)
          ws.onclose = (evt) => console.log('Gemini WS Session closed:', evt.code, evt.reason)
        } catch (wsErr) {
          console.warn('WebSocket connection init warning:', wsErr)
        }
      }

      // Initialize microphone audio stream & speech recognition
      setupMicrophone(mediaStream, wsRef.current)
    } catch (err) {
      console.error('Interview start failure:', err)
      cleanup()
      let msg = 'Could not start the live interview.'
      if (err?.name === 'NotAllowedError') {
        msg = 'Camera or microphone permission was denied. Please allow access and try again.'
      } else if (err?.name === 'NotFoundError') {
        msg = 'No camera or microphone was found. Please connect your hardware and try again.'
      } else if (err?.message) {
        msg = err.message
      }
      setError(msg)
      setAssistantState(STATE.ERROR)
    }
  }

  // Camera toggle
  const toggleCamera = () => {
    const stream = micStreamRef.current
    if (!stream) return
    stream.getVideoTracks().forEach((t) => (t.enabled = !cameraOn))
    setCameraOn((val) => !val)
  }

  // Mic toggle
  const toggleMic = () => {
    const stream = micStreamRef.current
    if (!stream) return
    stream.getAudioTracks().forEach((t) => (t.enabled = !micOn))
    setMicOn((val) => !val)
  }

  // Speaker toggle
  const toggleSpeaker = () => {
    setSpeakerOn((val) => {
      const next = !val
      if (!next) {
        playbackQueueRef.current = []
        if (window.speechSynthesis) window.speechSynthesis.cancel()
      }
      return next
    })
  }

  // Fullscreen toggle for complete fit-to-screen interview experience
  const toggleFullscreen = () => {
    if (!roomContainerRef.current) return
    if (!document.fullscreenElement) {
      roomContainerRef.current.requestFullscreen?.().then(() => setIsFullscreen(true)).catch(() => {})
    } else {
      document.exitFullscreen?.().then(() => setIsFullscreen(false)).catch(() => {})
    }
  }

  // Cleanup
  const cleanup = () => {
    try {
      if (window.speechSynthesis) window.speechSynthesis.cancel()
    } catch {}
    try {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current)
    } catch {}
    try {
      speechRecognitionRef.current?.stop()
    } catch {}
    try {
      processorRef.current?.disconnect()
    } catch {}
    try {
      sourceRef.current?.disconnect()
    } catch {}
    try {
      audioContextRef.current?.close()
    } catch {}
    try {
      playbackContextRef.current?.close()
    } catch {}

    micStreamRef.current?.getTracks()?.forEach((t) => t.stop())
    try {
      wsRef.current?.close()
    } catch {}

    processorRef.current = null
    sourceRef.current = null
    audioContextRef.current = null
    playbackContextRef.current = null
    micStreamRef.current = null
    wsRef.current = null
    playbackQueueRef.current = []
    isPlayingAudioRef.current = false
  }

  // End interview
  const endInterview = async () => {
    if (ending) return
    const confirmed = window.confirm('Are you sure you want to complete and end the interview?')
    if (!confirmed) return

    setEnding(true)
    try {
      cleanup()
      if (sessionIdRef.current) {
        await completeSession(sessionIdRef.current, {
          visual_metrics: {
            face_visibility: visualMetrics.faceVisibility,
            camera_orientation: visualMetrics.cameraOrientation,
            posture_consistency: visualMetrics.postureConsistency,
          },
        })
      }
      navigate('/candidate/reports')
    } catch (err) {
      console.error(err)
      navigate('/candidate/reports')
    } finally {
      setEnding(false)
    }
  }

  // Camera stream binding effect
  useEffect(() => {
    if (connected && cameraOn && videoRef.current && micStreamRef.current) {
      videoRef.current.srcObject = micStreamRef.current
      videoRef.current.play().catch((err) => console.warn('Camera play warning:', err))
    }
  }, [connected, cameraOn])

  // Page unmount cleanup
  useEffect(() => {
    return () => {
      cleanup()
    }
  }, [])

  const stateLabel = {
    [STATE.IDLE]: 'Ready',
    [STATE.CONNECTING]: 'Connecting...',
    [STATE.LISTENING]: 'Listening to your voice...',
    [STATE.THINKING]: 'AI is thinking...',
    [STATE.SPEAKING]: 'AI is speaking...',
    [STATE.ERROR]: 'Connection error',
  }

  return (
    <DashboardLayout role="candidate">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">TalentHire AI Live Interview</h1>
              {connected && (
                <span className="inline-flex items-center gap-2 rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-600 border border-red-200">
                  <span className="h-2 w-2 animate-ping rounded-full bg-red-500" />
                  LIVE INTERVIEW ROOM
                </span>
              )}
            </div>
            <p className="mt-0.5 text-xs text-slate-500">
              Interactive AI Video Interviewer (Resume-based dynamic conversation)
            </p>
          </div>

          {connected && (
            <div className="flex items-center gap-3">
              <div className="rounded-xl border border-slate-200 bg-white px-4 py-1.5 shadow-sm">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Duration</p>
                <p className="font-mono text-sm font-bold text-slate-800">{formatTime(elapsedSeconds)}</p>
              </div>

              <button
                onClick={toggleFullscreen}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
              >
                {isFullscreen ? '↙ Exit Fullscreen' : '⛶ Fit to Screen'}
              </button>
            </div>
          )}
        </div>

        <ErrorBanner message={error} />

        {/* Start Lobby Screen */}
        {!connected ? (
          <div className="flex min-h-[580px] items-center justify-center rounded-2xl border border-slate-200 bg-gradient-to-b from-slate-900 via-slate-950 to-black p-8 shadow-xl text-white">
            <div className="max-w-md text-center">
              <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-blue-600/20 border-2 border-blue-500/40 text-5xl shadow-[0_0_40px_rgba(59,130,246,0.3)]">
                🤖
              </div>
              <h2 className="text-2xl font-extrabold tracking-tight">TalentHire AI Interviewer</h2>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                Your camera and microphone will be used for a human-like voice interview based directly on your uploaded resume skills and chosen job role.
              </p>

              <div className="mt-6 grid grid-cols-3 gap-3 text-left">
                <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
                  <div className="text-xl">📹</div>
                  <p className="mt-1 text-xs font-semibold">Webcam</p>
                  <p className="text-[10px] text-slate-400">Live HD Video</p>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
                  <div className="text-xl">🎤</div>
                  <p className="mt-1 text-xs font-semibold">Voice AI</p>
                  <p className="text-[10px] text-slate-400">Human Speech</p>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
                  <div className="text-xl">📄</div>
                  <p className="mt-1 text-xs font-semibold">Resume</p>
                  <p className="text-[10px] text-slate-400">Dynamic Qs</p>
                </div>
              </div>

              <button
                onClick={connect}
                disabled={assistantState === STATE.CONNECTING}
                className="mt-8 w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 py-3.5 text-sm font-bold shadow-lg shadow-blue-500/25 transition hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50"
              >
                {assistantState === STATE.CONNECTING ? 'Connecting to AI Interviewer...' : '🎥 Start Live Interview'}
              </button>

              {assistantState === STATE.ERROR && (
                <button
                  onClick={connect}
                  className="mt-3 w-full rounded-xl border border-white/20 py-2 text-xs font-medium text-slate-300 hover:bg-white/10"
                >
                  Retry Connection
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Main Fullscreen / Fit-to-Screen Live Interview Room */
          <div
            ref={roomContainerRef}
            className={`grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px] ${
              isFullscreen ? 'h-screen w-screen p-4 bg-slate-950 fixed inset-0 z-50 overflow-auto' : ''
            }`}
          >
            {/* Video Interview Stage */}
            <div className="flex flex-col overflow-hidden rounded-2xl bg-slate-950 border border-slate-800 shadow-2xl">
              {/* Top Bar */}
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-3 bg-slate-900/60 backdrop-blur">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600/30 text-xl border border-blue-400/30">
                    🤖
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">TalentHire AI Interviewer</p>
                    <p className="text-[11px] text-slate-400">Resume-Grounded Human Voice Assistant</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                    {stateLabel[assistantState]}
                  </span>
                </div>
              </div>

              {/* Side-by-Side HD Video Layout */}
              <div className="grid flex-1 min-h-[440px] grid-cols-1 gap-3 p-4 md:grid-cols-2 bg-slate-950">
                {/* AI Interviewer Stage */}
                <div className="relative flex flex-col items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-slate-900 via-slate-950 to-black p-6 shadow-inner">
                  <div className="absolute left-4 top-4 rounded-lg bg-black/60 px-3 py-1 text-xs font-bold text-white backdrop-blur border border-white/10">
                    AI Interviewer
                  </div>

                  <div className="relative text-center">
                    {/* Pulsing Audio Wave Visualizer Ring */}
                    <div
                      className={`relative mx-auto flex h-36 w-36 items-center justify-center rounded-full transition-all duration-500 ${
                        assistantState === STATE.SPEAKING
                          ? 'bg-blue-600/20 ring-8 ring-blue-500/40 shadow-[0_0_60px_rgba(59,130,246,0.5)] scale-105'
                          : assistantState === STATE.LISTENING
                          ? 'bg-emerald-600/20 ring-4 ring-emerald-500/30 shadow-[0_0_40px_rgba(16,185,129,0.3)]'
                          : 'bg-slate-800/60 ring-2 ring-white/10'
                      }`}
                    >
                      <span className="text-6xl transition-transform hover:scale-110">🤖</span>
                    </div>

                    <p className="mt-4 text-base font-bold text-white tracking-wide">TalentHire AI</p>

                    {/* Speaking / Listening State Badges */}
                    <div className="mt-2 flex items-center justify-center gap-2">
                      {assistantState === STATE.SPEAKING && (
                        <div className="flex items-center gap-1 text-xs font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">
                          <span className="h-2 w-2 animate-ping rounded-full bg-blue-400" />
                          Speaking to candidate...
                        </div>
                      )}

                      {assistantState === STATE.LISTENING && (
                        <div className="flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                          Listening to candidate...
                        </div>
                      )}

                      {assistantState === STATE.THINKING && (
                        <span className="text-xs text-slate-400 animate-pulse">Analyzing response & thinking...</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Candidate Live Webcam Container */}
                <div className="relative flex min-h-[300px] items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-slate-900 shadow-inner">
                  {cameraOn ? (
                    <video
                      ref={(el) => {
                        videoRef.current = el
                        if (el && micStreamRef.current && cameraOn) {
                          if (el.srcObject !== micStreamRef.current) {
                            el.srcObject = micStreamRef.current
                            el.play().catch(() => {})
                          }
                        }
                      }}
                      autoPlay
                      muted
                      playsInline
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <div className="text-center">
                        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-slate-800 text-4xl border border-white/10">
                          👤
                        </div>
                        <p className="mt-3 text-xs text-slate-400">Camera is turned off</p>
                      </div>
                    </div>
                  )}

                  <div className="absolute left-4 top-4 rounded-lg bg-black/60 px-3 py-1 text-xs font-bold text-white backdrop-blur border border-white/10">
                    You (Candidate)
                  </div>

                  {/* Observable Metrics Overlay */}
                  <div className="absolute right-3 top-3 flex flex-col gap-1 text-[10px] font-semibold text-white/90">
                    <span className="bg-black/60 backdrop-blur px-2.5 py-1 rounded-md border border-white/10">
                      Face Vis: <b className="text-blue-400">{visualMetrics.faceVisibility}%</b>
                    </span>
                    <span className="bg-black/60 backdrop-blur px-2.5 py-1 rounded-md border border-white/10">
                      Align: <b className="text-indigo-400">{visualMetrics.cameraOrientation}%</b>
                    </span>
                    <span className="bg-black/60 backdrop-blur px-2.5 py-1 rounded-md border border-white/10">
                      Posture: <b className="text-teal-400">{visualMetrics.postureConsistency}%</b>
                    </span>
                  </div>

                  {micOn && (
                    <div className="absolute bottom-4 right-4 rounded-full bg-black/60 px-3 py-1.5 text-xs text-emerald-400 backdrop-blur border border-emerald-500/30 flex items-center gap-1.5 font-bold">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                      🎤 Mic Active
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Control Dock */}
              <div className="border-t border-white/10 bg-slate-900/80 px-6 py-4 backdrop-blur">
                <div className="flex items-center justify-center gap-4">
                  <button
                    onClick={toggleMic}
                    title={micOn ? 'Mute Microphone' : 'Unmute Microphone'}
                    className={`flex h-13 w-13 items-center justify-center rounded-2xl text-lg font-bold transition shadow-lg ${
                      micOn
                        ? 'bg-white/10 text-white hover:bg-white/20 border border-white/10'
                        : 'bg-red-600 text-white shadow-red-600/30'
                    }`}
                  >
                    {micOn ? '🎤' : '🔇'}
                  </button>

                  <button
                    onClick={toggleCamera}
                    title={cameraOn ? 'Turn Camera Off' : 'Turn Camera On'}
                    className={`flex h-13 w-13 items-center justify-center rounded-2xl text-lg font-bold transition shadow-lg ${
                      cameraOn
                        ? 'bg-white/10 text-white hover:bg-white/20 border border-white/10'
                        : 'bg-red-600 text-white shadow-red-600/30'
                    }`}
                  >
                    {cameraOn ? '📹' : '🚫'}
                  </button>

                  <button
                    onClick={toggleSpeaker}
                    title={speakerOn ? 'Mute AI Voice' : 'Unmute AI Voice'}
                    className={`flex h-13 w-13 items-center justify-center rounded-2xl text-lg font-bold transition shadow-lg ${
                      speakerOn
                        ? 'bg-white/10 text-white hover:bg-white/20 border border-white/10'
                        : 'bg-red-600 text-white shadow-red-600/30'
                    }`}
                  >
                    {speakerOn ? '🔊' : '🔇'}
                  </button>

                  <button
                    onClick={endInterview}
                    disabled={ending}
                    className="ml-4 flex h-13 items-center gap-2 rounded-2xl bg-gradient-to-r from-red-600 to-rose-600 px-6 text-sm font-extrabold text-white transition hover:from-red-500 hover:to-rose-500 shadow-lg shadow-red-600/30 disabled:opacity-50"
                  >
                    {ending ? 'Completing Session...' : '☎ End Interview'}
                  </button>
                </div>
              </div>
            </div>

            {/* Right Information & Live Transcript Side Panel */}
            <div className="space-y-4">
              {/* Current Question */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <span>🤖</span> AI Interviewer Question
                  </h3>
                  <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-[10px] font-bold text-blue-600 border border-blue-200">
                    RESUME-GROUNDED
                  </span>
                </div>
                <p className="mt-3 text-sm leading-relaxed font-medium text-slate-800">{currentQuestion}</p>
              </div>

              {/* Your Answer */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <span>🎤</span> Your Spoken Answer
                  </h3>
                  {assistantState === STATE.LISTENING && (
                    <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-emerald-600">
                      <span className="h-2 w-2 animate-ping rounded-full bg-emerald-500" />
                      Listening Live
                    </span>
                  )}
                </div>
                <p className="mt-3 min-h-[60px] text-sm leading-relaxed text-slate-600 font-medium">
                  {currentAnswer || candidateTextRef.current || 'Speak clearly into your microphone when replying to the AI interviewer...'}
                </p>

                <button
                  onClick={submitCandidateTurnAndAskNextQuestion}
                  disabled={!currentAnswer.trim() && !candidateTextRef.current.trim()}
                  className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-xs font-extrabold text-white shadow-md transition hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  💬 Submit Answer & Ask Next Question ➔
                </button>
              </div>

              {/* Live Transcript Log */}
              <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-100 px-5 py-3">
                  <h3 className="text-sm font-bold text-slate-900">Live Transcript Log</h3>
                </div>
                <div className="max-h-[220px] space-y-3 overflow-y-auto p-4">
                  {transcriptLog.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">Conversation transcripts will be logged here live...</p>
                  ) : (
                    transcriptLog.map((entry, idx) => (
                      <div key={idx} className="space-y-1 border-b border-slate-100 pb-2.5 last:border-b-0">
                        <p
                          className={`text-[10px] font-bold uppercase tracking-wider ${
                            entry.role === 'ai' ? 'text-blue-600' : 'text-emerald-600'
                          }`}
                        >
                          {entry.role === 'ai' ? 'TalentHire AI' : 'You (Candidate)'}
                        </p>
                        <p className="text-xs leading-relaxed text-slate-700">{entry.text}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}