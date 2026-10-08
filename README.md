# The Agentic Data Scientist · paquete del alumno

**Augmented Learning Labs.** Código que usan los cuadernos de Colab del curso: el estilo de la Taquería de Datos,
la identificación del alumno con sus secretos de Colab y el registro de su avance.

Este repositorio es público a propósito: no contiene rúbricas, respuestas esperadas, claves secretas ni datos de alumnos.
La seguridad de los datos la pone la base de datos (seguridad por fila de Supabase).

| Archivo | Qué es |
| --- | --- |
| `taqueria/__init__.py` | Paquete del alumno. Cada versión publicada tiene su etiqueta `vX.Y.Z`, que nunca se mueve |
| `estable.json` | Versión que deben usar los cuadernos y su huella SHA-256; el cuaderno rechaza cualquier archivo que no coincida |
| `curso.json` | Configuración pública: clave publicable de Supabase y enlace al aviso de privacidad |

Para alumnos: no necesitas nada de aquí; tu cuaderno lo descarga solo.
