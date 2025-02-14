import numpy as np
import json
import os
import time
import math

class SignTranslator:
    def __init__(self):
        self.gestures_file = "custom_gestures.json"
        self.custom_gestures = {}
        self.load_custom_gestures()
        
        # Dictionnaire des gestes prédéfinis (vide maintenant)
        self.gestures = {}
        
        # Variables pour l'apprentissage
        self.is_learning = False
        self.current_gesture = None
        self.gesture_frames = []
        self.frame_interval = 0.05
        self.last_frame_time = 0
        self.max_frames = 200
        self.min_frames = 5
        
        # Variables pour le suivi des mouvements (pour chaque main)
        self.movement_history_left = []
        self.movement_history_right = []
        self.max_history = 5
        self.movement_threshold = 0.15
        
        # Seuils pour la détection
        self.similarity_threshold = 0.45  # Réduit pour être plus permissif
        self.predefined_threshold = 0.55  # Réduit pour être plus permissif
        
        # Temps minimum entre les détections
        self.detection_cooldown = 0.4  # Réduit pour plus de réactivité
        self.last_detection_time = 0
        
        # Variables pour la confirmation du geste
        self.current_gesture_candidate = None
        self.gesture_start_time = 0
        self.gesture_confirmation_time = 0.25  # Réduit pour plus de réactivité
        
        # Nouveaux paramètres pour le filtrage du bruit
        self.noise_threshold = 0.02  # Augmenté légèrement pour être plus tolérant
        self.smoothing_window = 3  # Réduit pour moins de latence
        self.velocity_threshold = 0.12  # Augmenté pour permettre des mouvements plus rapides
        
        # Paramètres de normalisation améliorés
        self.position_scale = 1.2  # Augmenté pour amplifier les mouvements
        self.depth_weight = 0.5  # Réduit pour être moins sensible à la profondeur
        
        # Variables pour l'apprentissage
        self.is_learning = False
        self.current_gesture = None
        self.gesture_frames = []
        self.frame_interval = 0.05
        self.last_frame_time = 0
        self.max_frames = 200
        self.min_frames = 5
        
        # Variables pour le suivi des mouvements (pour chaque main)
        self.movement_history_left = []
        self.movement_history_right = []
        self.max_history = 5
        self.movement_threshold = 0.15
        
        # Seuils pour la détection
        self.similarity_threshold = 0.45
        self.predefined_threshold = 0.55
        self.detection_cooldown = 0.4
        self.last_detection_time = 0

    def load_custom_gestures(self):
        """Charge les gestes personnalisés depuis le fichier"""
        if os.path.exists(self.gestures_file):
            try:
                with open(self.gestures_file, 'r') as f:
                    data = json.load(f)
                    # Convertir les données au bon format
                    self.custom_gestures = {}
                    for gesture_name, gesture_data in data.items():
                        if 'sequence' in gesture_data:
                            sequence = []
                            for frame in gesture_data['sequence']:
                                converted_frame = self._convert_frame_data(frame)
                                if converted_frame:
                                    sequence.append(converted_frame)
                            if sequence:
                                self.custom_gestures[gesture_name] = {
                                    'sequence': sequence,
                                    'timestamp': gesture_data.get('timestamp', time.time())
                                }
            except Exception as e:
                print(f"Erreur lors du chargement des gestes: {str(e)}")
                self.custom_gestures = {}

    def _convert_frame_data(self, frame):
        """Convertit les données d'une frame au bon format"""
        try:
            if not frame:
                return None
                
            # Convertir palm_pos
            palm_pos = frame.get('palm_pos', {})
            if isinstance(palm_pos, dict):
                # Déjà au bon format, juste s'assurer que les valeurs sont des float
                palm_pos = {
                    'x': float(palm_pos.get('x', 0)),
                    'y': float(palm_pos.get('y', 0)),
                    'z': float(palm_pos.get('z', 0))
                }
            elif isinstance(palm_pos, (list, tuple)) and len(palm_pos) >= 3:
                # Convertir la liste en dictionnaire
                palm_pos = {
                    'x': float(palm_pos[0]),
                    'y': float(palm_pos[1]),
                    'z': float(palm_pos[2])
                }
            else:
                palm_pos = {'x': 0.0, 'y': 0.0, 'z': 0.0}
            
            # Convertir landmarks
            landmarks = []
            for point in frame.get('landmarks', []):
                if isinstance(point, dict):
                    landmarks.append([
                        float(point.get('x', 0)),
                        float(point.get('y', 0)),
                        float(point.get('z', 0))
                    ])
                elif isinstance(point, (list, tuple)) and len(point) >= 3:
                    landmarks.append([float(x) for x in point[:3]])
            
            return {
                'fingers': frame.get('fingers', {}),
                'palm_pos': palm_pos,  # Maintenant toujours un dictionnaire
                'landmarks': landmarks,
                'handedness': frame.get('handedness', 'Unknown'),
                'time': frame.get('time', 0.0)
            }
        except Exception as e:
            print(f"Erreur lors de la conversion des données: {str(e)}")
            return None

    def save_custom_gestures(self):
        """Sauvegarde les gestes personnalisés dans le fichier"""
        with open(self.gestures_file, 'w') as f:
            json.dump(self.custom_gestures, f)

    def start_learning(self, gesture_name):
        """Commence l'apprentissage d'un nouveau geste"""
        self.is_learning = True
        self.current_gesture = gesture_name.upper()
        self.gesture_frames = []
        self.last_frame_time = 0
        print(f"\n=== Début de l'enregistrement du geste '{gesture_name}' ===")
        print("Faites votre geste maintenant...")

    def stop_learning(self):
        """Arrête l'apprentissage et sauvegarde le geste"""
        if self.is_learning and self.current_gesture:
            print(f"\n=== Fin de l'enregistrement du geste '{self.current_gesture}' ===")
            
            if len(self.gesture_frames) < self.min_frames:
                print(f"ERREUR: Pas assez de frames capturées ({len(self.gesture_frames)} < {self.min_frames})")
                print("Veuillez refaire le geste plus lentement.")
            else:
                # Nettoyer la séquence pour garder les mouvements significatifs
                cleaned_frames = self._clean_sequence(self.gesture_frames)
                
                self.custom_gestures[self.current_gesture] = {
                    'sequence': cleaned_frames,
                    'timestamp': time.time()
                }
                self.save_custom_gestures()
                print(f"Geste enregistré avec succès !")
                print(f"- Nombre de frames capturées : {len(cleaned_frames)}")
                print(f"- Durée totale : {sum(f.get('time', 0) for f in cleaned_frames):.1f} secondes")
        
        self.is_learning = False
        self.current_gesture = None
        self.gesture_frames = []
        self.last_frame_time = 0

    def add_learning_frame(self, hand_info):
        """Ajoute une frame à la séquence d'apprentissage"""
        try:
            if not self.is_learning:
                return False
                
            # Vérifier le temps écoulé depuis la dernière frame
            current_time = time.time()
            if current_time - self.last_frame_time < self.frame_interval:
                return False
                
            # Extraire les caractéristiques
            features = self._extract_gesture_features(hand_info)
            if not features:
                return False
                
            # Vérifier si la position est nouvelle
            if len(self.gesture_frames) == 0 or self._is_new_position(features):
                # S'assurer que palm_pos contient des valeurs numériques
                if 'palm_pos' in features:
                    palm_pos = features['palm_pos']
                    features['palm_pos'] = {
                        'x': float(palm_pos.get('x', 0)),
                        'y': float(palm_pos.get('y', 0)),
                        'z': float(palm_pos.get('z', 0))
                    }
                
                self.gesture_frames.append(features)
                self.last_frame_time = current_time
                
                # Vérifier si on a atteint le nombre maximum de frames
                if len(self.gesture_frames) >= self.max_frames:
                    self.stop_learning()
                    
                return True
                
            return False
            
        except Exception as e:
            print(f"Erreur lors de l'ajout d'une frame: {str(e)}")
            return False

    def _is_new_position(self, new_features):
        """Vérifie si la position est suffisamment différente de la dernière position"""
        if not self.gesture_frames:
            return True
            
        last_features = self.gesture_frames[-1]
        
        try:
            # Extraire les coordonnées des positions
            new_pos = new_features.get('palm_pos', {})
            last_pos = last_features.get('palm_pos', {})
            
            # Convertir les coordonnées en array numpy
            new_coords = np.array([
                float(new_pos.get('x', 0)),
                float(new_pos.get('y', 0)),
                float(new_pos.get('z', 0))
            ])
            last_coords = np.array([
                float(last_pos.get('x', 0)),
                float(last_pos.get('y', 0)),
                float(last_pos.get('z', 0))
            ])
            
            # Calculer la différence de position
            position_diff = np.linalg.norm(new_coords - last_coords)
            
            # Comparer la configuration des doigts
            new_fingers = new_features.get('fingers', {})
            last_fingers = last_features.get('fingers', {})
            finger_diff = 0
            
            for f in ['thumb', 'index', 'middle', 'ring', 'pinky']:
                if f in new_fingers and f in last_fingers:
                    new_up = new_fingers[f].get('up', False)
                    last_up = last_fingers[f].get('up', False)
                    if new_up != last_up:
                        finger_diff += 1
            
            # La position est nouvelle si :
            # - La main a bougé suffisamment (> 5% de la taille de l'image)
            # - OU la configuration des doigts a changé
            return position_diff > 0.05 or finger_diff > 0
            
        except Exception as e:
            print(f"Erreur lors de la comparaison des positions: {str(e)}")
            return True

    def _clean_sequence(self, sequence):
        """Nettoie une séquence de frames en normalisant les positions et en filtrant le bruit"""
        try:
            if not sequence:
                return []
            
            # Obtenir la position de référence (première frame)
            ref_frame = sequence[0]
            if not isinstance(ref_frame, dict) or 'palm_pos' not in ref_frame:
                return sequence
            
            ref_pos = ref_frame['palm_pos']
            if not isinstance(ref_pos, dict):
                return sequence
            
            # Créer un vecteur de référence
            ref_vector = {
                'x': ref_pos['x'],
                'y': ref_pos['y'],
                'z': ref_pos['z']
            }
            
            # Normaliser et filtrer chaque frame
            cleaned = []
            last_velocity = {'x': 0, 'y': 0, 'z': 0}
            
            for i, frame in enumerate(sequence):
                if not isinstance(frame, dict) or 'palm_pos' not in frame:
                    continue
                    
                new_frame = frame.copy()
                palm_pos = frame['palm_pos']
                
                if not isinstance(palm_pos, dict):
                    continue
                
                # Calculer la position relative avec échelle et poids de profondeur
                rel_pos = {
                    'x': (palm_pos['x'] - ref_vector['x']) * self.position_scale,
                    'y': (palm_pos['y'] - ref_vector['y']) * self.position_scale,
                    'z': (palm_pos['z'] - ref_vector['z']) * self.position_scale * self.depth_weight
                }
                
                # Calculer la vitesse instantanée
                if i > 0:
                    prev_pos = cleaned[-1]['palm_pos']
                    dt = frame.get('time', 0) - cleaned[-1].get('time', 0)
                    if dt > 0:
                        velocity = {
                            'x': (rel_pos['x'] - prev_pos['x']) / dt,
                            'y': (rel_pos['y'] - prev_pos['y']) / dt,
                            'z': (rel_pos['z'] - prev_pos['z']) / dt
                        }
                        
                        # Filtrer les mouvements brusques
                        velocity_magnitude = math.sqrt(
                            velocity['x']**2 + velocity['y']**2 + velocity['z']**2
                        )
                        
                        if velocity_magnitude > self.velocity_threshold:
                            # Limiter la vitesse
                            scale = self.velocity_threshold / velocity_magnitude
                            velocity = {k: v * scale for k, v in velocity.items()}
                            
                        # Mettre à jour la position en fonction de la vitesse limitée
                        rel_pos = {
                            'x': prev_pos['x'] + velocity['x'] * dt,
                            'y': prev_pos['y'] + velocity['y'] * dt,
                            'z': prev_pos['z'] + velocity['z'] * dt
                        }
                        
                        last_velocity = velocity
                
                # Filtrer le bruit avec un seuil adaptatif
                if i > 0:
                    movement = math.sqrt(
                        (rel_pos['x'] - prev_pos['x'])**2 +
                        (rel_pos['y'] - prev_pos['y'])**2 +
                        (rel_pos['z'] - prev_pos['z'])**2
                    )
                    
                    # Ajuster le seuil de bruit en fonction de la vitesse
                    adaptive_threshold = self.noise_threshold * (1 + math.sqrt(
                        last_velocity['x']**2 + 
                        last_velocity['y']**2 + 
                        last_velocity['z']**2
                    ))
                    
                    if movement < adaptive_threshold:
                        continue
                
                new_frame['palm_pos'] = rel_pos
                cleaned.append(new_frame)
            
            # Appliquer un lissage Gaussien sur les positions
            if len(cleaned) >= self.smoothing_window:
                smoothed = []
                gaussian_kernel = self._create_gaussian_kernel(self.smoothing_window)
                
                for i in range(len(cleaned)):
                    start_idx = max(0, i - self.smoothing_window // 2)
                    end_idx = min(len(cleaned), i + self.smoothing_window // 2 + 1)
                    window = cleaned[start_idx:end_idx]
                    kernel = gaussian_kernel[:(end_idx - start_idx)]
                    kernel = [k / sum(kernel) for k in kernel]  # Normaliser le noyau
                    
                    avg_pos = {
                        'x': sum(f['palm_pos']['x'] * k for f, k in zip(window, kernel)),
                        'y': sum(f['palm_pos']['y'] * k for f, k in zip(window, kernel)),
                        'z': sum(f['palm_pos']['z'] * k for f, k in zip(window, kernel))
                    }
                    
                    smoothed_frame = cleaned[i].copy()
                    smoothed_frame['palm_pos'] = avg_pos
                    smoothed.append(smoothed_frame)
                
                return smoothed
            
            return cleaned
            
        except Exception as e:
            print(f"Erreur lors du nettoyage de la séquence: {str(e)}")
            return sequence

    def _create_gaussian_kernel(self, size):
        """Crée un noyau gaussien pour le lissage"""
        sigma = size / 6.0  # Couvre 99.7% de la distribution
        kernel = [math.exp(-(x - (size-1)/2)**2 / (2*sigma**2)) for x in range(size)]
        return kernel

    def _extract_gesture_features(self, hands_info):
        """Extrait les caractéristiques des mains pour la comparaison"""
        try:
            if not hands_info:
                return None
            
            # Si on reçoit une seule main au lieu d'une liste
            if isinstance(hands_info, dict):
                hand = hands_info
            else:
                hand = hands_info[0]  # Prendre la première main
            
            # Extraire les caractéristiques
            features = {
                'landmarks': hand['landmarks'],
                'fingers': hand['fingers_up'],
                'palm_pos': hand['palm_pos'],
                'handedness': hand['handedness']
            }
            
            return features
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des caractéristiques: {str(e)}")
            return None

    def update_movement_history(self, hands_info):
        """Met à jour l'historique des mouvements pour les deux mains"""
        if not hands_info:
            return
            
        for hand_info in hands_info:
            palm_center = hand_info.get('palm_pos', None)
            handedness = hand_info.get('handedness', None)
            
            # Vérifier que palm_center est un dictionnaire avec les bonnes clés
            if palm_center and handedness and isinstance(palm_center, dict):
                if all(k in palm_center for k in ['x', 'y', 'z']):
                    if handedness == 'Left':
                        self.movement_history_left.append(palm_center)
                        if len(self.movement_history_left) > self.max_history:
                            self.movement_history_left.pop(0)
                    else:  # Right
                        self.movement_history_right.append(palm_center)
                        if len(self.movement_history_right) > self.max_history:
                            self.movement_history_right.pop(0)

    def translate(self, hands_info):
        """Traduit les informations des mains en geste"""
        try:
            if not hands_info:
                self.current_gesture_candidate = None
                return "Aucune main détectée"
            
            if not isinstance(hands_info, list):
                if isinstance(hands_info, dict):
                    hands_info = [hands_info]
                else:
                    return "Format de données invalide"
            
            if self.is_learning:
                return "En apprentissage..."
            
            current_time = time.time()
            if current_time - self.last_detection_time < self.detection_cooldown:
                return None
            
            # Mettre à jour l'historique des mouvements
            self.update_movement_history(hands_info)
            
            # Vérifier les gestes personnalisés d'abord
            detected_gestures = []
            for gesture_name, gesture_data in self.custom_gestures.items():
                try:
                    if 'sequence' in gesture_data:
                        score = self._compare_with_sequence(hands_info, gesture_data['sequence'])
                        if score >= self.similarity_threshold:
                            detected_gestures.append((gesture_name, score))
                except Exception as e:
                    print(f"Erreur lors de la détection du geste personnalisé {gesture_name}: {str(e)}")
            
            # Vérifier les gestes prédéfinis
            for gesture_name, detect_func in self.gestures.items():
                try:
                    score = self._calculate_predefined_score(hands_info, detect_func)
                    if score >= self.predefined_threshold:
                        detected_gestures.append((gesture_name, score))
                except Exception as e:
                    print(f"Erreur lors de la détection de {gesture_name}: {str(e)}")
            
            if not detected_gestures:
                self.current_gesture_candidate = None
                return None
            
            # Filtrer et trier les gestes par score
            detected_gestures = [(name, score) for name, score in detected_gestures if score >= self.similarity_threshold]
            if not detected_gestures:
                self.current_gesture_candidate = None
                return None
                
            detected_gestures.sort(key=lambda x: x[1], reverse=True)
            best_gesture, best_score = detected_gestures[0]
            
            # Système de confirmation du geste
            if best_gesture != self.current_gesture_candidate:
                # Nouveau geste détecté, commencer le minuteur
                self.current_gesture_candidate = best_gesture
                self.gesture_start_time = current_time
                return None
            elif current_time - self.gesture_start_time >= self.gesture_confirmation_time:
                # Geste maintenu assez longtemps, le valider
                self.last_detection_time = current_time
                subtitle_text = best_gesture
                
                # Mettre à jour les sous-titres via l'application
                if hasattr(self, 'app') and hasattr(self.app, 'gui'):
                    print(f"Envoi du sous-titre : {subtitle_text}")
                    self.app.gui.update_subtitle(subtitle_text)
                else:
                    print("Erreur: Impossible d'accéder à l'interface graphique pour les sous-titres")
                
                print(f"Signe LSF détecté : {best_gesture}")
                return best_gesture
            
            # Geste en cours de confirmation
            return None
            
        except Exception as e:
            print(f"Erreur lors de la traduction: {str(e)}")
            return None

    def _calculate_predefined_score(self, hands_info, detect_func):
        """Calcule un score pour un geste prédéfini avec une meilleure pondération"""
        try:
            # Vérifier si le geste est détecté
            if not detect_func(hands_info):
                return 0.0
            
            score = 0.0
            
            # 1. Position des doigts (50% - augmenté car très important)
            fingers = hands_info[0].get('fingers_up', {})
            correct_fingers = 0
            total_fingers = 0
            for f in ['thumb', 'index', 'middle', 'ring', 'pinky']:
                if f in fingers:
                    total_fingers += 1
                    if fingers[f].get('up', False):
                        correct_fingers += 1
            
            finger_score = correct_fingers / max(1, total_fingers)
            score += 0.5 * finger_score
            
            # 2. Amplitude du mouvement (30%)
            movement_score = 0.0
            if len(self.movement_history_left) >= 2 or len(self.movement_history_right) >= 2:
                history = self.movement_history_left if len(self.movement_history_left) >= 2 else self.movement_history_right
                
                # Calculer la trajectoire complète
                total_movement = 0
                for i in range(1, len(history)):
                    prev_pos = history[i-1]
                    curr_pos = history[i]
                    movement = math.sqrt(
                        (curr_pos['x'] - prev_pos['x'])**2 +
                        (curr_pos['y'] - prev_pos['y'])**2 +
                        (curr_pos['z'] - prev_pos['z'])**2
                    )
                    total_movement += movement
                
                movement_score = min(1.0, total_movement / (self.movement_threshold * len(history)))
            score += 0.3 * movement_score
            
            # 3. Stabilité de la main (20% - réduit car moins critique)
            stability_score = 0.0
            if len(self.movement_history_left) >= 3 or len(self.movement_history_right) >= 3:
                history = self.movement_history_left if len(self.movement_history_left) >= 3 else self.movement_history_right
                
                # Calculer la variance des positions
                positions = np.array([[p['x'], p['y'], p['z']] for p in history])
                variance = np.var(positions, axis=0)
                avg_variance = np.mean(variance)
                
                stability_score = 1.0 - min(1.0, avg_variance / 0.1)
            score += 0.2 * stability_score
            
            return score
            
        except Exception as e:
            print(f"Erreur lors du calcul du score prédéfini: {str(e)}")
            return 0.0

    def get_available_gestures(self):
        """Retourne la liste des gestes disponibles"""
        return list(self.gestures.keys())

    def list_gestures(self):
        """Liste tous les gestes disponibles avec leur nombre d'occurrences"""
        gestures_count = {}
        
        # Compter les gestes prédéfinis
        for gesture_name in self.gestures.keys():
            gestures_count[gesture_name] = 1  # Chaque geste prédéfini compte pour 1
        
        # Compter les gestes personnalisés
        for gesture_name in self.custom_gestures.keys():
            if gesture_name in gestures_count:
                gestures_count[gesture_name] += 1
            else:
                gestures_count[gesture_name] = 1
        
        return gestures_count

    def get_gesture_count(self, gesture_name):
        """Retourne le nombre d'occurrences d'un geste spécifique"""
        count = 0
        
        # Vérifier dans les gestes prédéfinis
        if gesture_name in self.gestures:
            count += 1
        
        # Vérifier dans les gestes personnalisés
        if gesture_name in self.custom_gestures:
            count += 1
        
        return count

    def _get_finger_distance(self, landmarks, finger1_tip, finger2_tip):
        """Calcule la distance entre deux points de doigts"""
        p1 = landmarks.landmark[finger1_tip]
        p2 = landmarks.landmark[finger2_tip]
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

    def remove_custom_gesture(self, gesture_name):
        """Supprime un geste personnalisé"""
        gesture_name = gesture_name.upper()
        if gesture_name in self.custom_gestures:
            del self.custom_gestures[gesture_name]
            self.save_custom_gestures()
            return True
        return False

    def clear_all_custom_gestures(self):
        """Supprime tous les gestes personnalisés"""
        self.custom_gestures = {}
        self.save_custom_gestures()

    def delete_gesture(self, gesture_name):
        """Supprime un geste spécifique"""
        if gesture_name in self.custom_gestures:
            del self.custom_gestures[gesture_name]
            self.save_custom_gestures()
            print(f"Geste '{gesture_name}' supprimé avec succès!")
            return True
        else:
            print(f"Geste '{gesture_name}' non trouvé.")
            return False

    def get_custom_gestures(self):
        """Retourne la liste des gestes personnalisés"""
        return list(self.custom_gestures.keys())

    def _compare_with_sequence(self, hands_info, sequence):
        """Compare les caractéristiques actuelles avec une séquence de référence"""
        try:
            # Extraire les caractéristiques des mains
            current_features = self._extract_gesture_features(hands_info)
            if not current_features:
                return 0
            
            # Comparer avec chaque frame de la séquence et trouver la meilleure correspondance
            best_score = 0
            for reference_frame in sequence:
                frame_scores = []
                
                # 1. Comparer les positions des doigts (40% du score)
                if 'fingers' in reference_frame and 'fingers' in current_features:
                    finger_score = self._compare_fingers(current_features['fingers'], reference_frame['fingers'])
                    frame_scores.append((finger_score, 0.4))
                
                # 2. Comparer les positions des paumes (30% du score)
                if 'palm_pos' in reference_frame and 'palm_pos' in current_features:
                    palm_score = self._compare_palm_positions(current_features['palm_pos'], reference_frame['palm_pos'])
                    frame_scores.append((palm_score, 0.3))
                
                # 3. Comparer les landmarks (30% du score)
                if 'landmarks' in reference_frame and 'landmarks' in current_features:
                    landmark_score = self._compare_landmarks(current_features['landmarks'], reference_frame['landmarks'])
                    frame_scores.append((landmark_score, 0.3))
                
                # Vérifier la main utilisée (facteur multiplicatif)
                hand_multiplier = 1.0
                if 'handedness' in reference_frame and 'handedness' in current_features:
                    if current_features['handedness'] != reference_frame['handedness']:
                        hand_multiplier = 0.5  # Pénalité si mauvaise main
                
                # Calculer le score pondéré pour cette frame
                if frame_scores:
                    weighted_score = sum(score * weight for score, weight in frame_scores)
                    weighted_score *= hand_multiplier
                    best_score = max(best_score, weighted_score)
            
            return best_score
            
        except Exception as e:
            print(f"Erreur lors de la comparaison des caractéristiques: {str(e)}")
            return 0

    def _compare_fingers(self, current_fingers, reference_fingers):
        """Compare l'état des doigts"""
        try:
            if not current_fingers or not reference_fingers:
                return 0
                
            # Compter les correspondances
            matches = 0
            total = 0
            
            for finger in ['thumb', 'index', 'middle', 'ring', 'pinky']:
                if finger in current_fingers and finger in reference_fingers:
                    current_up = current_fingers[finger].get('up', False)
                    reference_up = reference_fingers[finger].get('up', False)
                    if current_up == reference_up:
                        matches += 1
                    total += 1
            
            return matches / total if total > 0 else 0
            
        except Exception as e:
            print(f"Erreur lors de la comparaison des doigts: {str(e)}")
            return 0

    def _compare_palm_positions(self, current_palm, reference_palm):
        """Compare les positions des paumes"""
        try:
            if not isinstance(current_palm, dict) or not isinstance(reference_palm, dict):
                return 0
                
            # Vérifier que les clés nécessaires sont présentes
            required_keys = ['x', 'y', 'z']
            if not all(k in current_palm for k in required_keys) or not all(k in reference_palm for k in required_keys):
                return 0
                
            # Extraire les valeurs numériques des dictionnaires
            x1, y1, z1 = float(current_palm['x']), float(current_palm['y']), float(current_palm['z'])
            x2, y2, z2 = float(reference_palm['x']), float(reference_palm['y']), float(reference_palm['z'])
            
            # Calculer la distance euclidienne
            distance = math.sqrt(
                (x1 - x2)**2 +
                (y1 - y2)**2 +
                (z1 - z2)**2
            )
            
            # Convertir la distance en score
            max_distance = 0.5
            return max(0, 1 - distance/max_distance)
            
        except Exception as e:
            print(f"Erreur lors de la comparaison des positions: {str(e)}")
            return 0

    def _compare_landmarks(self, current_landmarks, reference_landmarks):
        """Compare les positions des points de repère"""
        try:
            if not current_landmarks or not reference_landmarks:
                return 0
                
            # Prendre le minimum de points disponibles
            n_points = min(len(current_landmarks), len(reference_landmarks))
            if n_points == 0:
                return 0
                
            # Calculer la distance moyenne normalisée
            total_distance = 0
            for i in range(n_points):
                current_point = np.array(current_landmarks[i])
                reference_point = np.array(reference_landmarks[i])
                distance = np.linalg.norm(current_point - reference_point)
                total_distance += distance
            
            avg_distance = total_distance / n_points
            score = max(0, 1 - avg_distance)
            return score
            
        except Exception as e:
            print(f"Erreur lors de la comparaison des landmarks: {str(e)}")
            return 0

    def _detect_hello(self, hands_info):
        """Bonjour en LSF : Main droite qui fait un mouvement de droite à gauche"""
        try:
            if not hands_info or not isinstance(hands_info, list):
                return False
            
            # Trouver la main droite
            right_hand = None
            for hand in hands_info:
                if isinstance(hand, dict) and hand.get('handedness') == 'Right':
                    right_hand = hand
                    break
            
            if not right_hand:
                return False
            
            # Vérifier la position des doigts (tous les doigts doivent être levés)
            fingers = right_hand.get('fingers_up', {})
            if not isinstance(fingers, dict):
                return False
                
            if not all(fingers.get(f, {}).get('up', False) for f in ['thumb', 'index', 'middle', 'ring', 'pinky']):
                return False
            
            # Vérifier le mouvement horizontal
            if len(self.movement_history_right) < 2:
                return False
                
            start_pos = np.array(self.movement_history_right[0])
            end_pos = np.array(self.movement_history_right[-1])
            movement = end_pos - start_pos
            
            horizontal_movement = abs(movement[0])
            vertical_movement = abs(movement[1])
            
            # Le mouvement horizontal doit être plus important que le vertical
            return horizontal_movement > vertical_movement
            
        except Exception as e:
            print(f"Erreur dans _detect_hello: {str(e)}")
            return False

    def _detect_thank_you(self, hands_info):
        """Merci en LSF : Main droite qui descend depuis la bouche"""
        try:
            if not hands_info or not isinstance(hands_info, list):
                return False
            
            # Trouver la main droite
            right_hand = None
            for hand in hands_info:
                if isinstance(hand, dict) and hand.get('handedness') == 'Right':
                    right_hand = hand
                    break
            
            if not right_hand:
                return False
            
            # Vérifier la position des doigts (main plate)
            fingers = right_hand.get('fingers_up', {})
            if not isinstance(fingers, dict):
                return False
                
            total_up = sum(1 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']
                          if fingers.get(f, {}).get('up', False))
            if total_up < 3:  # Au moins 3 doigts levés
                return False
            
            # Vérifier le mouvement vertical
            if len(self.movement_history_right) < 2:
                return False
                
            start_pos = np.array(self.movement_history_right[0])
            end_pos = np.array(self.movement_history_right[-1])
            movement = end_pos - start_pos
            
            vertical_movement = abs(movement[1])
            horizontal_movement = abs(movement[0])
            
            # Le mouvement vertical doit être plus important que l'horizontal
            # et doit aller vers le bas (y augmente vers le bas)
            return vertical_movement > horizontal_movement and movement[1] > 0
            
        except Exception as e:
            print(f"Erreur dans _detect_thank_you: {str(e)}")
            return False

    def _detect_yes(self, hands_info):
        """Oui en LSF : Poing fermé avec mouvement de haut en bas"""
        try:
            if not hands_info or not isinstance(hands_info, list):
                return False
            
            # Prendre la première main disponible
            hand = hands_info[0]
            if not isinstance(hand, dict):
                return False
            
            # Vérifier la position des doigts (poing fermé)
            fingers = hand.get('fingers_up', {})
            if not isinstance(fingers, dict):
                return False
                
            total_up = sum(1 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']
                          if fingers.get(f, {}).get('up', False))
            if total_up > 1:  # Maximum 1 doigt levé
                return False
            
            # Vérifier le mouvement vertical
            history = self.movement_history_right if hand.get('handedness') == 'Right' else self.movement_history_left
            if len(history) < 2:
                return False
                
            start_pos = np.array(history[0])
            end_pos = np.array(history[-1])
            movement = end_pos - start_pos
            
            vertical_movement = abs(movement[1])
            horizontal_movement = abs(movement[0])
            
            # Le mouvement vertical doit être plus important
            return vertical_movement > horizontal_movement
            
        except Exception as e:
            print(f"Erreur dans _detect_yes: {str(e)}")
            return False

    def _detect_no(self, hands_info):
        """Non en LSF : Index levé avec mouvement de droite à gauche"""
        try:
            if not hands_info or not isinstance(hands_info, list):
                return False
            
            # Prendre la première main disponible
            hand = hands_info[0]
            if not isinstance(hand, dict):
                return False
            
            # Vérifier la position des doigts (index levé uniquement)
            fingers = hand.get('fingers_up', {})
            if not isinstance(fingers, dict):
                return False
                
            if not (fingers.get('index', {}).get('up', False) and 
                   sum(1 for f in ['thumb', 'middle', 'ring', 'pinky']
                       if fingers.get(f, {}).get('up', False)) == 0):
                return False
            
            # Vérifier le mouvement horizontal
            history = self.movement_history_right if hand.get('handedness') == 'Right' else self.movement_history_left
            if len(history) < 2:
                return False
                
            start_pos = np.array(history[0])
            end_pos = np.array(history[-1])
            movement = end_pos - start_pos
            
            horizontal_movement = abs(movement[0])
            vertical_movement = abs(movement[1])
            
            # Le mouvement horizontal doit être plus important
            return horizontal_movement > vertical_movement
            
        except Exception as e:
            print(f"Erreur dans _detect_no: {str(e)}")
            return False

    def _detect_please(self, hands_info):
        """S'il te plaît : Main plate sur la poitrine qui fait un cercle"""
        fingers = hands_info[0]['fingers_up']
        # Main plate qui tourne (tous les doigts tendus)
        return (fingers['total_up'] >= 4 and 
                all(fingers[f]['up'] for f in ['index', 'middle', 'ring', 'pinky']))

    def _detect_house(self, hands_info):
        """Maison : Les deux mains qui forment un toit"""
        fingers = hands_info[0]['fingers_up']
        # Tous les doigts tendus pour former le toit
        return (fingers['total_up'] >= 4 and 
                all(fingers[f]['up'] for f in ['index', 'middle', 'ring', 'pinky']))

    def _detect_eat(self, hands_info):
        """Manger : Main qui va vers la bouche"""
        fingers = hands_info[0]['fingers_up']
        # Main en forme de pince
        return (fingers['total_up'] == 2 and 
                fingers['thumb']['up'] and 
                fingers['index']['up'] and 
                not any(fingers[f]['up'] for f in ['middle', 'ring', 'pinky']))

    def _detect_drink(self, hands_info):
        """Boire : Pouce vers la bouche"""
        fingers = hands_info[0]['fingers_up']
        # Uniquement le pouce levé
        return (fingers['total_up'] == 1 and 
                fingers['thumb']['up'] and 
                not any(fingers[f]['up'] for f in ['index', 'middle', 'ring', 'pinky']))

    def _compare_positions(self, pos1, pos2, threshold=0.03):
        """Compare deux positions pour déterminer si le mouvement est significatif"""
        try:
            if not isinstance(pos1, dict) or not isinstance(pos2, dict):
                print("Format de position invalide")
                return True
            
            # Vérifier que les clés nécessaires sont présentes
            required_keys = ['x', 'y', 'z']
            if not all(k in pos1 for k in required_keys) or not all(k in pos2 for k in required_keys):
                print("Clés manquantes dans les positions")
                return True
            
            # Extraire les valeurs numériques des dictionnaires
            x1, y1, z1 = float(pos1['x']), float(pos1['y']), float(pos1['z'])
            x2, y2, z2 = float(pos2['x']), float(pos2['y']), float(pos2['z'])
            
            # Calculer la distance euclidienne
            distance = math.sqrt(
                (x1 - x2)**2 +
                (y1 - y2)**2 +
                (z1 - z2)**2
            )
            
            # Retourner True si le mouvement est significatif
            return distance > threshold
            
        except Exception as e:
            print(f"Erreur lors de la comparaison des positions: {str(e)}")
            return True

    def learn_gesture(self, hands_info):
        """Apprend un nouveau geste"""
        try:
            if not self.is_learning:
                return
            
            # Extraire les caractéristiques de la main
            features = self._extract_gesture_features(hands_info)
            if not features:
                return
            
            # Ajouter les caractéristiques à la séquence
            self.gesture_frames.append(features)
            print(f"Frame capturée ({len(self.gesture_frames)})")
            
            # Si on a assez de frames, vérifier si on doit en supprimer
            if len(self.gesture_frames) > 1:
                last_frame = self.gesture_frames[-2]
                current_frame = self.gesture_frames[-1]
                
                # Vérifier si le mouvement est significatif
                if not self._compare_positions(
                    last_frame.get('palm_pos', {}),
                    current_frame.get('palm_pos', {})
                ):
                    # Supprimer la dernière frame si le mouvement n'est pas significatif
                    self.gesture_frames.pop()
                    print("Frame ignorée (mouvement non significatif)")
            
            # Vérifier si on a trop de frames
            if len(self.gesture_frames) > 100:
                print("Trop de frames capturées !")
                print("Veuillez refaire le geste plus lentement.")
            else:
                # Nettoyer la séquence pour garder les mouvements significatifs
                cleaned_frames = self._clean_sequence(self.gesture_frames)
                
                self.custom_gestures[self.current_gesture] = {
                    'sequence': cleaned_frames,
                    'time': time.time()
                }
                
                # Sauvegarder les gestes personnalisés
                self.save_custom_gestures()
                
        except Exception as e:
            print(f"Erreur lors de l'apprentissage: {str(e)}")
            import traceback
            print("Traceback complet:")
            print(traceback.format_exc())