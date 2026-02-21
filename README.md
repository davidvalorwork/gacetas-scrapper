# Gaceta Oficial Scraper y Lector

Este proyecto descarga las Gacetas Oficiales de Venezuela directamente de la página del gobierno, las "lee" y guarda toda su información escrita para que sea muy fácil buscar datos dentro de ellas (como números de cédula, nombres, etc.).

## ¿Qué hace exactamente?

1. **Descarga**: Entra de forma automática a la página oficial (`gacetaoficial.gob.ve`) y descarga todos los documentos PDF de las gacetas que se han publicado.
2. **Lee el texto**: Usa una tecnología especial que le permite recorrer esos PDFs página por página, convertir las imágenes en texto real, y extraer todas las palabras. 
3. **Almacena y Busca**: Guarda todo ese texto de forma organizada y estructurada en una base de datos, lo que permite poder buscar rápidamente cualquier información dentro de miles de gacetas al mismo tiempo.

## ¿Cómo funciona?

El proceso se divide en dos tareas principales:
*   Primero, se ejecuta una herramienta que simula ser un usuario revisando el archivo histórico del gobierno: entra a los años, luego a los meses, y va descargando cada gaceta que encuentra en la lista hasta guardarlas todas en una carpeta en tu computadora.
*   Después, otra herramienta toma todos esos PDFs que se descargaron y empieza a leer las imágenes de cada página sacando el contenido escrito, para finalmente guardar ese texto en nuestro sistema de forma que la computadora lo pueda leer rápido después.

## Limitaciones y fallos conocidos

*   **Descargas que fallan (Enlaces rotos del gobierno):** Algunas gacetas (por ejemplo, la 42.535) darán error al intentar descargarse y no se guardarán. Esto **no es un error del sistema**, sino un problema en la propia página del gobierno: el enlace que muestran en su web apunta a un lugar que no existe dentro de sus propios servidores. La única solución es buscar estas gacetas puntuales en otras páginas y meter el documento manualmente en tu carpeta de descargas.
*   **Lentitud:** Leer millones de palabras en imágenes es pesado para la computadora. Cuando hay que leer muchas gacetas juntas, el proceso puede demorar desde varias horas hasta algunos días, dependiendo de qué tan potente sea el equipo.
*   **Almacenamiento:** Aunque este sistema las organiza bien, descargar miles de gacetas requiere que tengas bastante espacio libre en el disco duro (varios GBs).
