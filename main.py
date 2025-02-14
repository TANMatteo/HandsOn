import cv2
import tkinter as tk
from PIL import Image, ImageTk
from hand_detector import HandDetector
from sign_translator import SignTranslator
from text_to_speech import TextToSpeech
from gui import GUI
from video_source import VideoSource
from translations import Translator
import time
import threading

class Application:
    def __init__(self):
        self.translator = Translator()
        self.sign_translator = SignTranslator()
        self.video_source = VideoSource()
        # Initialiser la caméra au démarrage
        if not self.video_source.open_camera():
            print(self.translator.get_text('error_camera'))
        self.gui = None
        self.last_sign = None
        self.last_detection_time = 0
        self.detection_cooldown = 1.5
        
        # Donner une référence de l'application au traducteur
        self.sign_translator.app = self

    def process_frame(self, frame, hand_info):
        """Traite une frame de la vidéo"""
        current_time = time.time()
        
        if hand_info:
            # Si en mode apprentissage
            if self.sign_translator.is_learning:
                if self.sign_translator.add_learning_frame(hand_info):
                    self.gui.update_learning_status(True, len(self.sign_translator.gesture_frames))
                else:
                    self.gui.update_learning_status(True, len(self.sign_translator.gesture_frames))
            # Sinon, traduire le geste
            else:
                # Reconnaissance du geste
                sign = self.sign_translator.translate(hand_info)
                
                # Si un geste est reconnu et que le cooldown est passé
                if sign and sign != self.translator.get_text('gesture_not_recognized') and sign != self.translator.get_text('no_hand_detected'):
                    self.last_sign = sign
                    self.last_detection_time = current_time
                    
                    # Compter les versions du geste
                    count = 1
                    if sign in self.sign_translator.custom_gestures:
                        count += 1
                    
                    # Afficher les informations
                    info_text = (
                        f"{self.translator.get_text('recognized_gesture')} : {sign}\n"
                        f"- {self.translator.get_text('custom_version')} : {self.translator.get_text('yes') if sign in self.sign_translator.custom_gestures else self.translator.get_text('no')}\n"
                        f"- {self.translator.get_text('total_versions')} : {count}"
                    )
                    
                    self.gui.update_translation(info_text)
        else:
            if self.sign_translator.is_learning:
                self.gui.update_learning_status(True, len(self.sign_translator.gesture_frames))
        
        # Mise à jour de l'affichage
        self.gui.update_frame(frame)
    
    def start_learning(self, gesture_name):
        """Démarre l'apprentissage d'un nouveau geste"""
        if gesture_name:
            self.sign_translator.start_learning(gesture_name)
            self.gui.update_learning_status(True)
        else:
            self.sign_translator.stop_learning()
            self.gui.update_learning_status(False)
    
    def stop_learning(self):
        """Arrête l'apprentissage"""
        self.sign_translator.stop_learning()
        self.gui.update_learning_status(False)
    
    def remove_gestures(self):
        """Supprime tous les gestes personnalisés"""
        self.sign_translator.clear_custom_gestures()

