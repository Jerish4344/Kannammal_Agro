/**
 * Voice Price Input - Speech Recognition for Farmer Price Submission
 * Supports Web Speech API with fallback to file upload
 */

class VoicePriceInput {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.micButton = document.getElementById('micButton');
        this.priceInput = document.getElementById('id_price');
        this.statusElement = document.getElementById('micStatus');
        this.statusText = document.getElementById('statusText');
        this.transcriptElement = document.getElementById('voiceTranscript');
        this.transcriptText = document.getElementById('transcriptText');
        this.fileUploadSection = document.getElementById('fileUploadSection');
        
        this.init();
    }
    
    init() {
        if (!this.micButton || !this.priceInput) {
            console.warn('Voice input elements not found');
            return;
        }
        
        // Check for Speech Recognition support
        if (this.isSpeechRecognitionSupported()) {
            this.setupSpeechRecognition();
            this.micButton.addEventListener('click', () => this.toggleRecognition());
        } else {
            this.showFallbackUpload();
        }
        
        // Setup file upload fallback
        this.setupFileUpload();
    }
    
    isSpeechRecognitionSupported() {
        return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    }
    
    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.maxAlternatives = 1;
        
        // Set language based on current page language
        const htmlLang = document.documentElement.lang || 'en';
        this.recognition.lang = this.getRecognitionLanguage(htmlLang);
        
        // Event handlers
        this.recognition.onstart = () => this.onRecognitionStart();
        this.recognition.onresult = (event) => this.onRecognitionResult(event);
        this.recognition.onerror = (event) => this.onRecognitionError(event);
        this.recognition.onend = () => this.onRecognitionEnd();
    }
    
    getRecognitionLanguage(pageLanguage) {
        const languageMap = {
            'en': 'en-IN',
            'ta': 'ta-IN', 
            'hi': 'hi-IN'
        };
        return languageMap[pageLanguage] || 'en-IN';
    }
    
    toggleRecognition() {
        if (this.isListening) {
            this.stopRecognition();
        } else {
            this.startRecognition();
        }
    }
    
    startRecognition() {
        if (!this.recognition) return;
        
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Speech recognition error:', error);
            this.showError('Failed to start voice recognition');
        }
    }
    
    stopRecognition() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    onRecognitionStart() {
        this.isListening = true;
        this.micButton.classList.add('recording');
        this.micButton.classList.remove('disabled');
        this.showStatus('Listening... Speak the price now', 'listening');
    }
    
    onRecognitionResult(event) {
        const transcript = event.results[0][0].transcript;
        const confidence = event.results[0][0].confidence;
        
        console.log('Voice transcript:', transcript, 'Confidence:', confidence);
        
        // Show transcript
        this.showTranscript(transcript);
        
        // Extract numeric value from transcript
        const price = this.extractPriceFromTranscript(transcript);
        
        if (price > 0) {
            this.priceInput.value = price;
            this.priceInput.dispatchEvent(new Event('input', { bubbles: true }));
            this.showStatus(`Price set to ₹${price}`, 'success');
        } else {
            this.showStatus('Could not understand price. Please try again.', 'error');
        }
    }
    
    onRecognitionError(event) {
        console.error('Speech recognition error:', event.error);
        
        let errorMessage = 'Voice recognition failed';
        switch (event.error) {
            case 'network':
                errorMessage = 'Network error. Check your internet connection.';
                break;
            case 'not-allowed':
                errorMessage = 'Microphone access denied. Please allow microphone access.';
                break;
            case 'no-speech':
                errorMessage = 'No speech detected. Please try again.';
                break;
            case 'audio-capture':
                errorMessage = 'Microphone not available.';
                break;
        }
        
        this.showError(errorMessage);
    }
    
    onRecognitionEnd() {
        this.isListening = false;
        this.micButton.classList.remove('recording');
        
        if (!this.priceInput.value) {
            this.showStatus('Click microphone to try again', '');
        }
    }
    
    extractPriceFromTranscript(transcript) {
        // Remove common words and extract numbers
        const cleaned = transcript.toLowerCase()
            .replace(/rupees?|rs\.?|₹/gi, '')
            .replace(/only|paisa|paise/gi, '')
            .replace(/\band\b|\bpoint\b|\bdot\b/gi, '.')
            .trim();
        
        // Extract numeric patterns
        const numberPattern = /(\d+(?:\.\d+)?)/;
        const match = cleaned.match(numberPattern);
        
        if (match) {
            const price = parseFloat(match[1]);
            return isNaN(price) ? 0 : price;
        }
        
        // Try to convert word numbers (basic support)
        const wordNumbers = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'twenty': 20, 'thirty': 30, 'forty': 40,
            'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80,
            'ninety': 90, 'hundred': 100
        };
        
        for (const [word, num] of Object.entries(wordNumbers)) {
            if (cleaned.includes(word)) {
                return num;
            }
        }
        
        return 0;
    }
    
    showStatus(message, type = '') {
        this.statusElement.style.display = 'flex';
        this.statusText.textContent = message;
        this.statusElement.className = `mic-status ${type}`;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (this.statusElement.textContent === message) {
                this.statusElement.style.display = 'none';
            }
        }, 5000);
    }
    
    showError(message) {
        this.showStatus(message, 'error');
    }
    
    showTranscript(transcript) {
        this.transcriptText.textContent = transcript;
        this.transcriptElement.style.display = 'block';
        
        // Hide after 10 seconds
        setTimeout(() => {
            this.transcriptElement.style.display = 'none';
        }, 10000);
    }
    
    showFallbackUpload() {
        this.micButton.classList.add('disabled');
        this.micButton.title = 'Voice input not supported. Use file upload below.';
        this.fileUploadSection.style.display = 'block';
        this.showStatus('Voice input not supported on this browser', 'error');
    }
    
    setupFileUpload() {
        const audioFileInput = document.getElementById('audioFile');
        if (!audioFileInput) return;
        
        audioFileInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (!file) return;
            
            // Validate file type
            if (!file.type.startsWith('audio/')) {
                alert('Please select an audio file (WAV or MP3)');
                return;
            }
            
            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                alert('File size too large. Please select a file smaller than 5MB.');
                return;
            }
            
            this.uploadAudioFile(file);
        });
    }
    
    uploadAudioFile(file) {
        const formData = new FormData();
        formData.append('audio_file', file);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        this.showStatus('Processing audio file...', 'listening');
        
        fetch('/farmers/stt-upload/', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.text) {
                const price = this.extractPriceFromTranscript(data.text);
                if (price > 0) {
                    this.priceInput.value = price;
                    this.priceInput.dispatchEvent(new Event('input', { bubbles: true }));
                    this.showStatus(`Price set to ₹${price} from audio`, 'success');
                    this.showTranscript(data.text);
                } else {
                    this.showError('Could not extract price from audio');
                }
            } else {
                this.showError(data.error || 'Failed to process audio');
            }
        })
        .catch(error => {
            console.error('Audio upload error:', error);
            this.showError('Failed to upload audio file');
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('micButton')) {
        new VoicePriceInput();
    }
});
