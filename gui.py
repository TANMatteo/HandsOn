import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import os
import time
from translations import Translator

class GUI:
    def __init__(self, root, app):
        self.translator = Translator()
        self.root = root
        self.app = app
        self.root.title(self.translator.get_text('title'))
        self.video_callback = None
        self.learn_callback = None
        self.remove_gesture_callback = None
        self.current_subtitle = ""
        self.subtitle_start_time = 0
        self.subtitle_duration = 3.0

        # Créer la barre de menu
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        # Menu Language
        self.language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Language", menu=self.language_menu)
        self.language_menu.add_command(label="Français", command=lambda: self.change_language('fr'))
        self.language_menu.add_command(label="English", command=lambda: self.change_language('en'))
        self.language_menu.add_command(label="中文", command=lambda: self.change_language('zh'))
        self.language_menu.add_command(label="हिंदी", command=lambda: self.change_language('hi'))
        self.language_menu.add_command(label="Español", command=lambda: self.change_language('es'))
        self.language_menu.add_command(label="العربية", command=lambda: self.change_language('ar'))
        self.language_menu.add_command(label="বাংলা", command=lambda: self.change_language('bn'))
        self.language_menu.add_command(label="Português", command=lambda: self.change_language('pt'))
        self.language_menu.add_command(label="Русский", command=lambda: self.change_language('ru'))
        self.language_menu.add_command(label="日本語", command=lambda: self.change_language('ja'))

        # Menu À propos
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.translator.get_text('about'), menu=about_menu)
        about_menu.add_command(label=self.translator.get_text('portfolio'), command=self.open_portfolio)
        about_menu.add_command(label="LinkedIn", command=self.open_linkedin)
        about_menu.add_command(label=self.translator.get_text('about'), command=self.show_about)
        
        # Frame principale
        main_frame = tk.Frame(root)
        main_frame.pack(padx=10, pady=10)
        
        # Frame vidéo
        video_frame = tk.Frame(main_frame)
        video_frame.pack(side=tk.LEFT, padx=10)
        
        self.video_label = tk.Label(video_frame)
        self.video_label.pack()
        
        # Frame informations
        info_frame = tk.Frame(main_frame)
        info_frame.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        # Bouton pour la caméra
        video_controls = tk.Frame(info_frame)
        video_controls.pack(pady=5)
        
        self.camera_button = tk.Button(
            video_controls,
            text=self.translator.get_text('use_camera'),
            command=self.on_camera_click,
            font=('Arial', 12)
        )
        self.camera_button.pack(side=tk.LEFT, padx=5)
        
        # Frame pour les boutons de gestion des gestes
        learn_frame = tk.LabelFrame(info_frame, text=self.translator.get_text('gesture_management'), font=('Arial', 12, 'bold'), padx=10, pady=5)
        learn_frame.pack(pady=10, fill=tk.X)
        
        # Sous-frame pour l'apprentissage
        learning_controls = tk.Frame(learn_frame)
        learning_controls.pack(pady=5, fill=tk.X)
        
        self.learn_button = tk.Button(
            learning_controls,
            text=self.translator.get_text('learn_new_gesture'),
            command=self.on_learn_click,
            font=('Arial', 12),
            bg='#4CAF50',
            fg='white',
            width=20,
            relief=tk.RAISED
        )
        self.learn_button.pack(side=tk.LEFT, padx=5)
        
        self.finish_button = tk.Button(
            learning_controls,
            text=self.translator.get_text('finish_learning'),
            command=self.on_finish_click,
            font=('Arial', 12),
            bg='#2196F3',
            fg='white',
            width=20,
            state=tk.DISABLED,
            relief=tk.RAISED
        )
        self.finish_button.pack(side=tk.LEFT, padx=5)
        
        # Sous-frame pour la suppression
        delete_controls = tk.Frame(learn_frame)
        delete_controls.pack(pady=5, fill=tk.X)
        
        self.remove_button = tk.Button(
            delete_controls,
            text=self.translator.get_text('delete_all_gestures'),
            command=self.on_remove_click,
            font=('Arial', 12),
            bg='#f44336',
            fg='white',
            width=20,
            relief=tk.RAISED
        )
        self.remove_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_specific_button = tk.Button(
            delete_controls,
            text=self.translator.get_text('delete_specific_gesture'),
            command=self.show_delete_specific_dialog,
            font=('Arial', 12),
            bg='#ff9800',
            fg='white',
            width=20,
            relief=tk.RAISED
        )
        self.delete_specific_button.pack(side=tk.LEFT, padx=5)
        
        # Label pour le statut d'apprentissage
        self.learning_label = tk.Label(
            learn_frame,
            text="",
            font=('Arial', 12, 'italic'),
            fg='#1976D2'
        )
        self.learning_label.pack(pady=5)
        
        # Zone de texte pour la traduction
        text_frame = tk.Frame(info_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.translation_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            width=40,
            height=20,
            font=('Arial', 12),
            yscrollcommand=scrollbar.set
        )
        self.translation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.translation_text.yview)
        
        # Bouton pour quitter
        self.quit_button = tk.Button(
            info_frame,
            text=self.translator.get_text('quit'),
            command=root.quit,
            font=('Arial', 12)
        )
        self.quit_button.pack(pady=10)
    
    def set_video_source_callback(self, callback):
        self.video_callback = callback
    
    def set_learn_callback(self, callback):
        self.learn_callback = callback
    
    def set_remove_gesture_callback(self, callback):
        self.remove_gesture_callback = callback
    
    def on_camera_click(self):
        if self.video_callback:
            self.video_callback("camera")
    
    def on_learn_click(self):
        """Commence l'apprentissage d'un nouveau geste"""
        if self.learn_callback:
            gesture_name = simpledialog.askstring(
                self.translator.get_text('new_gesture'),
                self.translator.get_text('enter_gesture_name'),
                parent=self.root
            )
            if gesture_name:
                messagebox.showinfo(
                    self.translator.get_text('learning'),
                    self.translator.get_text('learning_instructions')
                )
                self.learn_callback(gesture_name)
    
    def on_remove_click(self):
        """Supprime un geste personnalisé"""
        if self.remove_gesture_callback:
            result = messagebox.askyesno(
                self.translator.get_text('delete_gesture'),
                self.translator.get_text('delete_confirmation'),
                icon='warning'
            )
            if result:
                self.remove_gesture_callback()
                messagebox.showinfo(
                    self.translator.get_text('deletion'),
                    self.translator.get_text('deletion_success')
                )
    
    def update_learning_status(self, is_learning, frames_count=0):
        """Met à jour le statut de l'apprentissage"""
        if is_learning:
            self.learning_label.config(
                text=self.translator.get_text('learning_status').format(frames_count)
            )
            self.learn_button.config(state=tk.DISABLED)
            self.finish_button.config(state=tk.NORMAL)
        else:
            self.learning_label.config(text="")
            self.learn_button.config(state=tk.NORMAL)
            self.finish_button.config(state=tk.DISABLED)
    
    def on_finish_click(self):
        """Termine l'apprentissage du geste"""
        if self.learn_callback:
            self.learn_callback(None)  # None indique qu'on termine l'apprentissage
    
    def update_subtitle(self, text):
        """Met à jour le sous-titre actuel"""
        print(f"Réception du sous-titre : {text}")
        self.current_subtitle = text
        self.subtitle_start_time = time.time()

    def update_frame(self, frame):
        """Met à jour l'image de la caméra"""
        if frame is not None:
            # Convertir le frame en image PIL
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # Redimensionner l'image si nécessaire
            max_width = 640
            if image.width > max_width:
                ratio = max_width / image.width
                new_size = (max_width, int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Créer un objet Draw pour l'image redimensionnée
            draw = ImageDraw.Draw(image)
            
            # Ajouter les sous-titres si nécessaires
            current_time = time.time()
            time_since_subtitle = current_time - self.subtitle_start_time
            
            if self.current_subtitle and time_since_subtitle < self.subtitle_duration:
                print(f"Affichage du sous-titre : {self.current_subtitle} (temps écoulé : {time_since_subtitle:.1f}s)")
                try:
                    # Calculer la position des sous-titres (en bas de l'image)
                    img_width, img_height = image.size
                    font_size = min(36, img_height // 10)  # Ajuster la taille de la police en fonction de l'image
                    
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except OSError:
                        # Si arial n'est pas disponible, utiliser une police par défaut
                        print("Police Arial non trouvée, utilisation d'une police par défaut")
                        font = ImageFont.load_default()
                    
                    # Créer un fond semi-transparent pour les sous-titres
                    text_bbox = draw.textbbox((0, 0), self.current_subtitle, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    text_x = (img_width - text_width) // 2
                    text_y = img_height - text_height - 40  # Un peu plus haut pour être plus visible
                    
                    # Dessiner le fond semi-transparent
                    padding = 20
                    draw.rectangle(
                        [
                            text_x - padding,
                            text_y - padding,
                            text_x + text_width + padding,
                            text_y + text_height + padding
                        ],
                        fill=(0, 0, 0, 180)  # Fond plus opaque
                    )
                    
                    # Dessiner le texte
                    draw.text(
                        (text_x, text_y),
                        self.current_subtitle,
                        font=font,
                        fill=(255, 255, 255)  # Texte blanc
                    )
                except Exception as e:
                    print(f"Erreur lors de l'affichage des sous-titres : {str(e)}")
            
            # Convertir en format pour tkinter
            photo = ImageTk.PhotoImage(image=image)
            self.video_label.configure(image=photo)
            self.video_label.image = photo

    def update_translation(self, text):
        """Met à jour le texte dans la zone de traduction"""
        self.translation_text.delete(1.0, tk.END)
        self.translation_text.insert(tk.END, text)

    def open_portfolio(self):
        """Ouvre le portfolio dans le navigateur par défaut"""
        import webbrowser
        webbrowser.open("https://tanmatteoportfolio.netlify.app/")

    def open_linkedin(self):
        """Ouvre LinkedIn dans le navigateur par défaut"""
        import webbrowser
        webbrowser.open("https://www.linkedin.com/in/matteo-tan-842011298/")

    def show_about(self):
        """Affiche la fenêtre À propos"""
        about_window = tk.Toplevel(self.root)
        about_window.title(self.translator.get_text('about'))
        about_window.geometry("400x300")
        
        # Centrer la fenêtre
        about_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # Ajouter le contenu
        tk.Label(
            about_window,
            text="HandsOn",
            font=('Arial', 14, 'bold')
        ).pack(pady=10)
        
        tk.Label(
            about_window,
            text=self.translator.get_text('developed_by'),
            font=('Arial', 12)
        ).pack(pady=5)
        
        # Boutons avec icônes
        button_frame = tk.Frame(about_window)
        button_frame.pack(pady=20)
        
        portfolio_btn = tk.Button(
            button_frame,
            text=self.translator.get_text('portfolio'),
            command=self.open_portfolio,
            font=('Arial', 11),
            bg='#4CAF50',
            fg='white',
            padx=20
        )
        portfolio_btn.pack(side=tk.LEFT, padx=5)
        
        linkedin_btn = tk.Button(
            button_frame,
            text="LinkedIn",
            command=self.open_linkedin,
            font=('Arial', 11),
            bg='#0077B5',  # Couleur LinkedIn
            fg='white',
            padx=20
        )
        linkedin_btn.pack(side=tk.LEFT, padx=5)

    def change_language(self, language):
        self.translator.set_language(language)
        self.update_interface_texts()
    
    def update_interface_texts(self):
        """Met à jour tous les textes de l'interface avec la nouvelle langue"""
        self.root.title(self.translator.get_text('title'))
        self.camera_button.config(text=self.translator.get_text('use_camera'))
        self.learn_button.config(text=self.translator.get_text('learn_new_gesture'))
        self.finish_button.config(text=self.translator.get_text('finish_learning'))
        self.remove_button.config(text=self.translator.get_text('delete_all_gestures'))
        self.delete_specific_button.config(text=self.translator.get_text('delete_specific_gesture'))
        self.quit_button.config(text=self.translator.get_text('quit'))
        self.learning_label.config(text="")

    def show_delete_specific_dialog(self):
        """Affiche une fenêtre de dialogue pour supprimer un geste spécifique"""
        # Récupérer la liste des gestes personnalisés et prédéfinis
        custom_gestures = self.app.sign_translator.get_custom_gestures()
        predefined_gestures = list(self.app.sign_translator.gestures.keys())
        all_gestures = custom_gestures + predefined_gestures
        
        if not all_gestures:
            messagebox.showinfo("Information", "Aucun geste disponible.")
            return
        
        # Créer une nouvelle fenêtre
        delete_window = tk.Toplevel(self.root)
        delete_window.title(self.translator.get_text('delete_specific_gesture'))
        delete_window.geometry("300x400")
        
        # Label d'instruction
        tk.Label(delete_window, text=self.translator.get_text('select_gesture_delete')).pack(pady=10)
        
        # Créer une liste avec les gestes
        gesture_listbox = tk.Listbox(delete_window, width=40, height=10)
        gesture_listbox.pack(pady=5, padx=10)
        
        # Ajouter les gestes personnalisés
        if custom_gestures:
            gesture_listbox.insert(tk.END, self.translator.get_text('custom_gestures_title'))
            for gesture in custom_gestures:
                gesture_listbox.insert(tk.END, gesture)
        
        # Ajouter les gestes prédéfinis
        gesture_listbox.insert(tk.END, self.translator.get_text('predefined_gestures_title'))
        for gesture in predefined_gestures:
            gesture_listbox.insert(tk.END, gesture)
        
        def confirm_delete():
            selection = gesture_listbox.curselection()
            if not selection:
                messagebox.showwarning("Attention", self.translator.get_text('warning_select_gesture'))
                return
                
            gesture = gesture_listbox.get(selection[0])
            
            # Vérifier si c'est un titre de section
            if gesture.startswith("==="):
                messagebox.showwarning("Attention", self.translator.get_text('warning_select_valid'))
                return
            
            # Vérifier si c'est un geste prédéfini
            if gesture in predefined_gestures and gesture not in custom_gestures:
                messagebox.showwarning("Attention", self.translator.get_text('warning_predefined'))
                return
            
            if messagebox.askyesno("Confirmation", self.translator.get_text('confirm_delete').format(gesture)):
                if self.app.sign_translator.delete_gesture(gesture):
                    messagebox.showinfo("Succès", self.translator.get_text('success_delete').format(gesture))
                    delete_window.destroy()
                else:
                    messagebox.showerror("Erreur", self.translator.get_text('error_delete').format(gesture))
        
        # Boutons
        button_frame = tk.Frame(delete_window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text=self.translator.get_text('delete'), command=confirm_delete).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text=self.translator.get_text('cancel'), command=delete_window.destroy).pack(side=tk.LEFT, padx=5)