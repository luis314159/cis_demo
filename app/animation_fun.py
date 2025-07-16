import time
import os
import random
import sys

def clear_screen():
    """Limpia la pantalla"""
    os.system('cls' if os.name == 'nt' else 'clear')

def gato_caminando():
    """Animación de un gato caminando"""
    frames = [
        """
        /\\_/\\  
       ( o.o ) 
        > ^ <  
       /     \\
      (  ) (  )
        """,
        """
        /\\_/\\  
       ( ^.^ ) 
        > v <  
       /     \\
      ( ) ( ) 
        """,
        """
        /\\_/\\  
       ( -.-)zzZ 
        > ^ <  
       /     \\
      (   )(   )
        """
    ]
    
    print("🐱 GATO CAMINANDO 🐱")
    for _ in range(15):
        for frame in frames:
            clear_screen()
            print(frame)
            time.sleep(0.5)

def lluvia_matrix():
    """Simulación de lluvia estilo Matrix"""
    print("🔴 LLUVIA MATRIX 🔴")
    chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
    
    for _ in range(50):
        clear_screen()
        for i in range(20):
            line = ""
            for j in range(60):
                if random.random() < 0.1:
                    line += random.choice(chars)
                else:
                    line += " "
            print(f"\033[92m{line}\033[0m")  # Verde brillante
        time.sleep(0.1)

def cohete_despegando():
    """Animación de un cohete despegando"""
    rocket_frames = [
        """
                 /\\
                /  \\
               |    |
               | 🚀 |
               |____|
                ||||
               /||||\\ 
              💥💥💥💥
        """,
        """
                 /\\
                /  \\
               |    |
               | 🚀 |
               |____|
                ||||
               /||||\\
             💥💥💥💥💥
        """,
        """
                 /\\
                /  \\
               |    |
               | 🚀 |
               |____|
                ||||
               /||||\\
            💥💥💥💥💥💥
        """
    ]
    
    print("🚀 COHETE AL ESPACIO 🚀")
    
    # Despegue
    for i in range(len(rocket_frames)):
        clear_screen()
        print("\n" * (10 - i * 2))
        print(rocket_frames[i])
        time.sleep(0.8)
    
    # Cohete subiendo
    for i in range(15):
        clear_screen()
        print("\n" * max(0, 15 - i))
        print("""
                 /\\
                /  \\
               |    |
               | 🚀 |
               |____|
                ||||
        """)
        time.sleep(0.3)

def danza_emojis():
    """Baile de emojis"""
    dancers = ["🕺", "💃", "🤖", "👽", "🐸", "🦄"]
    
    print("🎭 DANZA DE EMOJIS 🎭")
    
    for _ in range(20):
        clear_screen()
        line1 = ""
        line2 = ""
        line3 = ""
        
        for i in range(8):
            dancer = random.choice(dancers)
            space = " " * random.randint(1, 3)
            if random.choice([True, False]):
                line1 += space + dancer + space
                line2 += space + "  " + space
                line3 += space + "🦵🦵" + space
            else:
                line1 += space + "  " + space
                line2 += space + dancer + space
                line3 += space + "🦵🦵" + space
        
        print("\n" * 5)
        print(line1)
        print(line2)
        print(line3)
        print("\n🎵 ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ 🎵")
        time.sleep(0.4)

def snake_game_demo():
    """Demo de snake con caracteres"""
    print("🐍 SERPIENTE DEMO 🐍")
    
    snake = [(10, 5), (9, 5), (8, 5)]
    direction = (1, 0)
    
    for _ in range(30):
        clear_screen()
        
        # Crear tablero
        board = [[" " for _ in range(40)] for _ in range(15)]
        
        # Dibujar serpiente
        for i, (x, y) in enumerate(snake):
            if 0 <= x < 40 and 0 <= y < 15:
                if i == 0:
                    board[y][x] = "🟢"  # Cabeza
                else:
                    board[y][x] = "🟩"  # Cuerpo
        
        # Añadir comida
        food_x, food_y = random.randint(0, 39), random.randint(0, 14)
        if 0 <= food_x < 40 and 0 <= food_y < 15:
            board[food_y][food_x] = "🍎"
        
        # Mostrar tablero
        for row in board:
            print("".join(row))
        
        # Mover serpiente
        head_x, head_y = snake[0]
        new_head = (head_x + direction[0], head_y + direction[1])
        snake.insert(0, new_head)
        snake.pop()
        
        # Cambiar dirección ocasionalmente
        if random.random() < 0.3:
            direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        
        time.sleep(0.3)

def reloj_ascii():
    """Reloj digital ASCII"""
    print("🕐 RELOJ DIGITAL 🕐")
    
    digits = {
        '0': ["███", "█ █", "█ █", "█ █", "███"],
        '1': [" █ ", "██ ", " █ ", " █ ", "███"],
        '2': ["███", "  █", "███", "█  ", "███"],
        '3': ["███", "  █", "███", "  █", "███"],
        '4': ["█ █", "█ █", "███", "  █", "  █"],
        '5': ["███", "█  ", "███", "  █", "███"],
        '6': ["███", "█  ", "███", "█ █", "███"],
        '7': ["███", "  █", "  █", "  █", "  █"],
        '8': ["███", "█ █", "███", "█ █", "███"],
        '9': ["███", "█ █", "███", "  █", "███"],
        ':': [" ", "█", " ", "█", " "]
    }
    
    for _ in range(10):
        clear_screen()
        current_time = time.strftime("%H:%M:%S")
        
        print("\n" * 3)
        for row in range(5):
            line = "    "
            for char in current_time:
                line += digits[char][row] + "  "
            print(line)
        
        print(f"\n    {current_time}")
        time.sleep(1)

def menu_principal():
    """Menú principal con todas las animaciones"""
    animaciones = {
        "1": ("Gato Caminando", gato_caminando),
        "2": ("Lluvia Matrix", lluvia_matrix),
        "3": ("Cohete Despegando", cohete_despegando),
        "4": ("Danza de Emojis", danza_emojis),
        "5": ("Snake Demo", snake_game_demo),
        "6": ("Reloj ASCII", reloj_ascii),
        "7": ("¡Ver todas!", lambda: ejecutar_todas()),
        "0": ("Salir", None)
    }
    
    while True:
        clear_screen()
        print("=" * 50)
        print("🎪 ANIMACIONES ASCII DIVERTIDAS 🎪")
        print("=" * 50)
        print()
        
        for key, (name, _) in animaciones.items():
            print(f"  {key}. {name}")
        
        print("\n" + "=" * 50)
        choice = input("Elige una opción: ").strip()
        
        if choice in animaciones:
            if choice == "0":
                print("¡Hasta luego! 👋")
                break
            else:
                clear_screen()
                animaciones[choice][1]()
                input("\nPresiona Enter para continuar...")
        else:
            print("Opción no válida. Intenta de nuevo.")
            time.sleep(1)

def ejecutar_todas():
    """Ejecuta todas las animaciones en secuencia"""
    animaciones = [
        gato_caminando,
        cohete_despegando,
        danza_emojis,
        snake_game_demo,
        lluvia_matrix
    ]
    
    for animacion in animaciones:
        animacion()
        time.sleep(2)

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n¡Programa terminado! 🎭")
        sys.exit(0)