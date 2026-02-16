#!/usr/bin/env python3
"""
Script de maintenance : duplique les entrées récurrentes du budget familial
pour le mois en cours (date du 1er, statut prévu).
À exécuter au 1er de chaque mois (cron : 0 0 1 * *).
Usage : depuis la racine du projet, avec .env configuré :
  python duplicate_budget_recurrent.py
"""
import os
import sys

# S'assurer que le répertoire du projet est sur le path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import duplicate_budget_recurrent_mois_courant

def main():
    count, message = duplicate_budget_recurrent_mois_courant()
    print(message)
    return 0 if count >= 0 else 1

if __name__ == "__main__":
    sys.exit(main())
