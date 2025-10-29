# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE GRÁFICOS
=============================================================================
Genera gráficos visuales de rendimiento y estadísticas
Requiere: matplotlib
Instalación: pip install matplotlib --break-system-packages
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from core.db_manager import db
from core.queries import queries


# ===================================================================
# CONFIGURACIÓN
# ===================================================================

GRAFICOS_DIR = Path("graficos")
GRAFICOS_DIR.mkdir(exist_ok=True)

# Estilo de gráficos
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


# ===================================================================
# CLASE GENERADORA DE GRÁFICOS
# ===================================================================

class GeneradorGraficos:
    """Genera gráficos de rendimiento y estadísticas"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.colores = {
            'ganancia': '#2ecc71',
            'perdida': '#e74c3c',
            'capital': '#3498db',
            'comision': '#e67e22',
            'objetivo': '#9b59b6'
        }
    
    # ===================================================================
    # GRÁFICOS DE CICLO
    # ===================================================================
    
    def grafico_progreso_ciclo(self, ciclo_id: int) -> Optional[Path]:
        """
        Gráfico de progreso diario del ciclo
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Path: Ruta del gráfico generado
        """
        # Obtener días del ciclo
        dias = db.execute_query("""
            SELECT 
                numero_dia,
                fecha,
                capital_inicial,
                capital_final,
                ganancia_neta
            FROM dias
            WHERE ciclo_id = ? AND estado = 'cerrado'
            ORDER BY numero_dia
        """, (ciclo_id,))
        
        if not dias or len(dias) < 2:
            print("❌ No hay suficientes datos para generar gráfico")
            return None
        
        # Preparar datos
        numeros_dia = [dia['numero_dia'] for dia in dias]
        capital_inicial = [dia['capital_inicial'] for dia in dias]
        capital_final = [dia['capital_final'] for dia in dias]
        ganancias = [dia['ganancia_neta'] for dia in dias]
        
        # Crear figura con subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Subplot 1: Capital
        ax1.plot(numeros_dia, capital_inicial, 'o-', 
                label='Capital Inicial', color=self.colores['capital'], linewidth=2)
        ax1.plot(numeros_dia, capital_final, 's-', 
                label='Capital Final', color=self.colores['ganancia'], linewidth=2)
        ax1.set_xlabel('Día')
        ax1.set_ylabel('Capital (USD)')
        ax1.set_title(f'Evolución del Capital - Ciclo #{ciclo_id}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Subplot 2: Ganancias diarias
        colores_barras = [self.colores['ganancia'] if g >= 0 else self.colores['perdida'] 
                         for g in ganancias]
        ax2.bar(numeros_dia, ganancias, color=colores_barras, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_xlabel('Día')
        ax2.set_ylabel('Ganancia Neta (USD)')
        ax2.set_title('Ganancia Neta por Día')
        ax2.grid(True, alpha=0.3)
        
        # Guardar
        archivo = GRAFICOS_DIR / f"ciclo_{ciclo_id}_progreso_{self.timestamp}.png"
        plt.tight_layout()
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfico generado: {archivo.name}")
        return archivo
    
    def grafico_roi_ciclo(self, ciclo_id: int) -> Optional[Path]:
        """
        Gráfico de ROI acumulado del ciclo
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Path: Ruta del gráfico generado
        """
        # Obtener ciclo
        ciclo = queries.obtener_ciclo_por_id(ciclo_id)
        if not ciclo:
            print("❌ Ciclo no encontrado")
            return None
        
        # Obtener días
        dias = db.execute_query("""
            SELECT 
                numero_dia,
                ganancia_neta
            FROM dias
            WHERE ciclo_id = ? AND estado = 'cerrado'
            ORDER BY numero_dia
        """, (ciclo_id,))
        
        if not dias:
            print("❌ No hay datos")
            return None
        
        # Calcular ROI acumulado
        numeros_dia = []
        roi_acumulado = []
        ganancia_acumulada = 0
        
        for dia in dias:
            ganancia_acumulada += dia['ganancia_neta']
            roi = (ganancia_acumulada / ciclo['inversion_inicial'] * 100) if ciclo['inversion_inicial'] > 0 else 0
            numeros_dia.append(dia['numero_dia'])
            roi_acumulado.append(roi)
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(numeros_dia, roi_acumulado, 'o-', 
                color=self.colores['ganancia'], linewidth=2, markersize=8)
        ax.fill_between(numeros_dia, 0, roi_acumulado, 
                        alpha=0.3, color=self.colores['ganancia'])
        
        ax.set_xlabel('Día')
        ax.set_ylabel('ROI Acumulado (%)')
        ax.set_title(f'ROI Acumulado - Ciclo #{ciclo_id}')
        ax.grid(True, alpha=0.3)
        
        # Línea de objetivo si existe
        ganancia_objetivo = queries.obtener_ganancia_objetivo()
        dias_operados = len(dias)
        roi_objetivo_acumulado = ganancia_objetivo * dias_operados
        ax.axhline(y=roi_objetivo_acumulado, color=self.colores['objetivo'], 
                  linestyle='--', label=f'Objetivo: {roi_objetivo_acumulado:.1f}%')
        ax.legend()
        
        # Anotación final
        roi_final = roi_acumulado[-1]
        ax.annotate(f'ROI Final: {roi_final:.2f}%',
                   xy=(numeros_dia[-1], roi_final),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # Guardar
        archivo = GRAFICOS_DIR / f"ciclo_{ciclo_id}_roi_{self.timestamp}.png"
        plt.tight_layout()
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfico ROI generado: {archivo.name}")
        return archivo
    
    def grafico_comisiones_ciclo(self, ciclo_id: int) -> Optional[Path]:
        """
        Gráfico de comisiones pagadas por día
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Path: Ruta del gráfico generado
        """
        dias = db.execute_query("""
            SELECT 
                numero_dia,
                comisiones_pagadas
            FROM dias
            WHERE ciclo_id = ? AND estado = 'cerrado'
            ORDER BY numero_dia
        """, (ciclo_id,))
        
        if not dias:
            print("❌ No hay datos")
            return None
        
        numeros_dia = [dia['numero_dia'] for dia in dias]
        comisiones = [dia['comisiones_pagadas'] if dia['comisiones_pagadas'] else 0 for dia in dias]
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.bar(numeros_dia, comisiones, color=self.colores['comision'], alpha=0.7)
        ax.set_xlabel('Día')
        ax.set_ylabel('Comisiones Pagadas (USD)')
        ax.set_title(f'Comisiones por Día - Ciclo #{ciclo_id}')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Línea promedio
        promedio = sum(comisiones) / len(comisiones) if comisiones else 0
        ax.axhline(y=promedio, color='red', linestyle='--', 
                  label=f'Promedio: ${promedio:.2f}')
        ax.legend()
        
        # Total acumulado
        total = sum(comisiones)
        ax.text(0.02, 0.98, f'Total comisiones: ${total:.2f}',
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Guardar
        archivo = GRAFICOS_DIR / f"ciclo_{ciclo_id}_comisiones_{self.timestamp}.png"
        plt.tight_layout()
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfico de comisiones generado: {archivo.name}")
        return archivo
    
    # ===================================================================
    # GRÁFICOS COMPARATIVOS
    # ===================================================================
    
    def grafico_comparativo_ciclos(self) -> Optional[Path]:
        """
        Compara rendimiento de todos los ciclos cerrados
        
        Returns:
            Path: Ruta del gráfico generado
        """
        ciclos = db.execute_query("""
            SELECT 
                id,
                dias_operados,
                ganancia_total,
                roi_total
            FROM ciclos
            WHERE estado = 'cerrado'
            ORDER BY id
        """)
        
        if not ciclos or len(ciclos) < 2:
            print("❌ Se necesitan al menos 2 ciclos cerrados")
            return None
        
        ids = [f"#{c['id']}" for c in ciclos]
        ganancias = [c['ganancia_total'] for c in ciclos]
        rois = [c['roi_total'] for c in ciclos]
        
        # Crear figura con subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Subplot 1: Ganancias
        ax1.bar(ids, ganancias, color=self.colores['ganancia'], alpha=0.7)
        ax1.set_xlabel('Ciclo')
        ax1.set_ylabel('Ganancia Total (USD)')
        ax1.set_title('Ganancia Total por Ciclo')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Subplot 2: ROI
        ax2.bar(ids, rois, color=self.colores['objetivo'], alpha=0.7)
        ax2.set_xlabel('Ciclo')
        ax2.set_ylabel('ROI (%)')
        ax2.set_title('ROI por Ciclo')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Guardar
        archivo = GRAFICOS_DIR / f"comparativo_ciclos_{self.timestamp}.png"
        plt.tight_layout()
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfico comparativo generado: {archivo.name}")
        return archivo
    
    def grafico_eficiencia_ciclos(self) -> Optional[Path]:
        """
        Gráfico de eficiencia (ganancia/día) de ciclos
        
        Returns:
            Path: Ruta del gráfico generado
        """
        ciclos = db.execute_query("""
            SELECT 
                id,
                dias_operados,
                ganancia_total
            FROM ciclos
            WHERE estado = 'cerrado' AND dias_operados > 0
            ORDER BY id
        """)
        
        if not ciclos:
            print("❌ No hay ciclos cerrados")
            return None
        
        ids = [f"#{c['id']}" for c in ciclos]
        eficiencia = [c['ganancia_total'] / c['dias_operados'] for c in ciclos]
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colores_barras = [self.colores['ganancia'] if e > 0 else self.colores['perdida'] 
                         for e in eficiencia]
        ax.bar(ids, eficiencia, color=colores_barras, alpha=0.7)
        
        ax.set_xlabel('Ciclo')
        ax.set_ylabel('Ganancia Promedio por Día (USD)')
        ax.set_title('Eficiencia por Ciclo (Ganancia/Día)')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Línea promedio global
        promedio_global = sum(eficiencia) / len(eficiencia)
        ax.axhline(y=promedio_global, color='red', linestyle='--',
                  label=f'Promedio: ${promedio_global:.2f}/día')
        ax.legend()
        
        # Guardar
        archivo = GRAFICOS_DIR / f"eficiencia_ciclos_{self.timestamp}.png"
        plt.tight_layout()
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfico de eficiencia generado: {archivo.name}")
        return archivo
    
    # ===================================================================
    # GRÁFICOS DE VENTAS
    # ===================================================================
    
    def grafico_ventas_por_dia(self, ciclo_id: int) -> Optional[Path]:
        """
        Gráfico de número de ventas por día
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Path: Ruta del gráfico generado
        """
        # Obtener datos
        datos = db.execute_query("""
            SELECT 
                d.numero_dia,
                COUNT(v.id) as num_ventas
            FROM dias d
            LEFT JOIN ventas v ON d.id = v.dia_id
            WHERE d.ciclo_id = ? AND d.estado = 'cerrado'
            GROUP BY d.id
            ORDER BY d.numero_dia
        """, (ciclo_id,))
        
        if not datos:
            print("❌ No hay datos")
            return None
        
        dias = [d['numero_dia'] for d in datos]
        ventas = [d['num_ventas'] for d in datos]
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.bar(dias, ventas, color=self.colores['capital'], alpha=0.7)
        ax.set_xlabel('Día')
        ax.set_ylabel('Número de Ventas')
        ax.set_title(f'Ventas Realizadas por Día - Ciclo #{ciclo_id}')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Límites recomendados
        limites = queries.obtener_limites_ventas()
        ax.axhline(y=limites[0], color='green', linestyle='--', alpha=0.5,
                  label=f'Mínimo recomendado: {limites[0]}')
        ax.axhline(y=limites[1], color='red', linestyle='--', alpha=0.5,
                  label=f'Máximo recomendado: {limites[1]}')
        ax.legend()
        
        # Promedio
        promedio = sum(ventas) / len(ventas) if ventas else 0
        ax.text(0.02, 0.98, f'Promedio: {promedio:.1f} ventas/día',
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Guardar
        archivo = GRAFICOS_DIR / f"ciclo_{ciclo_id}_ventas_dia_{self.timestamp}.png"
        plt.tight_layout()
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfico de ventas generado: {archivo.name}")
        return archivo
    
    def grafico_distribucion_criptos(self, ciclo_id: int) -> Optional[Path]:
        """
        Gráfico de pastel de distribución de capital por cripto
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Path: Ruta del gráfico generado
        """
        criptos = queries.obtener_criptos_boveda(ciclo_id)
        
        if not criptos:
            print("❌ No hay criptos en bóveda")
            return None
        
        nombres = [f"{c['simbolo']}\n${c['valor_usd']:.2f}" for c in criptos]
        valores = [c['valor_usd'] for c in criptos]
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colores_pastel = plt.cm.Set3(range(len(criptos)))
        
        wedges, texts, autotexts = ax.pie(
            valores, 
            labels=nombres,
            autopct='%1.1f%%',
            colors=colores_pastel,
            startangle=90
        )
        
        # Mejorar legibilidad
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'Distribución de Capital por Cripto - Ciclo #{ciclo_id}')
        
        # Total
        total = sum(valores)
        plt.text(0, -1.3, f'Total: ${total:.2f}',
                ha='center', fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # Guardar
        archivo = GRAFICOS_DIR / f"ciclo_{ciclo_id}_distribucion_{self.timestamp}.png"
        plt.tight_layout()
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfico de distribución generado: {archivo.name}")
        return archivo
    
    # ===================================================================
    # DASHBOARD COMPLETO
    # ===================================================================
    
    def generar_dashboard_ciclo(self, ciclo_id: int) -> List[Path]:
        """
        Genera todos los gráficos de un ciclo
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Lista de archivos generados
        """
        print(f"\n📊 Generando dashboard completo del ciclo #{ciclo_id}...")
        
        archivos = []
        
        # Progreso
        archivo = self.grafico_progreso_ciclo(ciclo_id)
        if archivo:
            archivos.append(archivo)
        
        # ROI
        archivo = self.grafico_roi_ciclo(ciclo_id)
        if archivo:
            archivos.append(archivo)
        
        # Comisiones
        archivo = self.grafico_comisiones_ciclo(ciclo_id)
        if archivo:
            archivos.append(archivo)
        
        # Ventas por día
        archivo = self.grafico_ventas_por_dia(ciclo_id)
        if archivo:
            archivos.append(archivo)
        
        # Distribución
        archivo = self.grafico_distribucion_criptos(ciclo_id)
        if archivo:
            archivos.append(archivo)
        
        print(f"\n✅ {len(archivos)} gráfico(s) generado(s)")
        print(f"📂 Ubicación: {GRAFICOS_DIR.absolute()}")
        
        return archivos


# ===================================================================
# INTERFAZ DE USUARIO
# ===================================================================

def menu_graficos():
    """Menú de generación de gráficos"""
    
    generador = GeneradorGraficos()
    
    while True:
        print("\n" + "="*70)
        print("GENERADOR DE GRÁFICOS")
        print("="*70)
        print("[1] Dashboard completo de un ciclo")
        print("[2] Gráfico de progreso de ciclo")
        print("[3] Gráfico de ROI acumulado")
        print("[4] Gráfico de comisiones")
        print("[5] Gráfico de ventas por día")
        print("[6] Distribución de capital por cripto")
        print("[7] Comparativo de ciclos")
        print("[8] Eficiencia de ciclos")
        print("[9] Dashboard del ciclo activo")
        print("[10] Ver gráficos generados")
        print("[11] Volver")
        print("="*70)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.generar_dashboard_ciclo(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "2":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.grafico_progreso_ciclo(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "3":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.grafico_roi_ciclo(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "4":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.grafico_comisiones_ciclo(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "5":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.grafico_ventas_por_dia(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "6":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.grafico_distribucion_criptos(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "7":
            generador.grafico_comparativo_ciclos()
            input("\nPresiona Enter...")
        
        elif opcion == "8":
            generador.grafico_eficiencia_ciclos()
            input("\nPresiona Enter...")
        
        elif opcion == "9":
            ciclo = queries.obtener_ciclo_activo()
            if ciclo:
                generador.generar_dashboard_ciclo(ciclo['id'])
            else:
                print("\n❌ No hay ciclo activo")
            input("\nPresiona Enter...")
        
        elif opcion == "10":
            listar_graficos_generados()
            input("\nPresiona Enter...")
        
        elif opcion == "11":
            break
        
        else:
            print("❌ Opción inválida")


def listar_graficos_generados():
    """Lista todos los gráficos generados"""
    
    print("\n" + "="*70)
    print("GRÁFICOS GENERADOS")
    print("="*70)
    
    graficos = list(GRAFICOS_DIR.glob("*.png"))
    
    if not graficos:
        print("\n⚠️  No hay gráficos generados")
        return
    
    # Ordenar por fecha
    graficos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"\nTotal: {len(graficos)} gráfico(s)\n")
    
    for i, grafico in enumerate(graficos, 1):
        stat = grafico.stat()
        tamaño_kb = stat.st_size / 1024
        fecha = datetime.fromtimestamp(stat.st_mtime)
        
        print(f"[{i}] {grafico.name}")
        print(f"    Fecha: {fecha.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Tamaño: {tamaño_kb:.2f} KB")
        print(f"    Ruta: {grafico.absolute()}")
        print()
    
    print("="*70)


# ===================================================================
# VERIFICAR DEPENDENCIAS
# ===================================================================

def verificar_matplotlib():
    """Verifica si matplotlib está instalado"""
    try:
        import matplotlib
        return True
    except ImportError:
        print("\n❌ matplotlib no está instalado")
        print("\nPara instalar, ejecuta:")
        print("pip install matplotlib --break-system-packages")
        return False


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    if verificar_matplotlib():
        menu_graficos()
    else:
        print("\n⚠️  Instala matplotlib para usar este módulo")
