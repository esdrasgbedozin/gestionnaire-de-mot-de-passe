#!/bin/bash

# 🚀 Script de setup simplifié - DÉPRÉCIÉ
# Utilisez ./start.sh à la place

echo "⚠️ Ce script est déprécié."
echo "🔄 Utilisez ./start.sh à la place :"
echo ""
echo "  ./start.sh          # Démarrer l'application"
echo "  ./start.sh --dev    # Mode développement"  
echo "  ./start.sh --help   # Aide complète"
echo ""

# Rediriger vers le nouveau script
cd .. && ./start.sh "$@"
