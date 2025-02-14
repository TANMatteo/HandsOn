import pyttsx3
import threading
import queue
import sys

class TextToSpeech:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)    # Vitesse de parole
            self.engine.setProperty('volume', 0.9)  # Volume
            self.speech_queue = queue.Queue()
            self.speaking = False
            
            # Définir la voix en français si disponible
            voices = self.engine.getProperty('voices')
            french_voice_found = False
            for voice in voices:
                if 'french' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    french_voice_found = True
                    break
            
            if not french_voice_found:
                print("Attention: Aucune voix française n'a été trouvée. Utilisation de la voix par défaut.")
            
            # Démarrer le thread de synthèse vocale
            self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.speech_thread.start()
        except Exception as e:
            print(f"Erreur d'initialisation du moteur de synthèse vocale: {str(e)}")
            sys.exit(1)
    
    def _speech_worker(self):
        """Thread worker pour la synthèse vocale"""
        while True:
            try:
                text = self.speech_queue.get()
                if text and text != "Geste non reconnu":
                    self.speaking = True
                    try:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        print(f"Erreur lors de la synthèse vocale du texte '{text}': {str(e)}")
                    finally:
                        self.speaking = False
                self.speech_queue.task_done()
            except Exception as e:
                print(f"Erreur dans le thread de synthèse vocale: {str(e)}")
                self.speaking = False
                continue
    
    def speak(self, text):
        """Ajoute le texte à la file d'attente de synthèse vocale"""
        try:
            if not self.speaking and text:  # Vérifier que le texte n'est pas vide
                self.speech_queue.put(text)
        except Exception as e:
            print(f"Erreur lors de l'ajout du texte à la file d'attente: {str(e)}")