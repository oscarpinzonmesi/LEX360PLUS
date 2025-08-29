@echo off
cd /d "C:\Users\oscar\Desktop\LEX360PLUS"

echo ===================================
echo  Fusionando develop -> main (ours)
echo ===================================

:: Cambiar a main
git checkout main

:: Hacer merge forzando estrategia ours
git merge develop -s ours

:: Subir los cambios a GitHub
git push origin main

:: Regresar a develop para seguir trabajando
git checkout develop

echo ===================================
echo  Merge terminado y sincronizado.
echo ===================================
pause
