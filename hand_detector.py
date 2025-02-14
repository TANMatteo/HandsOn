import mediapipe as mp
import cv2
import numpy as np

class HandDetector:
    def __init__(self):
        """Initialisation simple du détecteur de main"""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Configuration basique
        self.hands = self.mp_hands.Hands(
            max_num_hands=2,                # Deux mains
            min_detection_confidence=0.5,    # Seuil de détection
            min_tracking_confidence=0.5      # Seuil de suivi
        )
        
        # Points des doigts
        self.FINGER_TIPS = [4, 8, 12, 16, 20]  # Bout des doigts
        self.FINGER_BASES = [2, 5, 9, 13, 17]  # Base des doigts

    def detect_hands(self, frame):
        """Détection des deux mains"""
        # Conversion en RGB pour MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Détection
        results = self.hands.process(rgb_frame)
        
        # Si pas de main détectée
        if not results.multi_hand_landmarks:
            return None
            
        hands_info = []
        
        # Pour chaque main détectée
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Dessiner les points et connexions
            self._draw_hand(frame, hand_landmarks)
            
            # Compter les doigts levés
            fingers = self._count_fingers(hand_landmarks)
            
            # Information de la main
            hand_info = {
                'landmarks': [[landmark.x, landmark.y, landmark.z] for landmark in hand_landmarks.landmark],
                'handedness': handedness.classification[0].label,
                'confidence': handedness.classification[0].score,
                'fingers_up': fingers,
                'palm_pos': self._calculate_palm_center(hand_landmarks)  # Renommer en palm_pos
            }
            hands_info.append(hand_info)
        
        return hands_info
    
    def _draw_hand(self, frame, landmarks):
        """Dessine les points et connexions de la main avec plus d'informations"""
        h, w = frame.shape[:2]
        
        # Dessiner toutes les connexions
        self.mp_drawing.draw_landmarks(
            frame, 
            landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),  # Points verts
            self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)  # Lignes rouges
        )
        
        # Dessiner les bouts des doigts avec des couleurs différentes et des étiquettes
        finger_colors = {
            'thumb': (255, 0, 0),      # Rouge
            'index': (0, 255, 0),      # Vert
            'middle': (0, 0, 255),     # Bleu
            'ring': (255, 255, 0),     # Jaune
            'pinky': (255, 0, 255)     # Magenta
        }
        
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
        for tip, name in zip(self.FINGER_TIPS, finger_names):
            x = int(landmarks.landmark[tip].x * w)
            y = int(landmarks.landmark[tip].y * h)
            
            # Dessiner un cercle plus grand pour le bout du doigt
            cv2.circle(frame, (x, y), 8, finger_colors[name], -1)
            
            # Ajouter le nom du doigt
            cv2.putText(frame, name, (x-20, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, finger_colors[name], 2)
    
    def _count_fingers(self, landmarks):
        """Compte les doigts levés avec plus de détails"""
        fingers = {
            'thumb': {'up': False, 'angle': 0},
            'index': {'up': False, 'angle': 0},
            'middle': {'up': False, 'angle': 0},
            'ring': {'up': False, 'angle': 0},
            'pinky': {'up': False, 'angle': 0},
            'total_up': 0
        }
        
        # Vérifier chaque doigt
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
        
        for idx, (tip, base, name) in enumerate(zip(self.FINGER_TIPS, self.FINGER_BASES, finger_names)):
            # Position des points
            tip_y = landmarks.landmark[tip].y
            base_y = landmarks.landmark[base].y
            
            # Le pouce est un cas spécial
            if idx == 0:
                tip_x = landmarks.landmark[tip].x
                base_x = landmarks.landmark[base].x
                
                # Détecter si c'est une main gauche ou droite
                is_right_hand = landmarks.landmark[0].x < landmarks.landmark[5].x
                is_up = tip_x < base_x if is_right_hand else tip_x > base_x
                
                # Calculer l'angle pour le pouce
                dx = tip_x - base_x
                dy = tip_y - base_y
                angle = abs(np.degrees(np.arctan2(dy, dx)))
                fingers[name]['angle'] = angle
            else:
                # Pour les autres doigts, on compare la hauteur
                is_up = tip_y < base_y
                
                # Calculer l'angle pour les autres doigts
                dx = landmarks.landmark[tip].x - landmarks.landmark[base].x
                dy = landmarks.landmark[tip].y - landmarks.landmark[base].y
                angle = abs(np.degrees(np.arctan2(dy, dx)))
                fingers[name]['angle'] = angle
            
            fingers[name]['up'] = is_up
            if is_up:
                fingers['total_up'] += 1
        
        return fingers

    def _calculate_palm_center(self, landmarks):
        """Calcule le centre de la paume en utilisant les points de base des doigts"""
        # Points qui forment le centre de la paume (0 = poignet, 5,9,13,17 = base des doigts)
        palm_points = [0, 5, 9, 13, 17]
        
        # Calculer la moyenne des coordonnées
        x_mean = sum(landmarks.landmark[i].x for i in palm_points) / len(palm_points)
        y_mean = sum(landmarks.landmark[i].y for i in palm_points) / len(palm_points)
        z_mean = sum(landmarks.landmark[i].z for i in palm_points) / len(palm_points)
        
        return {'x': float(x_mean), 'y': float(y_mean), 'z': float(z_mean)}