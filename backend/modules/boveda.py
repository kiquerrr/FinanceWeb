# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE BÓVEDA - Gestión de Capital y Compras (CORREGIDO)
=============================================================================
Maneja el fondeo, transferencias y consultas de la bóveda
✅ Ahora usa db_manager para conexiones seguras
"""

from datetime import datetime
from core.logger import log
from core.calculos import calc
from core.db_manager import db


# ===================================================================
# FUNCIONES DE CONSULTA
# ===================================================================

def consultar_boveda():
    """Consulta el estado actual de la bóveda"""
    
    print("\n" + "="*60)
    print("ESTADO ACTUAL DE LA BÓVEDA")
    print("="*60)
    
    with db.get_cursor(commit=False) as cursor:
        # Obtener todas las criptos con saldo
        cursor.execute("""
            SELECT 
                c.nombre,
                c.simbolo,
                bc.cantidad,
                bc.precio_promedio,
                (bc.cantidad * bc.precio_promedio) as valor_total
            FROM boveda_ciclo bc
            JOIN criptomonedas c ON bc.cripto_id = c.id
            WHERE bc.cantidad > 0
            ORDER BY valor_total DESC
        """)
        
        criptos = cursor.fetchall()
        
        if not criptos:
            print("\n⚠️  La bóveda está vacía")
            print("    Fondea la bóveda antes de operar")
            return
        
        print("\nCAPITAL TOTAL (Todas las criptos):")
        
        total_capital = 0
        
        for cripto in criptos:
            print(f"\n    {cripto['nombre']} ({cripto['simbolo']}):")
            print(f"    Cantidad: {cripto['cantidad']:.8f}")
            print(f"    Valor: ${cripto['valor_total']:.2f}")
            print(f"    Precio promedio: ${cripto['precio_promedio']:.4f}")
            total_capital += cripto['valor_total']
        
        print(f"\n    TOTAL EN FIAT: ${total_capital:.2f}")
        
        # Si hay ciclo activo, mostrar capital en ese ciclo
        from ciclos import obtener_ciclo_activo
        ciclo = obtener_ciclo_activo()
        
        if ciclo:
            print(f"\nCAPITAL EN CICLO ACTIVO (#{ciclo['id']}):")
            
            cursor.execute("""
                SELECT 
                    c.nombre,
                    c.simbolo,
                    bc.cantidad,
                    (bc.cantidad * bc.precio_promedio) as valor
                FROM boveda_ciclo bc
                JOIN criptomonedas c ON bc.cripto_id = c.id
                WHERE bc.ciclo_id = ? AND bc.cantidad > 0
            """, (ciclo['id'],))
            
            criptos_ciclo = cursor.fetchall()
            total_ciclo = 0
            
            for cripto in criptos_ciclo:
                print(f"\n    {cripto['nombre']} ({cripto['simbolo']}):")
                print(f"    Disponible: {cripto['cantidad']:.8f}")
                print(f"    Valor: ${cripto['valor']:.2f}")
                total_ciclo += cripto['valor']
            
            print(f"\n    TOTAL EN CICLO: ${total_ciclo:.2f}")
    
    print("="*60)


def listar_criptomonedas():
    """Lista todas las criptomonedas disponibles"""
    return db.execute_query("""
        SELECT id, nombre, simbolo, tipo, descripcion
        FROM criptomonedas
        ORDER BY tipo, nombre
    """)


# ===================================================================
# FONDEAR BÓVEDA
# ===================================================================

def fondear_boveda():
    """Registra una compra en la bóveda"""
    
    print("\n" + "="*60)
    print("FONDEAR BÓVEDA (REGISTRAR COMPRA)")
    print("="*60)
    
    # Obtener o crear ciclo activo
    from ciclos import obtener_ciclo_activo, crear_ciclo
    ciclo = obtener_ciclo_activo()
    
    if not ciclo:
        print("\n⚠️  No hay ciclo activo.")
        print("Para fondear la bóveda, primero debes crear un ciclo.")
        
        crear = input("\n¿Deseas crear un ciclo ahora? (s/n): ").lower()
        
        if crear == 's':
            try:
                dias = int(input("¿Cuántos días durará el ciclo? (15): ") or "15")
                ciclo_id = crear_ciclo(dias)
                
                if not ciclo_id:
                    print("❌ No se pudo crear el ciclo")
                    return
            except ValueError:
                print("❌ Valor inválido")
                return
        else:
            print("\n❌ No puedes fondear sin un ciclo activo")
            return
    else:
        ciclo_id = ciclo['id']
        print(f"\nRegistrando compra en el ciclo activo #{ciclo_id}")
    
    # Listar criptomonedas
    print("\n" + "="*60)
    print("CRIPTOMONEDAS DISPONIBLES")
    print("="*60)
    
    criptos = listar_criptomonedas()
    
    for i, cripto in enumerate(criptos, 1):
        icono = "$" if cripto['tipo'] == 'stablecoin' else "₿"
        print(f"\n{icono} [{i}] {cripto['nombre']} ({cripto['simbolo']})")
        print(f"    Tipo: {cripto['tipo'].title()}")
        print(f"    {cripto['descripcion']}")
    
    print("="*60)
    
    # Seleccionar criptomoneda
    try:
        print("\nSelecciona una opción (número): ", end='')
        seleccion = int(input())
        
        if seleccion < 1 or seleccion > len(criptos):
            print("❌ Selección inválida")
            return
        
        cripto_seleccionada = criptos[seleccion - 1]
        
        print(f"\nSeleccionaste: {cripto_seleccionada['nombre']} ({cripto_seleccionada['simbolo']})")
        
    except ValueError:
        print("\n❌ Ingresa un número válido.")
        return
    
    # Ingresar monto
    try:
        monto_usd = float(input("\nIngresa el monto que vas a invertir:\nMonto en USD: $"))
        
        if monto_usd <= 0:
            print("❌ Monto inválido")
            return
        
    except ValueError:
        print("❌ Monto inválido")
        return
    
    # Ingresar tasa de compra
    try:
        print(f"\nIngresa la tasa de compra de {cripto_seleccionada['simbolo']}:")
        print(f"    (Cuantos USD cuesta 1 {cripto_seleccionada['simbolo']}?)")
        tasa = float(input(f"1 {cripto_seleccionada['simbolo']} = $"))
        
        if tasa <= 0:
            print("❌ Tasa inválida")
            return
        
    except ValueError:
        print("❌ Tasa inválida")
        return
    
    # Calcular cantidad comprada
    cantidad = monto_usd / tasa
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("RESUMEN DE LA COMPRA")
    print("="*60)
    print(f"Criptomoneda: {cripto_seleccionada['nombre']} ({cripto_seleccionada['simbolo']})")
    print(f"Monto invertido: ${monto_usd:.2f} USD")
    print(f"Tasa de compra: 1 {cripto_seleccionada['simbolo']} = ${tasa:.4f}")
    print(f"Cantidad comprada: {cantidad:.8f} {cripto_seleccionada['simbolo']}")
    print(f"Precio unitario: ${tasa:.4f}")
    print("="*60)
    
    # Confirmar
    confirmar = input("\n¿Confirmar esta compra? (s/n): ").lower()
    
    if confirmar != 's':
        print("\n❌ Compra cancelada")
        return
    
    # Registrar compra
    registrar_compra(
        ciclo_id,
        cripto_seleccionada['id'],
        cantidad,
        monto_usd,
        tasa
    )


def registrar_compra(ciclo_id, cripto_id, cantidad, monto_usd, tasa):
    """Registra una compra en la base de datos"""
    
    try:
        with db.get_cursor(commit=False) as cursor:
            # Obtener info de la cripto
            cursor.execute("""
                SELECT nombre, simbolo FROM criptomonedas WHERE id = ?
            """, (cripto_id,))
            
            cripto = cursor.fetchone()
            
            if not cripto:
                print("❌ Criptomoneda no encontrada")
                return False
            
            # 1. Registrar compra en tabla de compras
            cursor.execute("""
                INSERT INTO compras (ciclo_id, cripto_id, cantidad, monto_usd, tasa, fecha)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (ciclo_id, cripto_id, cantidad, monto_usd, tasa))
            
            # 2. Verificar si ya existe en bóveda
            cursor.execute("""
                SELECT cantidad, precio_promedio
                FROM boveda_ciclo
                WHERE ciclo_id = ? AND cripto_id = ?
            """, (ciclo_id, cripto_id))
            
            boveda_actual = cursor.fetchone()
            
            if boveda_actual:
                # Ya existe, calcular nuevo promedio ponderado
                cantidad_anterior = boveda_actual['cantidad']
                precio_anterior = boveda_actual['precio_promedio']
                
                # Costo total anterior
                costo_anterior = cantidad_anterior * precio_anterior
                # Costo de nueva compra
                costo_nuevo = cantidad * tasa
                
                # Nueva cantidad total
                cantidad_total = cantidad_anterior + cantidad
                # Nuevo precio promedio ponderado
                precio_promedio_nuevo = (costo_anterior + costo_nuevo) / cantidad_total
                
                cursor.execute("""
                    UPDATE boveda_ciclo
                    SET cantidad = ?,
                        precio_promedio = ?
                    WHERE ciclo_id = ? AND cripto_id = ?
                """, (cantidad_total, precio_promedio_nuevo, ciclo_id, cripto_id))
                
                print(f"\n✅ Compra agregada a bóveda existente")
                print(f"   Cantidad anterior: {cantidad_anterior:.8f} {cripto['simbolo']}")
                print(f"   Precio anterior: ${precio_anterior:.4f}")
                print(f"   Nueva cantidad total: {cantidad_total:.8f} {cripto['simbolo']}")
                print(f"   Nuevo precio promedio: ${precio_promedio_nuevo:.4f}")
                
            else:
                # No existe, crear nuevo registro
                cursor.execute("""
                    INSERT INTO boveda_ciclo (ciclo_id, cripto_id, cantidad, precio_promedio)
                    VALUES (?, ?, ?, ?)
                """, (ciclo_id, cripto_id, cantidad, tasa))
                
                print(f"\n✅ Nueva cripto agregada a la bóveda")
                print(f"   Cantidad: {cantidad:.8f} {cripto['simbolo']}")
                print(f"   Precio promedio: ${tasa:.4f}")
            
            # Commit de la transacción
            cursor.connection.commit()
            
            # Registrar en log
            log.boveda_compra(
                cripto=cripto['nombre'],
                cantidad=cantidad,
                monto_usd=monto_usd,
                tasa=tasa,
                ciclo_id=ciclo_id
            )
            
            print(f"\n✅ Compra de {cantidad:.8f} {cripto['simbolo']} registrada exitosamente")
            return True
            
    except Exception as e:
        log.error("Error al registrar compra", str(e))
        print(f"\n❌ Error al registrar compra: {e}")
        return False


