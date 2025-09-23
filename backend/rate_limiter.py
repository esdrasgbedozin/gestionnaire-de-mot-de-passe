#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate limiting middleware pour prévenir les attaques par force brute et l'abus d'API
"""

import time
import hashlib
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter basé sur la mémoire avec différentes stratégies
    """
    
    def __init__(self):
        # Structure: {client_id: {endpoint: deque of timestamps}}
        self.requests = defaultdict(lambda: defaultdict(deque))
        
        # Configuration par endpoint
        self.limits = {
            # Authentification - moins strict en développement
            '/api/auth/login': {'requests': 10, 'window': 300, 'block_duration': 120},  # 10/5min, block 2min
            '/api/auth/register': {'requests': 5, 'window': 300, 'block_duration': 120},  # 5/5min, block 2min
            '/api/auth/refresh': {'requests': 20, 'window': 300, 'block_duration': 60},  # 20/5min, block 1min
            
            # Mots de passe - modéré
            '/api/passwords': {'requests': 50, 'window': 60, 'block_duration': 60},  # 50/min, block 1min
            '/api/passwords/*': {'requests': 30, 'window': 60, 'block_duration': 60},  # 30/min, block 1min
            
            # Utilisateurs - modéré
            '/api/users/profile': {'requests': 30, 'window': 60, 'block_duration': 60},  # 30/min, block 1min
            
            # Défaut pour toutes les autres routes
            'default': {'requests': 100, 'window': 60, 'block_duration': 60}  # 100/min, block 1min
        }
        
        # Blocked IPs: {client_id: unblock_time}
        self.blocked_clients = {}
        
        # Statistiques
        self.stats = defaultdict(lambda: {'requests': 0, 'blocks': 0, 'last_request': None})
    
    def _get_client_id(self, request):
        """Identifier unique du client (IP + User-Agent hash)"""
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Hash pour anonymiser tout en gardant l'unicité
        client_hash = hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()[:16]
        return client_hash
    
    def _get_rate_limit_config(self, endpoint):
        """Obtenir la configuration de rate limiting pour un endpoint"""
        # Recherche exacte d'abord
        if endpoint in self.limits:
            return self.limits[endpoint]
        
        # Recherche avec wildcard
        for pattern, config in self.limits.items():
            if pattern.endswith('*') and endpoint.startswith(pattern[:-1]):
                return config
        
        # Configuration par défaut
        return self.limits['default']
    
    def _normalize_endpoint(self, path):
        """Normaliser le chemin pour le rate limiting"""
        # Supprimer les paramètres de requête
        if '?' in path:
            path = path.split('?')[0]
        
        # Remplacer les IDs par des wildcards pour grouper les endpoints similaires
        import re
        # Remplacer les UUIDs et IDs numériques
        path = re.sub(r'/[a-f0-9\-]{8,}', '/*', path)  # UUIDs et long hashes
        path = re.sub(r'/\d+', '/*', path)  # IDs numériques
        
        return path
    
    def _cleanup_old_requests(self, client_id, endpoint, window):
        """Nettoyer les anciennes requêtes hors de la fenêtre"""
        now = time.time()
        cutoff = now - window
        
        request_times = self.requests[client_id][endpoint]
        while request_times and request_times[0] < cutoff:
            request_times.popleft()
    
    def _is_blocked(self, client_id):
        """Vérifier si un client est bloqué"""
        if client_id not in self.blocked_clients:
            return False
        
        if time.time() >= self.blocked_clients[client_id]:
            # Le blocage a expiré
            del self.blocked_clients[client_id]
            return False
        
        return True
    
    def _block_client(self, client_id, duration):
        """Bloquer un client pour une durée donnée"""
        self.blocked_clients[client_id] = time.time() + duration
        self.stats[client_id]['blocks'] += 1
        
        logger.warning(f"Client {client_id} blocked for {duration} seconds due to rate limiting")
    
    def is_allowed(self, request):
        """Vérifier si la requête est autorisée"""
        client_id = self._get_client_id(request)
        endpoint = self._normalize_endpoint(request.path)
        config = self._get_rate_limit_config(endpoint)
        
        # Vérifier si le client est bloqué
        if self._is_blocked(client_id):
            return False, {
                'allowed': False,
                'reason': 'blocked',
                'unblock_time': self.blocked_clients[client_id],
                'retry_after': int(self.blocked_clients[client_id] - time.time())
            }
        
        # Nettoyer les anciennes requêtes
        self._cleanup_old_requests(client_id, endpoint, config['window'])
        
        # Vérifier le nombre de requêtes dans la fenêtre
        request_count = len(self.requests[client_id][endpoint])
        
        if request_count >= config['requests']:
            # Limite dépassée, bloquer le client
            self._block_client(client_id, config['block_duration'])
            return False, {
                'allowed': False,
                'reason': 'rate_limit_exceeded',
                'limit': config['requests'],
                'window': config['window'],
                'retry_after': config['block_duration']
            }
        
        # Autoriser la requête et l'enregistrer
        self.requests[client_id][endpoint].append(time.time())
        self.stats[client_id]['requests'] += 1
        self.stats[client_id]['last_request'] = datetime.now()
        
        return True, {
            'allowed': True,
            'remaining': config['requests'] - request_count - 1,
            'reset_time': time.time() + config['window']
        }
    
    def get_stats(self):
        """Obtenir les statistiques de rate limiting"""
        return {
            'total_clients': len(self.stats),
            'blocked_clients': len(self.blocked_clients),
            'client_stats': dict(self.stats),
            'endpoint_limits': self.limits
        }
    
    def reset_client(self, client_id=None):
        """Réinitialiser le rate limiting pour un client spécifique ou tous"""
        if client_id:
            # Réinitialiser un client spécifique
            if client_id in self.blocked_clients:
                del self.blocked_clients[client_id]
            if client_id in self.requests:
                del self.requests[client_id]
            if client_id in self.stats:
                del self.stats[client_id]
        else:
            # Réinitialiser tous les clients
            self.blocked_clients.clear()
            self.requests.clear()
            self.stats.clear()
        
        logger.info(f"Rate limiter reset for client: {client_id if client_id else 'ALL'}")
    
    def unblock_client(self, client_id):
        """Débloquer manuellement un client"""
        if client_id in self.blocked_clients:
            del self.blocked_clients[client_id]
            logger.info(f"Client {client_id} manually unblocked")
            return True
        return False

