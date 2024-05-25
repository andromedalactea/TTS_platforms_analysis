import os
import re
import pygame

def play_wav_files(directory):
    # Inicializar Pygame para reproducción de audio
    pygame.mixer.init()
    
    # Listar archivos en el directorio
    files = os.listdir(directory)
    
    # Filtrar y ordenar los archivos que cumplen con el patrón "numero_*.wav"
    pattern = re.compile(r'^\d+_.*\.wav$')
    filtered_files = [file for file in files if pattern.match(file)]
    sorted_files = sorted(filtered_files, key=lambda x: int(x.split('_')[0]))
    
    # Reproducir los archivos de audio en orden
    for filename in sorted_files:
        print(f"Reproduciendo: {filename}")
        full_path = os.path.join(directory, filename)
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play()
        
        # Esperar a que el audio termine antes de continuar
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

if __name__ == "__main__":
    # Especifica la ruta de la carpeta donde están los audios
    directory = '/home/andromedalactea/test/google/autput_audios/Our_new_and_innovative_technology'
    play_wav_files(directory)