# ===================================================================
# HISTORIAL
# ===================================================================

def ver_historial():
    """Muestra el historial de todas las compras"""
    
    print("\n" + "="*60)
    print("HISTORIAL DE TRANSACCIONES")
    print("="*60)
    
    compras = db.execute_query("""
        SELECT 
            co.fecha,
            co.ciclo_id,
            cr.nombre,
            cr.simbolo,
            co.cantidad,
            co.monto_usd,
            co.tasa
        FROM compras co
        JOIN criptomonedas cr ON co.cripto_id = cr.id
        ORDER BY co.fecha DESC
        LIMIT 50
    """)
    
    if not compras:
        print("\n⚠️  No hay transacciones registradas")
        return
    
    print(f"\nÚltimas {len(compras)} transacciones:")
    
    for compra in compras:
        fecha = datetime.strptime(compra['fecha'], '%Y-%m-%d %H:%M:%S')
        print(f"\n🗓️ {fecha.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Ciclo #{compra['ciclo_id']}")
        print(f"    Compra: {compra['cantidad']:.8f} {compra['simbolo']}")
        print(f"    Monto: ${compra['monto_usd']:.2f}")
        print(f"    Tasa: 1 {compra['simbolo']} = ${compra['tasa']:.4f}")
    
    print("="*60)