# Instance globale du rate limiter
rate_limiter = RateLimiter()

def rate_limit_middleware(f):
    """Décorateur pour appliquer le rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed, info = rate_limiter.is_allowed(request)
        
        if not allowed:
            response = jsonify({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'details': info
            })
            
            if info['reason'] == 'blocked':
                response.status_code = 429
                response.headers['Retry-After'] = str(info['retry_after'])
            else:
                response.status_code = 429
                response.headers['Retry-After'] = str(info['retry_after'])
            
            # Headers informatifs
            if 'limit' in info:
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = '0'
            
            return response
        
        # Ajouter les headers de rate limiting à la réponse
        g.rate_limit_info = info
        return f(*args, **kwargs)
    
    return decorated_function

def add_rate_limit_headers(response):
    """Ajouter les headers de rate limiting à toutes les réponses"""
    if hasattr(g, 'rate_limit_info') and g.rate_limit_info.get('allowed'):
        info = g.rate_limit_info
        response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
        if 'reset_time' in info:
            response.headers['X-RateLimit-Reset'] = str(int(info['reset_time']))
    
    return response

def setup_rate_limiting(app):
    """Configurer le rate limiting pour l'application Flask"""
    
    # Ajouter les headers à toutes les réponses
    @app.after_request
    def after_request(response):
        return add_rate_limit_headers(response)
    
    # Route pour les statistiques de rate limiting (admin seulement)
    @app.route('/api/admin/rate-limit-stats')
    @rate_limit_middleware
    def rate_limit_stats():
        return jsonify(rate_limiter.get_stats())
    
    # Route pour réinitialiser le rate limiting (développement uniquement)
    @app.route('/api/admin/rate-limit-reset', methods=['POST'])
    def reset_rate_limit():
        from flask import request
        
        # Sécurité : uniquement en mode développement
        if app.config.get('ENV', 'production') == 'production':
            return jsonify({'error': 'Not available in production'}), 403
        
        data = request.get_json() or {}
        client_id = data.get('client_id')
        
        if client_id:
            # Réinitialiser un client spécifique
            rate_limiter.unblock_client(client_id)
            return jsonify({'message': f'Client {client_id} unblocked', 'status': 'success'})
        else:
            # Réinitialiser tout le rate limiter
            rate_limiter.reset_client()
            return jsonify({'message': 'Rate limiter reset for all clients', 'status': 'success'})
    
    logger.info("Rate limiting middleware configured")
    return app