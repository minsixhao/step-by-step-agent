import { useState, useRef, useCallback, useEffect } from 'react';
import { useUIStore } from '../../store';

type VoiceState = 'idle' | 'connecting' | 'listening' | 'processing' | 'speaking';

export default function VoiceView() {
  const [state, setState] = useState<VoiceState>('idle');
  const [transcript, setTranscript] = useState('');
  const [responseText, setResponseText] = useState('');
  const [volume, setVolume] = useState(0);
  const [error, setError] = useState('');

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const isPressingRef = useRef(false);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const volIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { } = useUIStore();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  const disconnect = () => {
    if (wsRef.current) {
      try {
        wsRef.current.send(JSON.stringify({ type: 'FinishConnection', data: {} }));
        wsRef.current.close();
      } catch {}
      wsRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
    if (volIntervalRef.current) {
      clearInterval(volIntervalRef.current);
      volIntervalRef.current = null;
    }
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    isPressingRef.current = false;
    setState('idle');
  };

  const connectWebSocket = useCallback(async () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Already connected - send StartSession
      wsRef.current.send(JSON.stringify({ type: 'StartSession', data: {} }));
      return;
    }

    setState('connecting');
    setError('');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/voice/ws`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[Voice] WebSocket connected');
      ws.send(JSON.stringify({ type: 'StartSession', data: {} }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleServerMessage(msg);
      } catch (e) {
        console.error('[Voice] Failed to parse message:', e);
      }
    };

    ws.onerror = (e) => {
      console.error('[Voice] WebSocket error:', e);
      setError('连接失败');
      setState('idle');
    };

    ws.onclose = () => {
      console.log('[Voice] WebSocket closed');
      wsRef.current = null;
      if (state !== 'idle') setState('idle');
    };

    wsRef.current = ws;
  }, [state]);

  const handleServerMessage = (msg: any) => {
    switch (msg.type) {
      case 'SessionStarted':
        setState('idle');
        break;
      case 'ASRResponse':
        const text = msg.data?.results?.map((r: any) => r.text).join('') || '';
        if (text) setTranscript((prev) => prev + text);
        break;
      case 'ChatResponse':
        const content = msg.data?.content || '';
        if (content) setResponseText((prev) => prev + content);
        break;
      case 'TTSResponse':
        const audioData = msg.data;
        if (audioData) {
          playAudioBase64(audioData);
        }
        setState('speaking');
        break;
      case 'SessionFinished':
        setState('idle');
        break;
      case 'InterruptAck':
        // Clear audio queue
        audioQueueRef.current = [];
        isPlayingRef.current = false;
        setState('listening');
        break;
      case 'Error':
        setError(msg.data?.message || '发生错误');
        setState('idle');
        break;
    }
  };

  const playAudioBase64 = async (base64Data: string) => {
    if (!audioCtxRef.current || audioCtxRef.current.state === 'closed') {
      try {
        audioCtxRef.current = new AudioContext();
      } catch {
        return;
      }
    }

    try {
      const binaryStr = atob(base64Data);
      const bytes = new Uint8Array(binaryStr.length);
      for (let i = 0; i < binaryStr.length; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
      }
      const audioBuffer = await audioCtxRef.current.decodeAudioData(bytes.buffer);
      audioQueueRef.current.push(audioBuffer);
      playNextInQueue();
    } catch (e) {
      console.error('[Voice] Failed to decode audio:', e);
    }
  };

  const playNextInQueue = () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
    if (!audioCtxRef.current || audioCtxRef.current.state === 'closed') return;

    isPlayingRef.current = true;
    const buffer = audioQueueRef.current.shift()!;
    const source = audioCtxRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(audioCtxRef.current.destination);
    source.onended = () => {
      isPlayingRef.current = false;
      if (audioQueueRef.current.length > 0) {
        playNextInQueue();
      } else {
        setState('listening');
      }
    };
    source.start();
  };

  const startRecording = async () => {
    setError('');
    setTranscript('');
    setResponseText('');

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      await connectWebSocket();
      // Wait for connection
      await new Promise((resolve) => setTimeout(resolve, 500));
    }

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('无法连接到语音服务');
      setState('idle');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      mediaStreamRef.current = stream;

      const audioCtx = new AudioContext({ sampleRate: 16000 });
      audioCtxRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      source.connect(processor);
      processor.connect(audioCtx.destination);

      processor.onaudioprocess = (e) => {
        if (!isPressingRef.current) return;

        const inputData = e.inputBuffer.getChannelData(0);
        // Calculate volume
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += Math.abs(inputData[i]);
        }
        const avg = sum / inputData.length;
        setVolume(Math.min(avg * 5, 1));

        // Convert Float32 to Int16 PCM
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send binary audio data
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(int16Data.buffer);
        }
      };

      setState('listening');
      isPressingRef.current = true;
    } catch (e: any) {
      console.error('[Voice] Failed to start recording:', e);
      setError('无法访问麦克风：' + (e.message || '权限被拒绝'));
      setState('idle');
    }
  };

  const stopRecording = () => {
    isPressingRef.current = false;
    setVolume(0);

    // Send EndASR
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'EndASR', data: {} }));
    }

    setState('processing');

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }

    // Disconnect processor
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
  };

  const handleInterrupt = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ClientInterrupt', data: {} }));
    }
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    setState('idle');
    setTranscript('');
    setResponseText('');
  };

  const stateLabels: Record<VoiceState, string> = {
    idle: '按住下方按钮开始说话',
    connecting: '连接中…',
    listening: '聆听中…',
    processing: '处理中…',
    speaking: '说话中…',
  };

  const stateColors: Record<VoiceState, string> = {
    idle: 'text-gray-400',
    connecting: 'text-yellow-500',
    listening: 'text-green-500',
    processing: 'text-primary-500',
    speaking: 'text-blue-500',
  };

  return (
    <div className="h-full flex flex-col">
      {/* Status & subtitles */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
        <div className={`text-lg font-medium mb-4 ${stateColors[state]}`}>
          {stateLabels[state]}
        </div>

        {error && (
          <div className="text-red-500 text-sm mb-3 bg-red-50 px-4 py-2 rounded-lg">
            {error}
          </div>
        )}

        {/* Volume indicator */}
        {(state === 'listening') && (
          <div className="flex items-center gap-1 mb-4">
            {Array.from({ length: 10 }).map((_, i) => (
              <div
                key={i}
                className="w-1.5 rounded-full transition-all duration-100"
                style={{
                  height: `${8 + Math.random() * 32 * (volume > 0.1 ? volume : 0)}px`,
                  backgroundColor: i / 10 < volume ? '#8b5cf6' : '#e0d5ff',
                  opacity: volume > 0 ? 1 : 0.3,
                }}
              />
            ))}
          </div>
        )}

        {/* Transcript */}
        {(transcript || responseText) && (
          <div className="w-full max-w-md space-y-3">
            {transcript && (
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-sm text-left">
                <div className="text-xs text-gray-400 mb-1">你说：</div>
                <div className="text-gray-800">{transcript}</div>
              </div>
            )}
            {responseText && (
              <div className="bg-primary-50 rounded-xl p-4 shadow-sm border border-primary-100 text-sm text-left">
                <div className="text-xs text-primary-400 mb-1">AI：</div>
                <div className="text-gray-800">{responseText}</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom controls */}
      <div className="flex-shrink-0 flex flex-col items-center pb-8 pt-4">
        {/* Interrupt button (visible during speaking) */}
        {state === 'speaking' && (
          <button
            onClick={handleInterrupt}
            className="mb-4 px-5 py-2 rounded-full bg-red-100 text-red-600 text-sm font-medium hover:bg-red-200 transition-colors"
          >
            打断
          </button>
        )}

        {/* Main push-to-talk button */}
        <button
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onMouseLeave={() => {
            if (isPressingRef.current) stopRecording();
          }}
          onTouchStart={(e) => {
            e.preventDefault();
            startRecording();
          }}
          onTouchEnd={(e) => {
            e.preventDefault();
            stopRecording();
          }}
          className={`w-20 h-20 md:w-[100px] md:h-[100px] rounded-full flex items-center justify-center transition-all duration-200 select-none ${
            state === 'listening'
              ? 'bg-red-500 shadow-lg shadow-red-300 scale-110'
              : state === 'connecting' || state === 'processing'
              ? 'bg-yellow-400 shadow-lg shadow-yellow-200'
              : state === 'speaking'
              ? 'bg-blue-500 shadow-lg shadow-blue-300'
              : 'bg-primary-500 shadow-lg shadow-primary-300 hover:shadow-xl hover:scale-105'
          }`}
          disabled={state === 'connecting'}
        >
          <svg className="w-10 h-10 md:w-12 md:h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {state === 'listening' ? (
              // Show recording indicator
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            )}
          </svg>
        </button>

        <p className="text-xs text-gray-400 mt-4">
          {state === 'idle' ? '按住 说话' : '松手 结束'}
        </p>
      </div>
    </div>
  );
}
