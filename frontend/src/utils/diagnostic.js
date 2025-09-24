/**
 * Utilitaires de diagnostic pour identifier les problèmes de l'application
 */

class DiagnosticTool {
  static async runFullDiagnostic() {
    console.log('🔍 === DIAGNOSTIC COMPLET DE L\'APPLICATION ===');
    
    // 1. Vérifier l'environnement
    this.checkEnvironment();
    
    // 2. Vérifier le localStorage
    this.checkLocalStorage();
    
    // 3. Vérifier la connectivité réseau
    await this.checkNetworkConnectivity();
    
    // 4. Vérifier les endpoints API
    await this.checkAPIEndpoints();
    
    console.log('🔍 === FIN DU DIAGNOSTIC ===');
  }
  
  static checkEnvironment() {
    console.log('🌍 === VÉRIFICATION ENVIRONNEMENT ===');
    console.log('- URL de l\'application:', window.location.href);
    console.log('- User Agent:', navigator.userAgent);
    console.log('- API Base URL:', process.env.REACT_APP_API_URL || 'http://localhost:8080/api');
    console.log('- Mode React:', process.env.NODE_ENV);
  }
  
  static checkLocalStorage() {
    console.log('💾 === VÉRIFICATION LOCALSTORAGE ===');
    
    const items = ['access_token', 'refresh_token', 'user'];
    items.forEach(item => {
      const value = localStorage.getItem(item);
      if (value) {
        if (item.includes('token')) {
          console.log(`- ${item}: ${value.substring(0, 50)}...`);
        } else {
          console.log(`- ${item}:`, JSON.parse(value));
        }
      } else {
        console.log(`- ${item}: ❌ MANQUANT`);
      }
    });
    
    console.log('- Nombre total d\'items dans localStorage:', localStorage.length);
  }
  
  static async checkNetworkConnectivity() {
    console.log('🌐 === VÉRIFICATION CONNECTIVITÉ RÉSEAU ===');
    
    const testUrls = [
      'http://localhost:8080/health',
      'http://localhost:3000',
      'https://httpbin.org/status/200'
    ];
    
    for (const url of testUrls) {
      try {
        const response = await fetch(url, { 
          method: 'GET',
          mode: 'cors',
          timeout: 5000 
        });
        console.log(`- ${url}: ✅ ${response.status} ${response.statusText}`);
      } catch (error) {
        console.log(`- ${url}: ❌ ${error.message}`);
      }
    }
  }
  
  static async checkAPIEndpoints() {
    console.log('🔗 === VÉRIFICATION ENDPOINTS API ===');
    
    const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';
    const token = localStorage.getItem('access_token');
    
    const endpoints = [
      { url: '/health', requireAuth: false },
      { url: '/users/profile', requireAuth: true },
      { url: '/passwords/', requireAuth: true }
    ];
    
    for (const endpoint of endpoints) {
      try {
        const headers = { 'Content-Type': 'application/json' };
        if (endpoint.requireAuth && token) {
          headers.Authorization = `Bearer ${token}`;
        }
        
        const response = await fetch(`${baseURL}${endpoint.url}`, {
          method: 'GET',
          headers,
          timeout: 5000
        });
        
        const data = await response.json();
        console.log(`- ${endpoint.url}: ✅ ${response.status}`, data);
      } catch (error) {
        console.log(`- ${endpoint.url}: ❌ ${error.message}`);
      }
    }
  }
  
  static clearAllData() {
    console.log('🧹 === NETTOYAGE COMPLET DES DONNÉES ===');
    const itemCount = localStorage.length;
    localStorage.clear();
    console.log(`- Supprimé ${itemCount} items du localStorage`);
    
    // Vider les cookies si nécessaire
    document.cookie.split(";").forEach(function(c) { 
      document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
    });
    
    console.log('- Cache navigateur vidé');
    console.log('- Redirection vers la page de login...');
    
    setTimeout(() => {
      window.location.href = '/login';
    }, 1000);
  }
  
  static async testPasswordFlow() {
    console.log('🔐 === TEST FLUX DES MOTS DE PASSE ===');
    
    try {
      // Simuler l'appel comme le fait le Dashboard
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        console.log('❌ Aucun token trouvé dans localStorage');
        return;
      }
      
      console.log('📡 Test de l\'endpoint passwords...');
      const response = await fetch(`${API_BASE_URL}/passwords/?page=1&limit=50`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Réponse API passwords:', data);
        console.log(`- Nombre de mots de passe: ${data.passwords?.length || 0}`);
        console.log(`- Pagination: ${JSON.stringify(data.pagination)}`);
      } else {
        console.log('❌ Erreur API:', response.status, response.statusText);
        const errorData = await response.text();
        console.log('- Détails de l\'erreur:', errorData);
      }
      
    } catch (error) {
      console.log('❌ Exception lors du test:', error);
    }
  }
}

// Exposer l'outil de diagnostic globalement pour faciliter le debugging
window.DiagnosticTool = DiagnosticTool;

export default DiagnosticTool;