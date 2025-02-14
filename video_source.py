import cv2
import os

class VideoSource:
    def __init__(self):
        self.cap = None
    
    def open_local_video(self, video_path):
        """Ouvre une vidéo locale comme source"""
        try:
            if not os.path.exists(video_path):
                raise Exception(f"Le fichier vidéo n'existe pas: {video_path}")
            
            # Libérer l'ancienne capture si elle existe
            if self.cap is not None:
                self.cap.release()
            
            # Ouvrir la vidéo avec OpenCV
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                raise Exception("Impossible d'ouvrir la vidéo")
            
            # Définir la taille de la vidéo
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            print("Vidéo locale ouverte avec succès")
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vidéo locale: {str(e)}")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            return False
    
    def open_camera(self, camera_id=0):
        """Ouvre la caméra comme source"""
        try:
            if self.cap is not None:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            return self.cap.isOpened()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la caméra: {str(e)}")
            return False
    
    def read(self):
        """Lit une frame de la source vidéo"""
        if self.cap is None:
            return False, None
        return self.cap.read()
    
    def release(self):
        """Libère les ressources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None