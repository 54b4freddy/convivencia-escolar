from collections import Counter


AREAS_MEJORA = {
    'Llegar tarde al aula de clase':          ('Gestión del tiempo y puntualidad',
        'Implementar rutinas de inicio de clase motivadoras y revisar factores externos como transporte.'),
    'No portar el uniforme completo':          ('Sentido de pertenencia institucional',
        'Fortalecer el vínculo identitario con el colegio mediante actividades de comunidad.'),
    'Uso inadecuado del celular en clase':    ('Competencia digital y autorregulación',
        'Diseñar acuerdos de uso responsable del celular e integrar la tecnología pedagógicamente.'),
    'Vocabulario inapropiado':                ('Comunicación asertiva y empatía',
        'Talleres de habilidades comunicativas y resolución pacífica de conflictos.'),
    'Agresión verbal a compañeros':           ('Convivencia y habilidades sociales',
        'Programa de mediación entre pares. Fortalecer la inteligencia emocional en el grupo.'),
    'Daño a propiedad de la institución':     ('Responsabilidad y cuidado del entorno',
        'Proyecto de apropiación del espacio escolar. Acciones de reparación simbólica.'),
    'Falsificación de firmas o documentos':   ('Honestidad y valores ciudadanos',
        'Trabajar el valor de la honestidad desde el currículo transversal y proyecto de vida.'),
    'Agresión física':                        ('Manejo de emociones y resolución de conflictos',
        'Intervención psicosocial urgente. Programa de manejo de ira y mediación.'),
    'Porte de sustancias psicoactivas':       ('Prevención de consumo y proyecto de vida',
        'Activar la Ruta de Atención Integral. Talleres de proyecto de vida y factores protectores.'),
    'Acoso escolar comprobado':               ('Clima escolar y dinámicas grupales',
        'Aplicar sociograma del curso. Intervención sistémica con grupo, acosador y víctima.'),
}


def generar_sugerencias(faltas):
    """
    Analiza el patrón de faltas y genera sugerencias de mejoramiento
    priorizando por frecuencia y gravedad.
    """
    cnt = Counter()
    for f in faltas:
        cnt[f.get('falta_especifica', '')] += 1

    sugerencias = []
    areas_vistas = set()

    # Reincidencias tipo I → sugerir proceso tipo II
    t1_por_est = Counter(f.get('estudiante', '') for f in faltas if f.get('tipo_falta') == 'Tipo I')
    reincidentes_t1 = [e for e, n in t1_por_est.items() if n >= 3]
    if reincidentes_t1:
        sugerencias.append(
            f'ALERTA REINCIDENCIA: {", ".join(reincidentes_t1)} acumulan 3+ faltas Tipo I. '
            f'Activar proceso Tipo II: citación de acudiente y compromiso formal.')

    # Top faltas → sugerencia pedagógica
    for falta, n in cnt.most_common(5):
        if n < 2:
            continue
        area = AREAS_MEJORA.get(falta)
        if area and area[0] not in areas_vistas:
            areas_vistas.add(area[0])
            sugerencias.append(f'[{area[0]}] ({n} casos de "{falta}"): {area[1]}')

    # Distribución por tipo
    tipos = Counter(f.get('tipo_falta', '') for f in faltas)
    if tipos.get('Tipo III', 0) >= 2:
        sugerencias.append(
            'Se registran múltiples faltas Tipo III. Considerar diagnóstico del clima escolar '
            'del grupo mediante sociograma y revisión del plan de convivencia.')
    if tipos.get('Tipo II', 0) >= 4:
        sugerencias.append(
            'Alta incidencia de faltas Tipo II. Proponer taller grupal de convivencia '
            'y revisar dinámicas de grupo con herramienta sociométrica.')

    return sugerencias