def main():
    # Initialisation
    detector = HandDetector()
    translator = SignTranslator()
    tts = TextToSpeech()
    video_source = VideoSource()
    
    # Interface graphique
    root = tk.Tk()
    app = Application()
    gui = GUI(root, app)
    app.gui = gui
    
    # Connecter le traducteur à l'application
    translator.app = app
    app.sign_translator = translator
    
    # Variables
    last_sign = None
    last_sign_time = time.time()
    sign_cooldown = 1.0
    
    def change_video_source(source_type, url=None):
        """Change la source vidéo"""
        video_source.release()  # Libérer l'ancienne source
        
        if source_type == "camera":
            success = video_source.open_camera()
        elif source_type == "local":
            success = video_source.open_local_video(url)  # url contient le chemin du fichier
        
        if not success:
            print(f"Erreur lors du changement de source vidéo: {source_type}")
    
    def start_learning(gesture_name):
        """Commence ou termine l'apprentissage d'un geste"""
        if gesture_name is None:
            # Terminer l'apprentissage
            translator.stop_learning()
            gui.update_learning_status(False)
        else:
            # Commencer l'apprentissage
            translator.start_learning(gesture_name)
            gui.update_learning_status(True)
    
    def show_gesture_info(gesture_name):
        """Affiche les informations sur un geste spécifique"""
        count = translator.get_gesture_count(gesture_name.upper())
        info_text = f"Geste '{gesture_name.upper()}' :\n"
        info_text += f"- Geste prédéfini : {'Oui' if gesture_name.upper() in translator.gestures else 'Non'}\n"
        info_text += f"- Version personnalisée : {'Oui' if gesture_name.upper() in translator.custom_gestures else 'Non'}\n"
        info_text += f"- Nombre total de versions : {count}"
        
        gui.update_translation(info_text)
    
    def remove_all_gestures():
        """Supprime tous les gestes personnalisés"""
        translator.clear_all_custom_gestures()
        show_gesture_info('BONJOUR')  # Mettre à jour l'affichage
    
    # Définir les callbacks
    gui.set_video_source_callback(change_video_source)
    gui.set_learn_callback(start_learning)
    gui.set_remove_gesture_callback(remove_all_gestures)
    
    # Démarrer avec la caméra par défaut
    video_source.open_camera()
    
    def update_frame():
        """Met à jour l'image de la caméra"""
        ret, frame = video_source.read()
        if ret:
            # Miroir horizontal
            frame = cv2.flip(frame, 1)
            
            # Détecter les mains
            hands = detector.detect_hands(frame)
            if hands and len(hands) > 0:
                hand_info = hands[0]  # Prendre la première main détectée
                
                # Si en mode apprentissage
                if translator.is_learning:
                    if translator.add_learning_frame(hand_info):
                        gui.update_learning_status(True, len(translator.gesture_frames))
                    else:
                        gui.update_learning_status(True, len(translator.gesture_frames))
                # Sinon, traduire le geste
                else:
                    # Reconnaissance du geste
                    sign = translator.translate(hand_info)
                    
                    # Synthèse vocale si nouveau geste
                    nonlocal last_sign, last_sign_time
                    current_time = time.time()
                    
                    if sign != "Geste non reconnu" and sign != "En apprentissage..." and (
                        sign != last_sign or 
                        current_time - last_sign_time >= sign_cooldown
                    ):
                        last_sign = sign
                        last_sign_time = current_time
                        threading.Thread(target=tts.speak, args=(sign,), daemon=True).start()
                    
                    # Affichage des informations
                    hand_type = "Main droite" if hand_info.get('handedness') == "Right" else "Main gauche"
                    fingers = hand_info.get('fingers_up', {})
                    
                    # Liste des doigts levés
                    finger_names = {
                        'thumb': 'Pouce',
                        'index': 'Index',
                        'middle': 'Majeur',
                        'ring': 'Annulaire',
                        'pinky': 'Auriculaire'
                    }
                    
                    raised_fingers = [
                        finger_names[finger] 
                        for finger, info in fingers.items() 
                        if finger != 'total_up' and info.get('up', False)
                    ]
                    
                    info_text = (
                        f"Main détectée : {hand_type}\n"
                        f"Doigts levés : {', '.join(raised_fingers)}\n"
                        f"Geste reconnu : {sign}"
                    )
                    
                    gui.update_translation(info_text)
            else:
                if translator.is_learning:
                    gui.update_learning_status(True, len(translator.gesture_frames))
            
            # Mise à jour de l'affichage
            gui.update_frame(frame)
        
        # Planifier la prochaine mise à jour
        root.after(10, update_frame)
    
    # Démarrer la boucle de mise à jour
    update_frame()
    
    show_gesture_info('BONJOUR')
    
    # Démarrer la boucle principale
    root.mainloop()
    
    # Nettoyage
    video_source.release()

if __name__ == "__main__":
    main()