# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE REPORTES
=============================================================================
Genera reportes detallados en diferentes formatos
Exporta datos a CSV, TXT y genera resúmenes ejecutivos
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from core.db_manager import db
from core.queries import queries


# ===================================================================
# DIRECTORIOS
# ===================================================================

REPORTES_DIR = Path("reportes")
REPORTES_DIR.mkdir(exist_ok=True)


# ===================================================================
# GENERADOR DE REPORTES
# ===================================================================

class GeneradorReportes:
    """Genera reportes en diferentes formatos"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ===================================================================
    # REPORTES DE CICLO
    # ===================================================================
    
    def generar_reporte_ciclo_txt(self, ciclo_id: int) -> Optional[Path]:
        """
        Genera reporte completo de un ciclo en formato TXT
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Path: Ruta del archivo generado
        """
        # Obtener datos del ciclo
        ciclo = queries.obtener_ciclo_por_id(ciclo_id)
        if not ciclo:
            print(f"❌ Ciclo #{ciclo_id} no encontrado")
            return None
        
        # Obtener días del ciclo
        dias = db.execute_query("""
            SELECT * FROM dias
            WHERE ciclo_id = ?
            ORDER BY numero_dia
        """, (ciclo_id,))
        
        # Crear archivo
        archivo = REPORTES_DIR / f"reporte_ciclo_{ciclo_id}_{self.timestamp}.txt"
        
        with open(archivo, 'w', encoding='utf-8') as f:
            # Encabezado
            f.write("="*70 + "\n")
            f.write(f"REPORTE COMPLETO - CICLO #{ciclo_id}\n")
            f.write("="*70 + "\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            # Información general del ciclo
            f.write("📊 INFORMACIÓN GENERAL\n")
            f.write("-"*70 + "\n")
            f.write(f"Estado: {ciclo['estado'].upper()}\n")
            f.write(f"Fecha inicio: {ciclo['fecha_inicio']}\n")
            f.write(f"Fecha fin estimada: {ciclo['fecha_fin_estimada']}\n")
            if ciclo['fecha_cierre']:
                f.write(f"Fecha cierre real: {ciclo['fecha_cierre']}\n")
            f.write(f"Días planificados: {ciclo['dias_planificados']}\n")
            f.write(f"Días operados: {ciclo['dias_operados']}\n")
            f.write(f"Inversión inicial: ${ciclo['inversion_inicial']:.2f}\n")
            
            if ciclo['estado'] == 'cerrado':
                f.write(f"Capital final: ${ciclo['capital_final']:.2f}\n")
                f.write(f"Ganancia total: ${ciclo['ganancia_total']:.2f}\n")
                f.write(f"ROI: {ciclo['roi_total']:.2f}%\n")
            
            f.write("\n")
            
            # Estadísticas generales
            stats = db.execute_query("""
                SELECT 
                    COUNT(*) as total_dias,
                    COALESCE(SUM(ganancia_neta), 0) as ganancia_total,
                    COALESCE(AVG(ganancia_neta), 0) as ganancia_promedio,
                    COALESCE(MAX(ganancia_neta), 0) as mejor_dia,
                    COALESCE(MIN(ganancia_neta), 0) as peor_dia
                FROM dias
                WHERE ciclo_id = ? AND estado = 'cerrado'
            """, (ciclo_id,), fetch_one=True)
            
            if stats['total_dias'] > 0:
                f.write("📈 ESTADÍSTICAS\n")
                f.write("-"*70 + "\n")
                f.write(f"Ganancia promedio por día: ${stats['ganancia_promedio']:.2f}\n")
                f.write(f"Mejor día: ${stats['mejor_dia']:.2f}\n")
                f.write(f"Peor día: ${stats['peor_dia']:.2f}\n")
                f.write(f"Ganancia total acumulada: ${stats['ganancia_total']:.2f}\n")
                f.write("\n")
            
            # Detalle de días
            if dias:
                f.write("📅 DETALLE DE DÍAS\n")
                f.write("="*70 + "\n\n")
                
                for dia in dias:
                    f.write(f"DÍA #{dia['numero_dia']} - {dia['fecha']}\n")
                    f.write("-"*70 + "\n")
                    f.write(f"Estado: {dia['estado'].upper()}\n")
                    f.write(f"Capital inicial: ${dia['capital_inicial']:.2f}\n")
                    
                    if dia['estado'] == 'cerrado':
                        f.write(f"Capital final: ${dia['capital_final']:.2f}\n")
                        f.write(f"Ganancia neta: ${dia['ganancia_neta']:.2f}\n")
                        f.write(f"Comisiones: ${dia['comisiones_pagadas']:.2f}\n")
                        
                        # Ventas del día
                        ventas = queries.obtener_ventas_dia(dia['id'])
                        f.write(f"Ventas realizadas: {len(ventas)}\n")
                        
                        if ventas:
                            f.write("\n  VENTAS:\n")
                            for i, venta in enumerate(ventas, 1):
                                f.write(f"    [{i}] {venta['cantidad']:.8f} {venta['simbolo']} ")
                                f.write(f"@ ${venta['precio_unitario']:.4f} = ")
                                f.write(f"${venta['efectivo_recibido']:.2f}\n")
                    
                    f.write("\n")
            
            # Capital en bóveda
            criptos_boveda = queries.obtener_criptos_boveda(ciclo_id)
            
            if criptos_boveda:
                f.write("💰 CAPITAL EN BÓVEDA\n")
                f.write("="*70 + "\n")
                
                total_boveda = 0
                for cripto in criptos_boveda:
                    f.write(f"{cripto['nombre']} ({cripto['simbolo']})\n")
                    f.write(f"  Cantidad: {cripto['cantidad']:.8f}\n")
                    f.write(f"  Precio promedio: ${cripto['precio_promedio']:.4f}\n")
                    f.write(f"  Valor total: ${cripto['valor_usd']:.2f}\n\n")
                    total_boveda += cripto['valor_usd']
                
                f.write("-"*70 + "\n")
                f.write(f"TOTAL EN BÓVEDA: ${total_boveda:.2f}\n")
            
            f.write("\n")
            f.write("="*70 + "\n")
            f.write("FIN DEL REPORTE\n")
            f.write("="*70 + "\n")
        
        print(f"✅ Reporte generado: {archivo.name}")
        return archivo
    
    def generar_reporte_ciclo_csv(self, ciclo_id: int) -> Optional[Path]:
        """
        Genera reporte de días en formato CSV
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Path: Ruta del archivo generado
        """
        dias = db.execute_query("""
            SELECT * FROM dias
            WHERE ciclo_id = ?
            ORDER BY numero_dia
        """, (ciclo_id,))
        
        if not dias:
            print(f"❌ No hay días en el ciclo #{ciclo_id}")
            return None
        
        archivo = REPORTES_DIR / f"ciclo_{ciclo_id}_dias_{self.timestamp}.csv"
        
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Encabezados
            writer.writerow([
                'Día', 'Fecha', 'Estado', 'Capital Inicial', 'Capital Final',
                'Ganancia Neta', 'Comisiones', 'Efectivo Recibido', 'Ventas'
            ])
            
            # Datos
            for dia in dias:
                num_ventas = queries.contar_ventas_dia(dia['id'])
                
                writer.writerow([
                    dia['numero_dia'],
                    dia['fecha'],
                    dia['estado'],
                    f"{dia['capital_inicial']:.2f}",
                    f"{dia['capital_final']:.2f}" if dia['capital_final'] else "",
                    f"{dia['ganancia_neta']:.2f}" if dia['ganancia_neta'] else "",
                    f"{dia['comisiones_pagadas']:.2f}" if dia['comisiones_pagadas'] else "",
                    f"{dia['efectivo_recibido']:.2f}" if dia['efectivo_recibido'] else "",
                    num_ventas
                ])
        
        print(f"✅ Reporte CSV generado: {archivo.name}")
        return archivo
    
    # ===================================================================
    # REPORTES DE VENTAS
    # ===================================================================
    
    def generar_reporte_ventas_csv(self, ciclo_id: int) -> Optional[Path]:
        """
        Genera reporte de todas las ventas del ciclo en CSV
        
        Args:
            ciclo_id: ID del ciclo
        
        Returns:
            Path: Ruta del archivo generado
        """
        ventas = db.execute_query("""
            SELECT 
                d.numero_dia,
                d.fecha,
                c.nombre as cripto,
                c.simbolo,
                v.cantidad,
                v.precio_unitario,
                v.costo_total,
                v.monto_venta,
                v.comision,
                v.efectivo_recibido,
                v.ganancia_bruta,
                v.ganancia_neta
            FROM ventas v
            JOIN dias d ON v.dia_id = d.id
            JOIN criptomonedas c ON v.cripto_id = c.id
            WHERE d.ciclo_id = ?
            ORDER BY d.numero_dia, v.fecha
        """, (ciclo_id,))
        
        if not ventas:
            print(f"❌ No hay ventas en el ciclo #{ciclo_id}")
            return None
        
        archivo = REPORTES_DIR / f"ciclo_{ciclo_id}_ventas_{self.timestamp}.csv"
        
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Encabezados
            writer.writerow([
                'Día', 'Fecha', 'Cripto', 'Símbolo', 'Cantidad', 'Precio Unitario',
                'Costo Total', 'Monto Venta', 'Comisión', 'Efectivo Recibido',
                'Ganancia Bruta', 'Ganancia Neta'
            ])
            
            # Datos
            for venta in ventas:
                writer.writerow([
                    venta['numero_dia'],
                    venta['fecha'],
                    venta['cripto'],
                    venta['simbolo'],
                    f"{venta['cantidad']:.8f}",
                    f"{venta['precio_unitario']:.4f}",
                    f"{venta['costo_total']:.2f}",
                    f"{venta['monto_venta']:.2f}",
                    f"{venta['comision']:.2f}",
                    f"{venta['efectivo_recibido']:.2f}",
                    f"{venta['ganancia_bruta']:.2f}",
                    f"{venta['ganancia_neta']:.2f}"
                ])
        
        print(f"✅ Reporte de ventas generado: {archivo.name}")
        return archivo
    
    # ===================================================================
    # REPORTE CONSOLIDADO
    # ===================================================================
    
    def generar_reporte_consolidado(self) -> Optional[Path]:
        """
        Genera reporte consolidado de todos los ciclos
        
        Returns:
            Path: Ruta del archivo generado
        """
        ciclos = db.execute_query("""
            SELECT * FROM ciclos
            ORDER BY id DESC
        """)
        
        if not ciclos:
            print("❌ No hay ciclos registrados")
            return None
        
        archivo = REPORTES_DIR / f"reporte_consolidado_{self.timestamp}.txt"
        
        with open(archivo, 'w', encoding='utf-8') as f:
            # Encabezado
            f.write("="*70 + "\n")
            f.write("REPORTE CONSOLIDADO - TODOS LOS CICLOS\n")
            f.write("="*70 + "\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            # Estadísticas generales
            stats = queries.obtener_estadisticas_generales()
            
            f.write("📊 RESUMEN GENERAL\n")
            f.write("-"*70 + "\n")
            f.write(f"Total de ciclos: {stats['total_ciclos']}\n")
            f.write(f"Ciclos activos: {stats['ciclos_activos']}\n")
            f.write(f"Días operados: {stats['dias_operados']}\n")
            f.write(f"Total de ventas: {stats['total_ventas']}\n")
            f.write(f"Total de compras: {stats['total_compras']}\n")
            f.write(f"Capital invertido: ${stats['capital_invertido']:.2f}\n")
            f.write(f"Ganancia total: ${stats['ganancia_total']:.2f}\n")
            
            if stats['capital_invertido'] > 0:
                roi_global = (stats['ganancia_total'] / stats['capital_invertido']) * 100
                f.write(f"ROI global: {roi_global:.2f}%\n")
            
            f.write("\n")
            
            # Detalle por ciclo
            f.write("📅 DETALLE POR CICLO\n")
            f.write("="*70 + "\n\n")
            
            for ciclo in ciclos:
                estado_emoji = "🔄" if ciclo['estado'] == 'activo' else "✅"
                
                f.write(f"{estado_emoji} CICLO #{ciclo['id']} - {ciclo['estado'].upper()}\n")
                f.write("-"*70 + "\n")
                f.write(f"Período: {ciclo['fecha_inicio']} → {ciclo['fecha_fin_estimada']}\n")
                f.write(f"Días: {ciclo['dias_operados']}/{ciclo['dias_planificados']}\n")
                f.write(f"Inversión inicial: ${ciclo['inversion_inicial']:.2f}\n")
                
                if ciclo['estado'] == 'cerrado':
                    f.write(f"Capital final: ${ciclo['capital_final']:.2f}\n")
                    f.write(f"Ganancia: ${ciclo['ganancia_total']:.2f}\n")
                    f.write(f"ROI: {ciclo['roi_total']:.2f}%\n")
                    
                    # Rendimiento diario promedio
                    if ciclo['dias_operados'] > 0:
                        ganancia_diaria = ciclo['ganancia_total'] / ciclo['dias_operados']
                        f.write(f"Ganancia diaria promedio: ${ganancia_diaria:.2f}\n")
                
                f.write("\n")
            
            f.write("="*70 + "\n")
            f.write("FIN DEL REPORTE\n")
            f.write("="*70 + "\n")
        
        print(f"✅ Reporte consolidado generado: {archivo.name}")
        return archivo
    
    # ===================================================================
    # REPORTE DE RENDIMIENTO
    # ===================================================================
    
    def generar_reporte_rendimiento_csv(self) -> Optional[Path]:
        """
        Genera CSV con métricas de rendimiento por ciclo
        
        Returns:
            Path: Ruta del archivo generado
        """
        ciclos = db.execute_query("""
            SELECT * FROM ciclos
            WHERE estado = 'cerrado'
            ORDER BY id
        """)
        
        if not ciclos:
            print("❌ No hay ciclos cerrados")
            return None
        
        archivo = REPORTES_DIR / f"rendimiento_ciclos_{self.timestamp}.csv"
        
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Encabezados
            writer.writerow([
                'Ciclo', 'Fecha Inicio', 'Fecha Fin', 'Días Operados',
                'Inversión Inicial', 'Capital Final', 'Ganancia Total',
                'ROI %', 'Ganancia Diaria Promedio', 'ROI Diario Promedio %'
            ])
            
            # Datos
            for ciclo in ciclos:
                ganancia_diaria = ciclo['ganancia_total'] / ciclo['dias_operados'] if ciclo['dias_operados'] > 0 else 0
                roi_diario = ciclo['roi_total'] / ciclo['dias_operados'] if ciclo['dias_operados'] > 0 else 0
                
                writer.writerow([
                    ciclo['id'],
                    ciclo['fecha_inicio'],
                    ciclo['fecha_cierre'],
                    ciclo['dias_operados'],
                    f"{ciclo['inversion_inicial']:.2f}",
                    f"{ciclo['capital_final']:.2f}",
                    f"{ciclo['ganancia_total']:.2f}",
                    f"{ciclo['roi_total']:.2f}",
                    f"{ganancia_diaria:.2f}",
                    f"{roi_diario:.2f}"
                ])
        
        print(f"✅ Reporte de rendimiento generado: {archivo.name}")
        return archivo


# ===================================================================
# MENÚ INTERACTIVO
# ===================================================================

def menu_reportes():
    """Menú de generación de reportes"""
    
    generador = GeneradorReportes()
    
    while True:
        print("\n" + "="*70)
        print("GENERADOR DE REPORTES")
        print("="*70)
        print("[1] Reporte completo de un ciclo (TXT)")
        print("[2] Reporte de días de un ciclo (CSV)")
        print("[3] Reporte de ventas de un ciclo (CSV)")
        print("[4] Reporte consolidado de todos los ciclos (TXT)")
        print("[5] Reporte de rendimiento (CSV)")
        print("[6] Generar todos los reportes del ciclo activo")
        print("[7] Ver reportes generados")
        print("[8] Volver")
        print("="*70)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.generar_reporte_ciclo_txt(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "2":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.generar_reporte_ciclo_csv(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "3":
            try:
                ciclo_id = int(input("\nID del ciclo: "))
                generador.generar_reporte_ventas_csv(ciclo_id)
            except ValueError:
                print("❌ ID inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "4":
            generador.generar_reporte_consolidado()
            input("\nPresiona Enter...")
        
        elif opcion == "5":
            generador.generar_reporte_rendimiento_csv()
            input("\nPresiona Enter...")
        
        elif opcion == "6":
            ciclo = queries.obtener_ciclo_activo()
            if ciclo:
                print(f"\nGenerando reportes del ciclo activo #{ciclo['id']}...")
                generador.generar_reporte_ciclo_txt(ciclo['id'])
                generador.generar_reporte_ciclo_csv(ciclo['id'])
                generador.generar_reporte_ventas_csv(ciclo['id'])
                print("\n✅ Todos los reportes generados")
            else:
                print("\n❌ No hay ciclo activo")
            input("\nPresiona Enter...")
        
        elif opcion == "7":
            listar_reportes_generados()
            input("\nPresiona Enter...")
        
        elif opcion == "8":
            break
        
        else:
            print("❌ Opción inválida")


def listar_reportes_generados():
    """Lista todos los reportes generados"""
    
    print("\n" + "="*70)
    print("REPORTES GENERADOS")
    print("="*70)
    
    reportes = list(REPORTES_DIR.glob("*"))
    
    if not reportes:
        print("\n⚠️  No hay reportes generados")
        return
    
    # Ordenar por fecha de modificación (más reciente primero)
    reportes.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"\nTotal: {len(reportes)} archivo(s)\n")
    
    for i, reporte in enumerate(reportes, 1):
        stat = reporte.stat()
        tamaño_kb = stat.st_size / 1024
        fecha = datetime.fromtimestamp(stat.st_mtime)
        
        print(f"[{i}] {reporte.name}")
        print(f"    Fecha: {fecha.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Tamaño: {tamaño_kb:.2f} KB")
        print(f"    Ruta: {reporte.absolute()}")
        print()
    
    print("="*70)


# ===================================================================
# FUNCIONES DE EXPORTACIÓN RÁPIDA
# ===================================================================

def exportar_ciclo_completo(ciclo_id: int):
    """Exporta todos los reportes de un ciclo"""
    generador = GeneradorReportes()
    
    print(f"\n📄 Generando reportes del ciclo #{ciclo_id}...\n")
    
    archivos = []
    
    # TXT completo
    archivo = generador.generar_reporte_ciclo_txt(ciclo_id)
    if archivo:
        archivos.append(archivo)
    
    # CSV días
    archivo = generador.generar_reporte_ciclo_csv(ciclo_id)
    if archivo:
        archivos.append(archivo)
    
    # CSV ventas
    archivo = generador.generar_reporte_ventas_csv(ciclo_id)
    if archivo:
        archivos.append(archivo)
    
    if archivos:
        print(f"\n✅ {len(archivos)} reporte(s) generado(s):")
        for archivo in archivos:
            print(f"   📁 {archivo.name}")
        print(f"\n📂 Ubicación: {REPORTES_DIR.absolute()}")
    
    return archivos


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    menu_reportes()
