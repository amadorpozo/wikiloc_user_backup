# wikiloc_user_backup
## Descripción
Hace una copia local de todas las rutas de un usuario de Wikiloc, incluyendo GPX, descripción y fotos. 
## Prerequisitos (para Windows 10)
### Python3
Es necesario tener instalado Python3. Si no lo tienes, descárgalo de https://www.python.org/downloads/
### Librerías necesarias para el programa
Se pueden instalar usando la utilidad "PIP" the Python para descardar librerías. Para ello usa el "cmd.exe" de Windows y ejecuta: 

```
cd C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38\Scripts
.\pip.exe install requests
.\pip.exe install lxml
.\pip.exe install beautifulsoup4
.\pip.exe install selenium
```
Descargar un plugin de navegador para Selenium. Por ejemplo, en el caso de Firefox: https://github.com/mozilla/geckodriver/releases/tag/v0.24.0
Descomprimir y copiarlo en un lugar del PATH de Windows, por ejemplo en mi caso C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\geckodriver.exe
Si no usas Firefox, visita: https://selenium-python.readthedocs.io/installation.html#drivers



## Uso del programa

