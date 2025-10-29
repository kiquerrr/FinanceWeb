# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE NOTAS
=============================================================================
Sistema de notas y observaciones para ciclos, días y operaciones
Permite documentar decisiones, incidentes y aprendizajes
"""

from datetime import datetime
from typing import Optional, List
from core.db_manager import db
from core.logger import log


# ===================================================================
# CREAR TABLA DE NOTAS
# ===================================================================

def inicializar_tabla_notas():
    """Crea la tabla de notas si no existe"""
    
    with db.get_cursor(commit=True) as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                referencia_id INTEGER,
                titulo TEXT NOT NULL,
                contenido TEXT NOT NULL,
                prioridad TEXT DEFAULT 'normal',
                etiquetas TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP,
                autor TEXT DEFAULT 'Operador'
            )
        """)
        
        # Índices para búsqueda rápida
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notas_tipo 
            ON notas(tipo)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notas_referencia 
            ON notas(tipo, referencia_id)
        """)
    
    log.info("Tabla de notas inicializada", categoria='general')


# Inicializar al importar
inicializar_tabla_notas()


# ===================================================================
# CLASE DE GESTIÓN DE NOTAS
# ===================================================================

class GestorNotas:
    """Gestiona notas y observaciones del sistema"""
    
    TIPOS_VALIDOS = ['ciclo', 'dia', 'venta', 'general', 'incidente', 'aprendizaje']
    PRIORIDADES = ['baja', 'normal', 'alta', 'urgente']
    
    # ===================================================================
    # CREAR NOTAS
    # ===================================================================
    
    @staticmethod
    def crear_nota(tipo: str, titulo: str, contenido: str, 
                   referencia_id: Optional[int] = None,
                   prioridad: str = 'normal',
                   etiquetas: Optional[List[str]] = None,
                   autor: str = 'Operador') -> int:
        """
        Crea una nueva nota
        
        Args:
            tipo: Tipo de nota (ciclo, dia, venta, general, etc)
            titulo: Título breve
            contenido: Contenido de la nota
            referencia_id: ID del elemento relacionado (ciclo_id, dia_id, etc)
            prioridad: baja, normal, alta, urgente
            etiquetas: Lista de etiquetas
            autor: Nombre del autor
        
        Returns:
            int: ID de la nota creada
        """
        if tipo not in GestorNotas.TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Debe ser uno de: {GestorNotas.TIPOS_VALIDOS}")
        
        if prioridad not in GestorNotas.PRIORIDADES:
            prioridad = 'normal'
        
        # Convertir etiquetas a texto
        etiquetas_str = ','.join(etiquetas) if etiquetas else ''
        
        nota_id = db.execute_update("""
            INSERT INTO notas (
                tipo, referencia_id, titulo, contenido, 
                prioridad, etiquetas, autor
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tipo, referencia_id, titulo, contenido, prioridad, etiquetas_str, autor))
        
        log.info(f"Nota creada: {titulo} (#{nota_id})", categoria='general')
        
        return nota_id
    
    @staticmethod
    def nota_ciclo(ciclo_id: int, titulo: str, contenido: str, 
                   prioridad: str = 'normal', etiquetas: Optional[List[str]] = None):
        """Crea nota asociada a un ciclo"""
        return GestorNotas.crear_nota('ciclo', titulo, contenido, ciclo_id, prioridad, etiquetas)
    
    @staticmethod
    def nota_dia(dia_id: int, titulo: str, contenido: str,
                 prioridad: str = 'normal', etiquetas: Optional[List[str]] = None):
        """Crea nota asociada a un día"""
        return GestorNotas.crear_nota('dia', titulo, contenido, dia_id, prioridad, etiquetas)
    
    @staticmethod
    def nota_incidente(titulo: str, contenido: str, 
                       referencia_id: Optional[int] = None,
                       etiquetas: Optional[List[str]] = None):
        """Crea nota de incidente (alta prioridad)"""
        return GestorNotas.crear_nota('incidente', titulo, contenido, 
                                      referencia_id, 'alta', etiquetas)
    
    @staticmethod
    def nota_aprendizaje(titulo: str, contenido: str,
                        referencia_id: Optional[int] = None,
                        etiquetas: Optional[List[str]] = None):
        """Crea nota de aprendizaje"""
        return GestorNotas.crear_nota('aprendizaje', titulo, contenido,
                                      referencia_id, 'normal', etiquetas)
    
    # ===================================================================
    # CONSULTAR NOTAS
    # ===================================================================
    
    @staticmethod
    def obtener_nota(nota_id: int):
        """Obtiene una nota por ID"""
        return db.execute_query(
            "SELECT * FROM notas WHERE id = ?",
            (nota_id,),
            fetch_one=True
        )
    
    @staticmethod
    def listar_notas(tipo: Optional[str] = None, 
                     referencia_id: Optional[int] = None,
                     prioridad: Optional[str] = None,
                     limite: int = 50):
        """
        Lista notas con filtros
        
        Args:
            tipo: Filtrar por tipo
            referencia_id: Filtrar por referencia
            prioridad: Filtrar por prioridad
            limite: Máximo de resultados
        
        Returns:
            Lista de notas
        """
        query = "SELECT * FROM notas WHERE 1=1"
        params = []
        
        if tipo:
            query += " AND tipo = ?"
            params.append(tipo)
        
        if referencia_id is not None:
            query += " AND referencia_id = ?"
            params.append(referencia_id)
        
        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad)
        
        query += " ORDER BY fecha_creacion DESC LIMIT ?"
        params.append(limite)
        
        return db.execute_query(query, tuple(params))
    
    @staticmethod
    def buscar_notas(termino: str):
        """Busca notas por término en título o contenido"""
        return db.execute_query("""
            SELECT * FROM notas
            WHERE titulo LIKE ? OR contenido LIKE ?
            ORDER BY fecha_creacion DESC
            LIMIT 50
        """, (f'%{termino}%', f'%{termino}%'))
    
    @staticmethod
    def obtener_notas_ciclo(ciclo_id: int):
        """Obtiene todas las notas de un ciclo"""
        return GestorNotas.listar_notas(tipo='ciclo', referencia_id=ciclo_id)
    
    @staticmethod
    def obtener_notas_dia(dia_id: int):
        """Obtiene todas las notas de un día"""
        return GestorNotas.listar_notas(tipo='dia', referencia_id=dia_id)
    
    @staticmethod
    def obtener_notas_prioritarias():
        """Obtiene notas de alta prioridad y urgentes"""
        return db.execute_query("""
            SELECT * FROM notas
            WHERE prioridad IN ('alta', 'urgente')
            ORDER BY 
                CASE prioridad
                    WHEN 'urgente' THEN 1
                    WHEN 'alta' THEN 2
                END,
                fecha_creacion DESC
            LIMIT 20
        """)
    
    # ===================================================================
    # ACTUALIZAR Y ELIMINAR
    # ===================================================================
    
    @staticmethod
    def actualizar_nota(nota_id: int, titulo: Optional[str] = None,
                       contenido: Optional[str] = None,
                       prioridad: Optional[str] = None):
        """Actualiza una nota existente"""
        
        nota = GestorNotas.obtener_nota(nota_id)
        if not nota:
            print(f"❌ Nota #{nota_id} no encontrada")
            return False
        
        campos = []
        valores = []
        
        if titulo:
            campos.append("titulo = ?")
            valores.append(titulo)
        
        if contenido:
            campos.append("contenido = ?")
            valores.append(contenido)
        
        if prioridad and prioridad in GestorNotas.PRIORIDADES:
            campos.append("prioridad = ?")
            valores.append(prioridad)
        
        if not campos:
            print("⚠️  No hay cambios para actualizar")
            return False
        
        campos.append("fecha_modificacion = datetime('now')")
        valores.append(nota_id)
        
        query = f"UPDATE notas SET {', '.join(campos)} WHERE id = ?"
        db.execute_update(query, tuple(valores))
        
        log.info(f"Nota #{nota_id} actualizada", categoria='general')
        return True
    
    @staticmethod
    def eliminar_nota(nota_id: int):
        """Elimina una nota"""
        db.execute_update("DELETE FROM notas WHERE id = ?", (nota_id,))
        log.info(f"Nota #{nota_id} eliminada", categoria='general')
        return True
    
    # ===================================================================
    # ESTADÍSTICAS
    # ===================================================================
    
    @staticmethod
    def obtener_estadisticas():
        """Obtiene estadísticas de notas"""
        with db.get_cursor(commit=False) as cursor:
            stats = {}
            
            # Total de notas
            cursor.execute("SELECT COUNT(*) as total FROM notas")
            stats['total'] = cursor.fetchone()['total']
            
            # Por tipo
            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad
                FROM notas
                GROUP BY tipo
            """)
            stats['por_tipo'] = {row['tipo']: row['cantidad'] for row in cursor.fetchall()}
            
            # Por prioridad
            cursor.execute("""
                SELECT prioridad, COUNT(*) as cantidad
                FROM notas
                GROUP BY prioridad
            """)
            stats['por_prioridad'] = {row['prioridad']: row['cantidad'] for row in cursor.fetchall()}
            
            return stats


# ===================================================================
# INTERFAZ DE USUARIO
# ===================================================================

def menu_notas():
    """Menú principal de gestión de notas"""
    
    gestor = GestorNotas()
    
    while True:
        print("\n" + "="*70)
        print("GESTIÓN DE NOTAS Y OBSERVACIONES")
        print("="*70)
        print("[1] Crear nueva nota")
        print("[2] Ver todas las notas")
        print("[3] Ver notas de un ciclo")
        print("[4] Ver notas de un día")
        print("[5] Ver notas prioritarias")
        print("[6] Buscar notas")
        print("[7] Registrar incidente")
        print("[8] Registrar aprendizaje")
        print("[9] Ver estadísticas")
        print("[10] Editar nota")
        print("[11] Eliminar nota")
        print("[12] Volver")
        print("="*70)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            crear_nota_interactivo(gestor)
        elif opcion == "2":
            ver_todas_notas(gestor)
        elif opcion == "3":
            ver_notas_ciclo_interactivo(gestor)
        elif opcion == "4":
            ver_notas_dia_interactivo(gestor)
        elif opcion == "5":
            ver_notas_prioritarias(gestor)
        elif opcion == "6":
            buscar_notas_interactivo(gestor)
        elif opcion == "7":
            registrar_incidente_interactivo(gestor)
        elif opcion == "8":
            registrar_aprendizaje_interactivo(gestor)
        elif opcion == "9":
            ver_estadisticas_notas(gestor)
        elif opcion == "10":
            editar_nota_interactivo(gestor)
        elif opcion == "11":
            eliminar_nota_interactivo(gestor)
        elif opcion == "12":
            break
        else:
            print("❌ Opción inválida")


def crear_nota_interactivo(gestor: GestorNotas):
    """Interfaz para crear nota"""
    
    print("\n" + "="*70)
    print("CREAR NUEVA NOTA")
    print("="*70)
    
    # Tipo
    print("\nTipo de nota:")
    for i, tipo in enumerate(gestor.TIPOS_VALIDOS, 1):
        print(f"  [{i}] {tipo.title()}")
    
    try:
        tipo_idx = int(input("\nSelecciona tipo: ")) - 1
        if tipo_idx < 0 or tipo_idx >= len(gestor.TIPOS_VALIDOS):
            print("❌ Tipo inválido")
            return
        tipo = gestor.TIPOS_VALIDOS[tipo_idx]
    except ValueError:
        print("❌ Selección inválida")
        return
    
    # Referencia (opcional)
    referencia_id = None
    if tipo in ['ciclo', 'dia']:
        ref = input(f"\nID del {tipo} (Enter para omitir): ").strip()
        if ref:
            try:
                referencia_id = int(ref)
            except ValueError:
                print("⚠️  ID inválido, se creará sin referencia")
    
    # Título
    titulo = input("\nTítulo: ").strip()
    if not titulo:
        print("❌ El título es obligatorio")
        return
    
    # Contenido
    print("\nContenido (termina con una línea vacía):")
    lineas = []
    while True:
        linea = input()
        if linea == "":
            break
        lineas.append(linea)
    contenido = "\n".join(lineas)
    
    if not contenido:
        print("❌ El contenido es obligatorio")
        return
    
    # Prioridad
    print("\nPrioridad:")
    for i, p in enumerate(gestor.PRIORIDADES, 1):
        print(f"  [{i}] {p.title()}")
    
    prioridad_input = input("\nSelecciona (Enter para 'normal'): ").strip()
    if prioridad_input:
        try:
            prioridad_idx = int(prioridad_input) - 1
            prioridad = gestor.PRIORIDADES[prioridad_idx]
        except (ValueError, IndexError):
            prioridad = 'normal'
    else:
        prioridad = 'normal'
    
    # Etiquetas
    etiquetas_input = input("\nEtiquetas (separadas por comas, opcional): ").strip()
    etiquetas = [e.strip() for e in etiquetas_input.split(',')] if etiquetas_input else None
    
    # Crear nota
    try:
        nota_id = gestor.crear_nota(tipo, titulo, contenido, referencia_id, prioridad, etiquetas)
        print(f"\n✅ Nota #{nota_id} creada exitosamente")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPresiona Enter...")


def ver_todas_notas(gestor: GestorNotas):
    """Ver todas las notas"""
    
    print("\n" + "="*70)
    print("TODAS LAS NOTAS")
    print("="*70)
    
    notas = gestor.listar_notas()
    
    if not notas:
        print("\n⚠️  No hay notas registradas")
    else:
        mostrar_lista_notas(notas)
    
    input("\nPresiona Enter...")


def ver_notas_ciclo_interactivo(gestor: GestorNotas):
    """Ver notas de un ciclo"""
    
    try:
        ciclo_id = int(input("\nID del ciclo: "))
        notas = gestor.obtener_notas_ciclo(ciclo_id)
        
        print(f"\n{'='*70}")
        print(f"NOTAS DEL CICLO #{ciclo_id}")
        print("="*70)
        
        if not notas:
            print("\n⚠️  No hay notas para este ciclo")
        else:
            mostrar_lista_notas(notas)
    except ValueError:
        print("❌ ID inválido")
    
    input("\nPresiona Enter...")


def ver_notas_dia_interactivo(gestor: GestorNotas):
    """Ver notas de un día"""
    
    try:
        dia_id = int(input("\nID del día: "))
        notas = gestor.obtener_notas_dia(dia_id)
        
        print(f"\n{'='*70}")
        print(f"NOTAS DEL DÍA #{dia_id}")
        print("="*70)
        
        if not notas:
            print("\n⚠️  No hay notas para este día")
        else:
            mostrar_lista_notas(notas)
    except ValueError:
        print("❌ ID inválido")
    
    input("\nPresiona Enter...")


def ver_notas_prioritarias(gestor: GestorNotas):
    """Ver notas prioritarias"""
    
    print("\n" + "="*70)
    print("NOTAS PRIORITARIAS (Alta/Urgente)")
    print("="*70)
    
    notas = gestor.obtener_notas_prioritarias()
    
    if not notas:
        print("\n✅ No hay notas prioritarias pendientes")
    else:
        mostrar_lista_notas(notas)
    
    input("\nPresiona Enter...")


def buscar_notas_interactivo(gestor: GestorNotas):
    """Buscar notas"""
    
    termino = input("\nTérmino de búsqueda: ").strip()
    if not termino:
        print("❌ Debes ingresar un término")
        return
    
    notas = gestor.buscar_notas(termino)
    
    print(f"\n{'='*70}")
    print(f"RESULTADOS PARA: '{termino}'")
    print("="*70)
    
    if not notas:
        print("\n⚠️  No se encontraron notas")
    else:
        print(f"\n{len(notas)} resultado(s):\n")
        mostrar_lista_notas(notas)
    
    input("\nPresiona Enter...")


def registrar_incidente_interactivo(gestor: GestorNotas):
    """Registrar incidente"""
    
    print("\n" + "="*70)
    print("REGISTRAR INCIDENTE")
    print("="*70)
    
    titulo = input("\nTítulo del incidente: ").strip()
    if not titulo:
        print("❌ El título es obligatorio")
        return
    
    print("\nDescripción del incidente:")
    lineas = []
    while True:
        linea = input()
        if linea == "":
            break
        lineas.append(linea)
    contenido = "\n".join(lineas)
    
    if not contenido:
        print("❌ La descripción es obligatoria")
        return
    
    ref = input("\nReferencia (ID ciclo/día, opcional): ").strip()
    referencia_id = int(ref) if ref else None
    
    try:
        nota_id = gestor.nota_incidente(titulo, contenido, referencia_id, ['incidente'])
        print(f"\n⚠️  Incidente #{nota_id} registrado (ALTA PRIORIDAD)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPresiona Enter...")


def registrar_aprendizaje_interactivo(gestor: GestorNotas):
    """Registrar aprendizaje"""
    
    print("\n" + "="*70)
    print("REGISTRAR APRENDIZAJE")
    print("="*70)
    
    titulo = input("\nTítulo: ").strip()
    if not titulo:
        print("❌ El título es obligatorio")
        return
    
    print("\n¿Qué aprendiste?:")
    lineas = []
    while True:
        linea = input()
        if linea == "":
            break
        lineas.append(linea)
    contenido = "\n".join(lineas)
    
    if not contenido:
        print("❌ El contenido es obligatorio")
        return
    
    try:
        nota_id = gestor.nota_aprendizaje(titulo, contenido, etiquetas=['aprendizaje'])
        print(f"\n📚 Aprendizaje #{nota_id} registrado")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPresiona Enter...")


def ver_estadisticas_notas(gestor: GestorNotas):
    """Ver estadísticas de notas"""
    
    print("\n" + "="*70)
    print("ESTADÍSTICAS DE NOTAS")
    print("="*70)
    
    stats = gestor.obtener_estadisticas()
    
    print(f"\n📊 Total de notas: {stats['total']}")
    
    if stats['por_tipo']:
        print("\n📝 Por tipo:")
        for tipo, cantidad in stats['por_tipo'].items():
            print(f"   {tipo.title()}: {cantidad}")
    
    if stats['por_prioridad']:
        print("\n🔔 Por prioridad:")
        for prioridad, cantidad in stats['por_prioridad'].items():
            emoji = {'urgente': '🚨', 'alta': '⚠️', 'normal': '📌', 'baja': '💬'}.get(prioridad, '📝')
            print(f"   {emoji} {prioridad.title()}: {cantidad}")
    
    print("="*70)
    
    input("\nPresiona Enter...")


def editar_nota_interactivo(gestor: GestorNotas):
    """Editar nota"""
    
    try:
        nota_id = int(input("\nID de la nota a editar: "))
        nota = gestor.obtener_nota(nota_id)
        
        if not nota:
            print(f"❌ Nota #{nota_id} no encontrada")
            return
        
        print(f"\n{'='*70}")
        print(f"EDITANDO NOTA #{nota_id}")
        print("="*70)
        print(f"\nTítulo actual: {nota['titulo']}")
        print(f"Contenido actual:\n{nota['contenido']}")
        print(f"Prioridad actual: {nota['prioridad']}")
        
        print("\n¿Qué deseas editar?")
        print("[1] Título")
        print("[2] Contenido")
        print("[3] Prioridad")
        print("[4] Cancelar")
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            nuevo_titulo = input("\nNuevo título: ").strip()
            if nuevo_titulo:
                gestor.actualizar_nota(nota_id, titulo=nuevo_titulo)
                print("✅ Título actualizado")
        
        elif opcion == "2":
            print("\nNuevo contenido (termina con línea vacía):")
            lineas = []
            while True:
                linea = input()
                if linea == "":
                    break
                lineas.append(linea)
            nuevo_contenido = "\n".join(lineas)
            if nuevo_contenido:
                gestor.actualizar_nota(nota_id, contenido=nuevo_contenido)
                print("✅ Contenido actualizado")
        
        elif opcion == "3":
            print("\nNueva prioridad:")
            for i, p in enumerate(gestor.PRIORIDADES, 1):
                print(f"  [{i}] {p.title()}")
            idx = int(input("\nSelecciona: ")) - 1
            if 0 <= idx < len(gestor.PRIORIDADES):
                gestor.actualizar_nota(nota_id, prioridad=gestor.PRIORIDADES[idx])
                print("✅ Prioridad actualizada")
        
    except ValueError:
        print("❌ ID inválido")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPresiona Enter...")


def eliminar_nota_interactivo(gestor: GestorNotas):
    """Eliminar nota"""
    
    try:
        nota_id = int(input("\nID de la nota a eliminar: "))
        nota = gestor.obtener_nota(nota_id)
        
        if not nota:
            print(f"❌ Nota #{nota_id} no encontrada")
            return
        
        print(f"\nNota a eliminar:")
        print(f"  Título: {nota['titulo']}")
        print(f"  Tipo: {nota['tipo']}")
        print(f"  Fecha: {nota['fecha_creacion']}")
        
        confirmar = input("\n¿Confirmar eliminación? (s/n): ").lower()
        if confirmar == 's':
            gestor.eliminar_nota(nota_id)
            print(f"✅ Nota #{nota_id} eliminada")
        else:
            print("❌ Eliminación cancelada")
    
    except ValueError:
        print("❌ ID inválido")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPresiona Enter...")


def mostrar_lista_notas(notas):
    """Muestra lista de notas formateada"""
    
    for nota in notas:
        # Emoji según prioridad
        emoji_prioridad = {
            'urgente': '🚨',
            'alta': '⚠️',
            'normal': '📌',
            'baja': '💬'
        }.get(nota['prioridad'], '📝')
        
        # Emoji según tipo
        emoji_tipo = {
            'ciclo': '🔄',
            'dia': '📅',
            'venta': '💰',
            'incidente': '⚠️',
            'aprendizaje': '📚',
            'general': '📝'
        }.get(nota['tipo'], '📝')
        
        print(f"\n{emoji_prioridad} {emoji_tipo} [{nota['id']}] {nota['titulo']}")
        print(f"   Tipo: {nota['tipo'].title()} | Prioridad: {nota['prioridad'].title()}")
        print(f"   Fecha: {nota['fecha_creacion']}")
        
        if nota['referencia_id']:
            print(f"   Referencia: {nota['tipo'].title()} #{nota['referencia_id']}")
        
        if nota['etiquetas']:
            print(f"   Etiquetas: {nota['etiquetas']}")
        
        # Mostrar preview del contenido
        contenido_preview = nota['contenido'][:100]
        if len(nota['contenido']) > 100:
            contenido_preview += "..."
        print(f"   {contenido_preview}")


# ===================================================================
# FUNCIONES RÁPIDAS
# ===================================================================

def nota_rapida(titulo: str, contenido: str):
    """Crea una nota rápida general"""
    gestor = GestorNotas()
    nota_id = gestor.crear_nota('general', titulo, contenido)
    print(f"✅ Nota rápida #{nota_id} creada")
    return nota_id


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    menu_notas()
