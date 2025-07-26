# assistant_ia_personnel.py

# === IMPORTS ===
import face_recognition
import cv2
import speech_recognition as sr
import pyttsx3
import subprocess
import webbrowser
import openai
import time

# === CONFIGURATION ===
openai.api_key = "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"  # 🔑 Remplace par ta clé OpenAI
PHOTO_UTILISATEUR = "ton_visage.jpg"  # 📸 Photo de ton visage dans le dossier

# === INITIALISATION ===
tts = pyttsx3.init()
reconnaisseur = sr.Recognizer()
encodage_utilisateur = face_recognition.face_encodings(
    face_recognition.load_image_file(PHOTO_UTILISATEUR)
)[0]

# === FONCTIONS ===

def parler(texte):
    print("🗣️ ", texte)
    tts.say(texte)
    tts.runAndWait()

def ecouter():
    with sr.Microphone() as source:
        print("🎤 En attente de commande...")
        audio = reconnaisseur.listen(source)
    try:
        return reconnaisseur.recognize_google(audio, language="fr-FR")
    except:
        return ""

def generer_reponse(prompt):
    reponse = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es un assistant personnel vocal très compétent, qui peut aussi déclencher des actions système ou web."},
            {"role": "user", "content": prompt}
        ]
    )
    return reponse.choices[0].message.content

def rechercher_sur_internet(texte):
    url = f"https://www.google.com/search?q={texte.replace(' ', '+')}"
    webbrowser.open(url)

def lancer_vs_code():
    subprocess.Popen(["code"])  # Assure-toi que 'code' fonctionne dans le terminal

def executer_commande(commande):
    subprocess.run(commande, shell=True)

def reconnaitre_utilisateur():
    webcam = cv2.VideoCapture(0)
    parler("Recherche de ton visage...")
    trouve = False

    while True:
        ret, frame = webcam.read()
        rgb = frame[:, :, ::-1]
        faces = face_recognition.face_encodings(rgb)

        for face in faces:
            correspondance = face_recognition.compare_faces([encodage_utilisateur], face)
            if correspondance[0]:
                trouve = True
                break

        cv2.imshow("Reconnaissance faciale", frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or trouve:
            break

    webcam.release()
    cv2.destroyAllWindows()
    return trouve

def traiter_commande_voix():
    commande = ecouter()
    if not commande:
        parler("Je n'ai pas compris.")
        return

    if "ouvre VS Code" in commande or "ouvre Visual Studio Code" in commande:
        parler("J'ouvre Visual Studio Code.")
        lancer_vs_code()
    elif "recherche" in commande:
        recherche = commande.replace("recherche", "").strip()
        parler(f"Voici ce que j'ai trouvé pour : {recherche}")
        rechercher_sur_internet(recherche)
    else:
        reponse = generer_reponse(commande)
        parler(reponse)

# === MAIN ===
if __name__ == "__main__":
    if reconnaitre_utilisateur():
        parler("Bonjour Yokoha. Je suis à ton service.")
        while True:
            traiter_commande_voix()
            time.sleep(1)
    else:
        parler("Visage non reconnu. Accès refusé.")