# ===================================================================
# TRANSFERIR CAPITAL
# ===================================================================

def transferir_capital():
    """Transfiere capital entre ciclos"""
    
    print("\n" + "="*60)
    print("TRANSFERIR CAPITAL AL CICLO ACTIVO")
    print("="*60)
    
    # Verificar ciclo activo
    from ciclos import obtener_ciclo_activo
    ciclo = obtener_ciclo_activo()
    
    if not ciclo:
        print("\n❌ No hay ciclo activo")
        print("    Crea un ciclo antes de transferir capital")
        return
    
    print(f"\nCiclo activo: #{ciclo['id']}")
    
    # Mostrar capital disponible en otros ciclos
    with db.get_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                bc.ciclo_id,
                c.nombre,
                c.simbolo,
                c.id as cripto_id,
                bc.cantidad,
                bc.precio_promedio
            FROM boveda_ciclo bc
            JOIN criptomonedas c ON bc.cripto_id = c.id
            WHERE bc.ciclo_id != ? AND bc.cantidad > 0
            ORDER BY bc.ciclo_id, c.nombre
        """, (ciclo['id'],))
        
        capital_otros = cursor.fetchall()
    
    if not capital_otros:
        print("\n⚠️  No hay capital en otros ciclos para transferir")
        return
    
    print("\nCapital disponible en otros ciclos:")
    
    for i, item in enumerate(capital_otros, 1):
        valor = item['cantidad'] * item['precio_promedio']
        print(f"\n[{i}] Ciclo #{item['ciclo_id']} - {item['nombre']} ({item['simbolo']})")
        print(f"    Cantidad: {item['cantidad']:.8f}")
        print(f"    Valor: ${valor:.2f}")
    
    # Seleccionar cripto a transferir
    try:
        seleccion = int(input("\n¿Qué cripto deseas transferir? (número): ")) - 1
        
        if seleccion < 0 or seleccion >= len(capital_otros):
            print("❌ Selección inválida")
            return
        
        cripto_seleccionada = capital_otros[seleccion]
        
        # Preguntar cantidad
        print(f"\nTransfiriendo {cripto_seleccionada['nombre']} del Ciclo #{cripto_seleccionada['ciclo_id']} al Ciclo #{ciclo['id']}")
        print(f"Disponible: {cripto_seleccionada['cantidad']:.8f}")
        
        cantidad_input = input("\n¿Cuánto deseas transferir? (o 'todo'): ").strip().lower()
        
        if cantidad_input == 'todo':
            cantidad = cripto_seleccionada['cantidad']
        else:
            cantidad = float(cantidad_input)
            
            if cantidad <= 0 or cantidad > cripto_seleccionada['cantidad']:
                print("❌ Cantidad inválida")
                return
        
        # Confirmar
        valor_transfer = cantidad * cripto_seleccionada['precio_promedio']
        print(f"\n📄 RESUMEN DE TRANSFERENCIA:")
        print(f"    Cripto: {cripto_seleccionada['nombre']}")
        print(f"    Cantidad: {cantidad:.8f}")
        print(f"    Valor: ${valor_transfer:.2f}")
        print(f"    Desde: Ciclo #{cripto_seleccionada['ciclo_id']}")
        print(f"    Hacia: Ciclo #{ciclo['id']}")
        
        confirmar = input("\n¿Confirmar transferencia? (s/n): ").lower()
        
        if confirmar != 's':
            print("❌ Transferencia cancelada")
            return
        
        # Realizar transferencia usando transacción
        with db.transaction() as conn:
            cursor = conn.cursor()
            
            # 1. Restar del ciclo origen
            cursor.execute("""
                UPDATE boveda_ciclo
                SET cantidad = cantidad - ?
                WHERE ciclo_id = ? AND cripto_id = ?
            """, (cantidad, cripto_seleccionada['ciclo_id'], cripto_seleccionada['cripto_id']))
            
            # 2. Verificar si existe en ciclo destino
            cursor.execute("""
                SELECT cantidad, precio_promedio
                FROM boveda_ciclo
                WHERE ciclo_id = ? AND cripto_id = ?
            """, (ciclo['id'], cripto_seleccionada['cripto_id']))
            
            destino_actual = cursor.fetchone()
            
            if destino_actual:
                # Ya existe, calcular nuevo promedio
                cant_anterior = destino_actual['cantidad']
                precio_anterior = destino_actual['precio_promedio']
                
                costo_anterior = cant_anterior * precio_anterior
                costo_nuevo = cantidad * cripto_seleccionada['precio_promedio']
                
                cantidad_total = cant_anterior + cantidad
                precio_promedio_nuevo = (costo_anterior + costo_nuevo) / cantidad_total 
                
                cursor.execute("""
                    UPDATE boveda_ciclo
                    SET cantidad = ?,
                        precio_promedio = ?
                    WHERE ciclo_id = ? AND cripto_id = ?
                """, (cantidad_total, precio_promedio_nuevo, ciclo['id'], cripto_seleccionada['cripto_id']))
                
            else:
                # No existe, insertar nuevo registro
                cursor.execute("""
                    INSERT INTO boveda_ciclo (ciclo_id, cripto_id, cantidad, precio_promedio)
                    VALUES (?, ?, ?, ?)
                """, (ciclo['id'], cripto_seleccionada['cripto_id'], cantidad, cripto_seleccionada['precio_promedio']))
            
            # Commit automático al salir del context manager
        
        # Registrar en log
        log.boveda_transferencia(
            cripto=cripto_seleccionada['nombre'],
            cantidad=cantidad,
            valor_usd=valor_transfer,
            origen=cripto_seleccionada['ciclo_id'],
            destino=ciclo['id']
        )
        
        print(f"\n✅ Transferencia de capital exitosa!")
        print(f"    {cantidad:.8f} {cripto_seleccionada['simbolo']} transferidos del ciclo #{cripto_seleccionada['ciclo_id']} al ciclo #{ciclo['id']}.")
        
    except ValueError:
        print("❌ Entrada inválida (debe ser un número o 'todo').")
    except Exception as e:
        log.error("Error al transferir capital", str(e))
        print(f"❌ Ocurrió un error inesperado: {e}")


# ===================================================================
# MENÚ DE BÓVEDA
# ===================================================================

def menu_boveda():
    """Menú principal de gestión de bóveda"""
    
    while True:
        print("\n" + "="*60)
        print("GESTIÓN DE BÓVEDA") 
        print("="*60)
        print("[1] Consultar Estado de la Bóveda") 
        print("[2] Fondear Bóveda (Registrar Compra)")
        print("[3] Ver Historial de Transacciones")
        print("[4] Transferir Capital al Ciclo Activo")
        print("[5] Volver al Menú Principal") 
        print("="*60)
        
        opcion = input("Selecciona una opción: ").strip() 
        
        if opcion == "1":
            consultar_boveda()
            input("\nPresiona Enter para volver...")
        
        elif opcion == "2":
            fondear_boveda()
            input("\nPresiona Enter para continuar...")
        
        elif opcion == "3":
            ver_historial()
            input("\nPresiona Enter para volver...")
        
        elif opcion == "4":
            transferir_capital()
            input("\nPresiona Enter para volver...")
        
        elif opcion == "5":
            break
        
        else:
            print("❌ Opción inválida")


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    menu_boveda()
