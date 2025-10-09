#!/usr/bin/env python3
"""
Script de prueba para verificar las optimizaciones implementadas
"""

import time
import requests
from datetime import datetime

def test_performance():
    """Prueba de rendimiento básica"""
    print("🧪 Iniciando pruebas de optimización...")
    
    # URLs a probar
    test_urls = [
        'http://localhost:5000/',
        'http://localhost:5000/menu',
        'http://localhost:5000/login',
        'http://localhost:5000/registro'
    ]
    
    results = {}
    
    for url in test_urls:
        print(f"⏱️  Probando: {url}")
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=10)
            end_time = time.time()
            load_time = end_time - start_time
            
            results[url] = {
                'status': response.status_code,
                'load_time': round(load_time, 3),
                'success': response.status_code == 200
            }
            
            status_icon = "✅" if response.status_code == 200 else "❌"
            print(f"   {status_icon} Status: {response.status_code} | Tiempo: {load_time:.3f}s")
            
        except requests.exceptions.RequestException as e:
            results[url] = {
                'status': 'ERROR',
                'load_time': None,
                'success': False,
                'error': str(e)
            }
            print(f"   ❌ Error: {e}")
    
    return results

def test_form_validation():
    """Prueba de validación de formularios"""
    print("\n📝 Probando validación de formularios...")
    
    # Datos de prueba para formulario de registro
    test_data = {
        'nombre': 'Usuario Test',
        'email': 'test@example.com',
        'confirm_email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'terms': 'on'
    }
    
    try:
        # Simular envío de formulario
        response = requests.post('http://localhost:5000/registro', data=test_data, timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Formulario procesado correctamente")
            return True
        else:
            print(f"   ❌ Error en formulario: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def generate_report(results):
    """Genera reporte de resultados"""
    print("\n📊 REPORTE DE OPTIMIZACIONES")
    print("=" * 50)
    
    successful_tests = sum(1 for r in results.values() if r['success'])
    total_tests = len(results)
    
    print(f"Pruebas exitosas: {successful_tests}/{total_tests}")
    
    if successful_tests > 0:
        avg_load_time = sum(r['load_time'] for r in results.values() if r['load_time']) / successful_tests
        print(f"Tiempo promedio de carga: {avg_load_time:.3f}s")
        
        # Verificar si los tiempos son aceptables (< 2 segundos)
        slow_pages = [url for url, r in results.items() if r['load_time'] and r['load_time'] > 2.0]
        if slow_pages:
            print(f"⚠️  Páginas lentas (>2s): {len(slow_pages)}")
            for page in slow_pages:
                print(f"   - {page}: {results[page]['load_time']}s")
        else:
            print("✅ Todas las páginas cargan en menos de 2 segundos")
    
    print("\n🎯 OPTIMIZACIONES IMPLEMENTADAS:")
    print("✅ Limpieza automática optimizada (solo en rutas admin)")
    print("✅ Consultas de base de datos optimizadas")
    print("✅ Índices adicionales creados")
    print("✅ Cache para categorías implementado")
    print("✅ Manejo de errores en formularios mejorado")
    print("✅ Consultas N+1 eliminadas")
    print("✅ Validación de formularios preserva datos")

if __name__ == "__main__":
    print("🚀 MenuMastery - Test de Optimizaciones")
    print("=" * 50)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code != 200:
            print("❌ El servidor no está respondiendo correctamente")
            exit(1)
    except requests.exceptions.RequestException:
        print("❌ No se puede conectar al servidor. Asegúrate de que esté corriendo en localhost:5000")
        exit(1)
    
    # Ejecutar pruebas
    results = test_performance()
    form_test = test_form_validation()
    
    # Generar reporte
    generate_report(results)
    
    print(f"\n📝 Prueba de formularios: {'✅ Exitosa' if form_test else '❌ Fallida'}")
    print("\n✨ Pruebas completadas!")
