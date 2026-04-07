import logging
from datetime import datetime 

# -----------------------------------------------------------------------------
# La bibliothèque "logging"
# -----------------------------------------------------------------------------
# - "logging" est la bibliothèque standard de Python pour afficher et enregistrer
#   des messages (appelés "logs").
# - Ces logs servent à suivre ce que fait le programme : informations,
#   avertissements, erreurs, etc.
# - Un "logger" est simplement un objet capable d’émettre ces messages.
# -----------------------------------------------------------------------------

def setup_logger(name, log_file=None, level=logging.INFO):
    """Configure un logger"""

    # On récupère un logger existant portant ce nom,
    # ou Python en crée un nouveau si c’est la première fois.
    logger = logging.getLogger(name)

    # On définit le niveau minimal des messages à afficher (INFO, WARNING, ERROR…)
    # Niveaux de logs (du moins important au plus grave) :
    # - DEBUG    → détails techniques pour le développeur → logger.debug("message")
    # - INFO     → informations normales du programme     → logger.info("message")
    # - WARNING  → avertissement sans blocage             → logger.warning("message")
    # - ERROR    → erreur empêchant une action            → logger.error("message")
    # - CRITICAL → erreur critique bloquante              → logger.critical("message")
    # Le niveau défini ici filtre les messages affichés :
    # seuls les messages de ce niveau et au-dessus seront visibles.
    logger.setLevel(level)

    # Définition du format des messages :
    # - %(asctime)s : date/heure
    # - %(name)s : nom du logger
    # - %(levelname)s : niveau du message
    # - %(message)s : texte du message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # --- Handler console ---
    # Un "handler" décide *où* envoyer les logs.
    # Ici : afficher les logs directement dans le terminal.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- Handler fichier ---
    # Si un chemin de fichier est fourni, on ajoute un second handler :
    # celui-ci écrit les logs dans un fichier texte.
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # On retourne le logger entièrement configuré.
    return logger