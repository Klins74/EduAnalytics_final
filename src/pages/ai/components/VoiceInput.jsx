import React, { useState, useEffect, useRef } from 'react';
import Icon from '../../../components/AppIcon';

const VoiceInput = ({ onTranscript, isActive, setIsActive }) => {
  const [isSupported, setIsSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    // Check if speech recognition is supported
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setIsSupported(true);
      
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'ru-RU';
      
      recognitionRef.current.onstart = () => {
        setIsListening(true);
      };
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        setTranscript(finalTranscript || interimTranscript);
        
        if (finalTranscript) {
          onTranscript(finalTranscript);
          setTranscript('');
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setIsActive(false);
      };
      
      recognitionRef.current.onend = () => {
        setIsListening(false);
        setIsActive(false);
      };
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [onTranscript, setIsActive]);

  const toggleVoiceInput = () => {
    if (!isSupported) {
      alert('Голосовой ввод не поддерживается в вашем браузере');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      setIsActive(true);
      recognitionRef.current.start();
    }
  };

  if (!isSupported) {
    return null;
  }

  return (
    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
      <button
        type="button"
        onClick={toggleVoiceInput}
        className={`
          p-2 rounded-lg transition-all duration-200 hover-lift
          ${isListening 
            ? 'bg-error text-white animate-pulse' :'bg-background hover:bg-primary-50 text-text-secondary hover:text-primary'
          }
        `}
        title={isListening ? 'Остановить запись' : 'Начать голосовой ввод'}
      >
        <Icon 
          name={isListening ? "MicOff" : "Mic"} 
          size={16} 
        />
      </button>
      
      {/* Voice Input Indicator */}
      {isListening && (
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 bg-text-primary text-white px-3 py-1 rounded-lg text-xs whitespace-nowrap">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-error rounded-full animate-pulse" />
            <span>Слушаю...</span>
          </div>
          {transcript && (
            <div className="mt-1 text-xs opacity-80 max-w-xs truncate">
              {transcript}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VoiceInput;